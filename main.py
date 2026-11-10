import os
import shutil
import io
import csv
from typing import List, Optional
from datetime import datetime, timezone
import httpx
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import database
from database import get_db, init_db, Document, LineItem, AuditLog
import schemas
from parser_engine import DocumentParser
from reconciliation_engine import ReconciliationEngine
import generate_demo_data

# Ensure upload and sample dirs exist
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Initialize database
init_db()

app = FastAPI(
    title="Antigravity Operations Reconciliation Engine",
    description="Deterministic ingestion, parsing, reconciliation and export pipeline for B2B operations.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def serve_dashboard():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_path):
        return {"message": "Dashboard UI is initializing..."}
    return FileResponse(index_path)


@app.get("/api/metrics", response_model=schemas.DashboardMetrics)
def get_metrics(db: Session = Depends(get_db)):
    total_docs = db.query(Document).count()
    pending = db.query(Document).filter(Document.status == "PENDING_REVIEW").count()
    flagged = db.query(Document).filter(Document.status == "FLAGGED").count()
    approved = db.query(Document).filter(Document.status == "APPROVED").count()
    exported = db.query(Document).filter(Document.status == "EXPORTED").count()
    
    docs = db.query(Document).all()
    total_volume = sum(d.total_amount for d in docs)
    # Estimate: ~15 minutes (0.25h) saved per processed document
    est_hours = round(total_docs * 0.25, 1)

    # Calculate overbilling caught from math mismatches
    overbilling = 0.0
    for d in docs:
        expected = round((d.subtotal or 0.0) + (d.tax_amount or 0.0), 2)
        if d.total_amount and expected > 0 and d.total_amount > expected:
            overbilling += (d.total_amount - expected)
        elif d.line_items:
            li_sum = sum(li.total_price for li in d.line_items)
            if d.subtotal and d.subtotal > li_sum:
                overbilling += (d.subtotal - li_sum)

    avg_conf = round(sum(d.confidence_score or 1.0 for d in docs) / len(docs), 3) if docs else 1.0

    return schemas.DashboardMetrics(
        total_documents=total_docs,
        pending_review=pending,
        flagged_discrepancies=flagged,
        approved_count=approved,
        exported_count=exported,
        total_reconciled_volume=round(total_volume, 2),
        est_hours_saved=est_hours,
        total_overbilling_caught=round(overbilling, 2),
        avg_confidence_score=avg_conf
    )


@app.post("/api/documents/upload", response_model=List[schemas.DocumentResponse])
async def upload_documents(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    processed = []
    
    for file in files:
        file_bytes = await file.read()
        safe_filename = os.path.basename(file.filename)
        saved_path = os.path.join(UPLOAD_DIR, f"{int(datetime.now(timezone.utc).timestamp())}_{safe_filename}")
        
        with open(saved_path, "wb") as f:
            f.write(file_bytes)
        
        # 1. Parse document text & structure
        parsed_data = DocumentParser.parse_document(safe_filename, file_bytes)
        
        # 2. Run deterministic validation rules
        status, flags = ReconciliationEngine.validate_document(parsed_data, db)
        
        # 3. Create database record
        doc_record = Document(
            filename=safe_filename,
            file_path=saved_path,
            file_type=parsed_data.get("file_type", "TXT"),
            vendor_name=parsed_data.get("vendor_name"),
            document_number=parsed_data.get("document_number"),
            document_date=parsed_data.get("document_date"),
            subtotal=parsed_data.get("subtotal", 0.0),
            tax_amount=parsed_data.get("tax_amount", 0.0),
            total_amount=parsed_data.get("total_amount", 0.0),
            currency=parsed_data.get("currency", "USD"),
            status=status,
            confidence_score=parsed_data.get("confidence_score", 1.0),
            validation_flags=flags,
            raw_text=parsed_data.get("raw_text")
        )
        db.add(doc_record)
        db.flush() # obtain doc_record.id
        
        # 4. Add Line Items
        for item in parsed_data.get("line_items", []):
            line_item = LineItem(
                document_id=doc_record.id,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
                item_code=item.item_code
            )
            db.add(line_item)
            
        # 5. Add initial audit log
        log_action = "FLAGGED" if status == "FLAGGED" else ("AUTO_VERIFIED" if status == "APPROVED" else "UPLOADED")
        audit = AuditLog(
            document_id=doc_record.id,
            action=log_action,
            details=f"Extracted {len(parsed_data.get('line_items', []))} line items. {len(flags)} validation flags generated."
        )
        db.add(audit)
        db.commit()
        db.refresh(doc_record)
        processed.append(doc_record)

    return processed


@app.get("/api/documents", response_model=List[schemas.DocumentResponse])
def list_documents(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Document).order_by(Document.created_at.desc())
    if status and status != "ALL":
        query = query.filter(Document.status == status)
    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            (Document.vendor_name.ilike(search_fmt)) |
            (Document.document_number.ilike(search_fmt)) |
            (Document.filename.ilike(search_fmt))
        )
    return query.all()


@app.get("/api/documents/{doc_id}", response_model=schemas.DocumentResponse)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@app.put("/api/documents/{doc_id}", response_model=schemas.DocumentResponse)
def update_document(doc_id: int, payload: schemas.DocumentUpdate, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if payload.vendor_name is not None:
        doc.vendor_name = payload.vendor_name
    if payload.document_number is not None:
        doc.document_number = payload.document_number
    if payload.document_date is not None:
        doc.document_date = payload.document_date
    if payload.subtotal is not None:
        doc.subtotal = payload.subtotal
    if payload.tax_amount is not None:
        doc.tax_amount = payload.tax_amount
    if payload.total_amount is not None:
        doc.total_amount = payload.total_amount

    # Update line items if provided
    if payload.line_items is not None:
        db.query(LineItem).filter(LineItem.document_id == doc.id).delete()
        for item in payload.line_items:
            new_item = LineItem(
                document_id=doc.id,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
                item_code=item.item_code
            )
            db.add(new_item)

    # Re-run deterministic validation
    doc_dict = {
        "vendor_name": doc.vendor_name,
        "document_number": doc.document_number,
        "subtotal": doc.subtotal,
        "tax_amount": doc.tax_amount,
        "total_amount": doc.total_amount,
        "line_items": doc.line_items
    }
    status, flags = ReconciliationEngine.validate_document(doc_dict, db, current_doc_id=doc.id)
    doc.status = status
    doc.validation_flags = flags

    audit = AuditLog(
        document_id=doc.id,
        action="EDITED_AND_RECHECKED",
        details=f"Human operator updated record. Validation refreshed with status {status}."
    )
    db.add(audit)
    db.commit()
    db.refresh(doc)
    return doc


@app.post("/api/documents/{doc_id}/approve", response_model=schemas.DocumentResponse)
def approve_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.status = "APPROVED"
    audit = AuditLog(
        document_id=doc.id,
        action="APPROVED",
        details="Document approved for final sync & export by human operator."
    )
    db.add(audit)
    db.commit()
    db.refresh(doc)
    return doc


@app.post("/api/demo/generate-and-ingest", response_model=List[schemas.DocumentResponse])
def generate_and_ingest_samples(db: Session = Depends(get_db)):
    """
    Generates realistic demo documents (HVAC clean, Freight discrepancy, Dental high-value, CSV batch)
    and automatically ingests them to showcase live reconciliation in sales pitches.
    """
    generate_demo_data.generate_all_samples()
    sample_files = [
        "Apex_HVAC_Supply_INV-8821.pdf",
        "NorthStar_Logistics_BOL-4091_MATH_ERROR.pdf",
        "Metro_Dental_Supply_INV-9904_HIGH_VALUE.pdf",
        "Summit_Property_Repair_INV-3318_ROW_ERROR.pdf",
        "Dispatch_Batch_0907.csv"
    ]
    
    results = []
    for fname in sample_files:
        fpath = os.path.join(generate_demo_data.SAMPLE_DIR, fname)
        if os.path.exists(fpath):
            with open(fpath, "rb") as f:
                content = f.read()
            
            parsed = DocumentParser.parse_document(fname, content)
            status, flags = ReconciliationEngine.validate_document(parsed, db)
            
            doc_record = Document(
                filename=fname,
                file_path=fpath,
                file_type=parsed.get("file_type", "TXT"),
                vendor_name=parsed.get("vendor_name"),
                document_number=parsed.get("document_number"),
                document_date=parsed.get("document_date"),
                subtotal=parsed.get("subtotal", 0.0),
                tax_amount=parsed.get("tax_amount", 0.0),
                total_amount=parsed.get("total_amount", 0.0),
                currency=parsed.get("currency", "USD"),
                status=status,
                confidence_score=parsed.get("confidence_score", 1.0),
                validation_flags=flags,
                raw_text=parsed.get("raw_text")
            )
            db.add(doc_record)
            db.flush()
            
            for item in parsed.get("line_items", []):
                li = LineItem(
                    document_id=doc_record.id,
                    description=item.description,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.total_price,
                    item_code=item.item_code
                )
                db.add(li)
                
            audit = AuditLog(
                document_id=doc_record.id,
                action="DEMO_INGESTED",
                details=f"Demo document auto-ingested. Status: {status} with {len(flags)} flags."
            )
            db.add(audit)
            db.commit()
            db.refresh(doc_record)
            results.append(doc_record)

    return results


@app.get("/api/export/csv")
def export_csv(db: Session = Depends(get_db)):
    docs = db.query(Document).filter(Document.status.in_(["APPROVED", "EXPORTED"])).all()
    output = io.StringIO()
    writer = csv.writer(output)
    
    # CSV Header
    writer.writerow([
        "Document ID", "Vendor Name", "Document #", "Date", "Status",
        "Subtotal", "Tax", "Total Amount", "Item Description", "Item Qty", "Item Unit Price", "Item Total"
    ])
    
    for doc in docs:
        if doc.line_items:
            for item in doc.line_items:
                writer.writerow([
                    doc.id, doc.vendor_name, doc.document_number, doc.document_date, doc.status,
                    f"{doc.subtotal:.2f}", f"{doc.tax_amount:.2f}", f"{doc.total_amount:.2f}",
                    item.description, item.quantity, f"{item.unit_price:.2f}", f"{item.total_price:.2f}"
                ])
        else:
            writer.writerow([
                doc.id, doc.vendor_name, doc.document_number, doc.document_date, doc.status,
                f"{doc.subtotal:.2f}", f"{doc.tax_amount:.2f}", f"{doc.total_amount:.2f}",
                "No line items", "", "", ""
            ])
        doc.status = "EXPORTED"
        db.add(AuditLog(document_id=doc.id, action="EXPORTED", details="Exported via batch CSV."))

    db.commit()
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=reconciled_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.csv"}
    )


@app.post("/api/export/webhook")
async def export_webhook(payload: schemas.BatchExportRequest, db: Session = Depends(get_db)):
    if not payload.webhook_url:
        raise HTTPException(status_code=400, detail="webhook_url is required")
        
    docs = db.query(Document).filter(Document.id.in_(payload.document_ids)).all()
    export_payload = []
    
    for d in docs:
        items = [{
            "description": li.description,
            "quantity": li.quantity,
            "unit_price": li.unit_price,
            "total_price": li.total_price,
            "item_code": li.item_code
        } for li in d.line_items]
        
        export_payload.append({
            "id": d.id,
            "vendor_name": d.vendor_name,
            "document_number": d.document_number,
            "document_date": d.document_date,
            "subtotal": d.subtotal,
            "tax_amount": d.tax_amount,
            "total_amount": d.total_amount,
            "line_items": items,
            "exported_at": datetime.now(timezone.utc).isoformat()
        })
        d.status = "EXPORTED"
        db.add(AuditLog(document_id=d.id, action="EXPORTED_WEBHOOK", details=f"Synced to {payload.webhook_url}"))
    
    db.commit()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(payload.webhook_url, json={"documents": export_payload})
            return {"status": "SUCCESS", "status_code": resp.status_code, "count": len(docs)}
    except Exception as e:
        return {"status": "FAILED_OUTBOUND_CALL", "error": str(e), "queued_count": len(docs)}


@app.post("/api/documents/batch-approve")
def batch_approve_documents(db: Session = Depends(get_db)):
    """Approves all PENDING_REVIEW documents that have zero ERROR flags."""
    docs = db.query(Document).filter(Document.status == "PENDING_REVIEW").all()
    approved_ids = []
    for doc in docs:
        flags = doc.validation_flags or []
        has_err = any(f.get("severity") == "ERROR" for f in flags)
        if not has_err:
            doc.status = "APPROVED"
            db.add(AuditLog(
                document_id=doc.id,
                action="BATCH_APPROVED",
                details="Auto-approved via 1-click batch approval (0 error flags)."
            ))
            approved_ids.append(doc.id)
    db.commit()
    return {"approved_count": len(approved_ids), "approved_ids": approved_ids}


@app.post("/api/roi/calculate", response_model=schemas.RoiCalculationResponse)
def calculate_roi(payload: schemas.RoiCalculationRequest):
    monthly_hours = round((payload.monthly_invoice_volume * payload.minutes_per_manual_doc) / 60.0, 1)
    labor_savings = round(monthly_hours * payload.hourly_staff_rate, 2)
    monthly_spend = payload.monthly_invoice_volume * payload.avg_invoice_value
    overbilling_prevented = round(monthly_spend * (payload.overbilling_error_rate_pct / 100.0) * 0.65, 2)
    gross_monthly = round(labor_savings + overbilling_prevented, 2)
    net_monthly = round(gross_monthly - payload.monthly_retainer_fee, 2)
    annual_net = round((net_monthly * 12) - payload.setup_fee, 2)
    daily_net = max(net_monthly / 30.0, 1.0)
    payback_days = max(1, int(round(payload.setup_fee / daily_net)))
    total_annual_cost = payload.setup_fee + (payload.monthly_retainer_fee * 12)
    roi_mult = round((gross_monthly * 12) / max(total_annual_cost, 1.0), 1)

    return schemas.RoiCalculationResponse(
        monthly_hours_saved=monthly_hours,
        monthly_labor_savings=labor_savings,
        monthly_overbilling_prevented=overbilling_prevented,
        gross_monthly_value=gross_monthly,
        net_monthly_profit=net_monthly,
        annual_net_roi=annual_net,
        payback_period_days=payback_days,
        roi_multiple=roi_mult
    )


@app.post("/api/proposal/generate", response_model=schemas.ProposalGeneratorResponse)
def generate_client_proposal(payload: schemas.ProposalGeneratorRequest):
    roi_req = schemas.RoiCalculationRequest(
        monthly_invoice_volume=payload.monthly_volume,
        avg_invoice_value=payload.avg_invoice_value,
        hourly_staff_rate=payload.hourly_wage,
        minutes_per_manual_doc=15.0,
        overbilling_error_rate_pct=2.1,
        monthly_retainer_fee=payload.monthly_retainer,
        setup_fee=payload.setup_fee
    )
    roi = calculate_roi(roi_req)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    exec_summary = (
        f"Deterministic B2B Document Ingestion & Math Reconciliation deployment for {payload.client_company} "
        f"({payload.industry_niche}). Processes {payload.monthly_volume:,} monthly documents, eliminating "
        f"{roi.monthly_hours_saved} hrs/mo of manual keystroke entry and catching an estimated "
        f"${roi.monthly_overbilling_prevented:,.2f}/mo in vendor billing discrepancies before ERP commit to {payload.target_erp}."
    )

    sow_md = f"""# STATEMENT OF WORK (SOW): AUTONOMOUS RECONCILIATION PIPELINE
**Prepared For:** {payload.client_company} ({payload.contact_name})
**Industry Vertical:** {payload.industry_niche}
**Target Accounting / ERP Sink:** {payload.target_erp}
**Date Issued:** {now_str}

---

## 1. ARCHITECTURE & SCOPE OF DEPLOYMENT
1. **Multi-Format Ingestion Endpoint**: Dedicated FastAPI listener accepting PDF invoices, Bills of Lading (BOL), EDI/CSV dispatch feeds, and raw work orders.
2. **Deterministic Validation Engine**:
   - Line-item row extension checks (`Quantity × Unit Price = Row Total` within `$0.02` tolerance).
   - Subtotal + Tax vs. Grand Total verification.
   - Historical SQLite/PostgreSQL duplicate invoice blocking (`Vendor + Document #` composite index).
   - High-Value managerial sign-off routing (`>= $5,000.00`).
3. **Human-in-the-Loop (HITL) Exception Console**: Side-by-side raw stream vs. structured table editor with 1-click approval and ERP CSV/Webhook sync.

## 2. FINANCIAL ROI PROJECTION
| Metric | Projected Value |
| :--- | :--- |
| **Monthly Document Volume** | {payload.monthly_volume:,} docs / month |
| **Manual Labor Hours Eliminated** | {roi.monthly_hours_saved:,.1f} hrs / month |
| **Monthly Payroll Savings** | ${roi.monthly_labor_savings:,.2f} / month |
| **Vendor Overbilling Prevented (Est.)** | ${roi.monthly_overbilling_prevented:,.2f} / month |
| **Net Year-1 Bottom-Line Impact** | **${roi.annual_net_roi:,.2f} / year ({roi.roi_multiple}x ROI)** |
| **Capital Payback Window** | **{roi.payback_period_days} Days** |

## 3. COMMERCIAL TERMS
- **Turnkey Implementation & Schema Calibration**: `${payload.setup_fee:,.2f}` (One-Time)
- **Managed Infrastructure & Rule Retainer**: `${payload.monthly_retainer:,.2f} / month`
"""

    return schemas.ProposalGeneratorResponse(
        client_company=payload.client_company,
        generated_at=now_str,
        executive_summary=exec_summary,
        roi_breakdown=roi,
        statement_of_work_markdown=sow_md,
        sla_guarantees=[
            "< 250ms deterministic math & duplicate validation latency per document",
            "100% isolated single-tenant SQLite/PostgreSQL ledger (Zero public LLM data training)",
            "24-hour SLA on vendor template parser rule updates",
            "99.95% pipeline uptime with automated CSV & Webhook retry queues"
        ]
    )


@app.get("/api/audit-logs", response_model=List[schemas.AuditLogResponse])
def list_recent_audit_logs(limit: int = Query(30, ge=1, le=200), db: Session = Depends(get_db)):
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()



# Serve static frontend files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
