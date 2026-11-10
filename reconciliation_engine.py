from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
import database

class ReconciliationEngine:
    """
    Deterministic rule and validation engine for operational documents.
    Eliminates manual math checks, flags duplicates, and identifies risk anomalies.
    """

    @classmethod
    def validate_document(
        cls,
        doc_data: Dict[str, Any],
        db: Session,
        current_doc_id: int = None
    ) -> Tuple[str, List[Dict[str, str]]]:
        """
        Validates parsed document against business rules.
        Returns: (status: str, flags: List[Dict])
        """
        flags: List[Dict[str, str]] = []
        
        vendor = doc_data.get("vendor_name")
        doc_num = doc_data.get("document_number")
        subtotal = float(doc_data.get("subtotal") or 0.0)
        tax = float(doc_data.get("tax_amount") or 0.0)
        total = float(doc_data.get("total_amount") or 0.0)
        line_items = doc_data.get("line_items", [])
        
        # 1. Missing Critical Fields Check
        if not vendor or vendor.strip() == "Unknown Vendor":
            flags.append({
                "code": "MISSING_VENDOR",
                "severity": "WARNING",
                "message": "Vendor name could not be reliably determined."
            })
            
        if not doc_num or doc_num.startswith("DOC-"):
            flags.append({
                "code": "MISSING_DOC_NUM",
                "severity": "WARNING",
                "message": "Invoice / Reference number is missing or auto-generated."
            })

        # 2. Line Item Sum vs. Subtotal Check
        if line_items:
            items_sum = round(sum(
                (item.total_price if hasattr(item, "total_price") else item.get("total_price", 0.0))
                for item in line_items
            ), 2)
            
            # Allow minor floating point tolerance
            if subtotal > 0 and abs(items_sum - subtotal) > 0.02:
                flags.append({
                    "code": "LINE_ITEM_SUM_MISMATCH",
                    "severity": "ERROR",
                    "message": f"Sum of line items (${items_sum:,.2f}) does not match stated subtotal (${subtotal:,.2f}). Difference: ${abs(items_sum - subtotal):,.2f}"
                })

        # 3. Subtotal + Tax vs. Total Check
        calculated_total = round(subtotal + tax, 2)
        if total > 0 and abs(calculated_total - total) > 0.02:
            flags.append({
                "code": "TAX_TOTAL_MISMATCH",
                "severity": "ERROR",
                "message": f"Subtotal (${subtotal:,.2f}) + Tax (${tax:,.2f}) = ${calculated_total:,.2f}, which does not match Grand Total (${total:,.2f})."
            })

        # 3b. Line Item Extended Math Check (qty * unit_price == total_price)
        for idx, item in enumerate(line_items):
            qty = float(item.quantity if hasattr(item, "quantity") else item.get("quantity", 1.0))
            unit = float(item.unit_price if hasattr(item, "unit_price") else item.get("unit_price", 0.0))
            tot = float(item.total_price if hasattr(item, "total_price") else item.get("total_price", 0.0))
            desc = str(item.description if hasattr(item, "description") else item.get("description", f"Item #{idx+1}"))
            expected_row_total = round(qty * unit, 2)
            if tot > 0 and unit > 0 and abs(expected_row_total - tot) > 0.05:
                flags.append({
                    "code": "ROW_EXTENSION_MISMATCH",
                    "severity": "ERROR",
                    "message": f"Line item '{desc}' math mismatch: {qty} x ${unit:,.2f} = ${expected_row_total:,.2f}, but billed ${tot:,.2f}."
                })

        # 3c. Tax Rate Anomaly Check (> 15% effective sales tax)
        if subtotal > 0 and tax > 0:
            effective_tax_rate = (tax / subtotal) * 100.0
            if effective_tax_rate > 15.0:
                flags.append({
                    "code": "TAX_RATE_ANOMALY",
                    "severity": "WARNING",
                    "message": f"Effective tax rate ({effective_tax_rate:.1f}%) exceeds standard 15.0% statutory ceiling."
                })

        # 4. Duplicate Detection in Database
        if vendor and doc_num and not doc_num.startswith("DOC-"):
            query = db.query(database.Document).filter(
                database.Document.vendor_name == vendor,
                database.Document.document_number == doc_num
            )
            if current_doc_id:
                query = query.filter(database.Document.id != current_doc_id)
            
            existing = query.first()
            if existing:
                flags.append({
                    "code": "DUPLICATE_DOCUMENT",
                    "severity": "ERROR",
                    "message": f"Duplicate document detected! Vendor '{vendor}' with Doc # '{doc_num}' was already processed on {existing.created_at.strftime('%Y-%m-%d')} (Record #{existing.id})."
                })

        # 5. High-Value Threshold Flag ($5,000+)
        if total >= 5000.0:
            flags.append({
                "code": "HIGH_VALUE_THRESHOLD",
                "severity": "INFO",
                "message": f"High value transaction (${total:,.2f} >= $5,000.00). Requires manager sign-off."
            })

        # 6. Determine Recommended Pipeline Status
        has_errors = any(f["severity"] == "ERROR" for f in flags)
        has_warnings = any(f["severity"] == "WARNING" for f in flags)
        
        if has_errors:
            status = "FLAGGED"
        elif has_warnings or total == 0.0 or not line_items:
            status = "PENDING_REVIEW"
        else:
            status = "APPROVED"

        return status, flags
