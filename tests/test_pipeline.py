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
