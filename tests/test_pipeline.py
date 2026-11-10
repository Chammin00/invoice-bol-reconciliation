import os
import sys
import io
import csv
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
import database
from database import init_db, SessionLocal, Document

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    init_db()
    db = SessionLocal()
    # Clean up test DB before tests
    db.query(database.LineItem).delete()
    db.query(database.AuditLog).delete()
    db.query(database.Document).delete()
    db.commit()
    db.close()
    yield

def test_metrics_endpoint():
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_documents" in data
    assert "pending_review" in data
    assert "flagged_discrepancies" in data
    assert "total_reconciled_volume" in data

def test_csv_upload_and_reconciliation():
    csv_content = (
        "date,description,quantity,unit_price,total\n"
        "2026-09-07,HVAC Filter Pack,5,30.00,150.00\n"
        "2026-09-07,Thermostat Replacement,2,120.00,240.00\n"
    )
    
    files = [
        ("files", ("dispatch_test.csv", io.BytesIO(csv_content.encode('utf-8')), "text/csv"))
    ]
    
    response = client.post("/api/documents/upload", files=files)
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 1
    doc = docs[0]
    assert doc["filename"] == "dispatch_test.csv"
    assert doc["subtotal"] == 390.00
    assert doc["total_amount"] == 390.00
    assert len(doc["line_items"]) == 2

def test_demo_generation_and_rules():
    response = client.post("/api/demo/generate-and-ingest")
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) >= 3
    
    # Check that math discrepancy is caught
    freight_doc = next((d for d in docs if "NorthStar" in (d.get("vendor_name") or "")), None)
    if freight_doc:
        assert freight_doc["status"] == "FLAGGED"
        error_flags = [f for f in freight_doc["validation_flags"] if f["severity"] == "ERROR"]
        assert len(error_flags) > 0

def test_csv_export():
    # Ingest samples
    client.post("/api/demo/generate-and-ingest")
    
    # Approve one document
    docs = client.get("/api/documents").json()
    assert len(docs) > 0
    first_id = docs[0]["id"]
    client.post(f"/api/documents/{first_id}/approve")
    
    # Test CSV export
    export_resp = client.get("/api/export/csv")
    assert export_resp.status_code == 200
    assert "text/csv" in export_resp.headers["content-type"]
    assert "Document ID" in export_resp.text


def test_row_extension_mismatch_and_batch_approve():
    client.post("/api/demo/generate-and-ingest")
    docs = client.get("/api/documents").json()
    summit_doc = next((d for d in docs if "Summit" in (d.get("vendor_name") or "")), None)
    assert summit_doc is not None
    assert summit_doc["status"] == "FLAGGED"
    codes = [f["code"] for f in summit_doc["validation_flags"]]
    assert "ROW_EXTENSION_MISMATCH" in codes

    # Test batch approve on non-error pending review docs
    batch_resp = client.post("/api/documents/batch-approve")
    assert batch_resp.status_code == 200
    assert "approved_count" in batch_resp.json()


def test_roi_and_proposal_studio_endpoints():
    roi_resp = client.post("/api/roi/calculate", json={
        "monthly_invoice_volume": 800,
        "avg_invoice_value": 1500.0,
        "hourly_staff_rate": 25.0,
        "minutes_per_manual_doc": 15.0,
        "overbilling_error_rate_pct": 2.0,
        "monthly_retainer_fee": 400.0,
        "setup_fee": 2500.0
    })
    assert roi_resp.status_code == 200
    r_data = roi_resp.json()
    assert r_data["monthly_hours_saved"] == 200.0
    assert r_data["monthly_labor_savings"] == 5000.0
    assert r_data["annual_net_roi"] > 0

    prop_resp = client.post("/api/proposal/generate", json={
        "client_company": "Apex Freight Corp",
        "industry_niche": "Regional Freight & 3PL Logistics",
        "contact_name": "VP Operations",
        "monthly_volume": 800,
        "avg_invoice_value": 1500.0,
        "hourly_wage": 25.0,
        "setup_fee": 2500.0,
        "monthly_retainer": 400.0,
        "target_erp": "NetSuite ERP"
    })
    assert prop_resp.status_code == 200
    p_data = prop_resp.json()
    assert p_data["client_company"] == "Apex Freight Corp"
    assert "STATEMENT OF WORK" in p_data["statement_of_work_markdown"]

