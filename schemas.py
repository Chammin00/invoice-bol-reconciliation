from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

class LineItemBase(BaseModel):
    description: str
    quantity: float = 1.0
    unit_price: float = 0.0
    total_price: float = 0.0
    item_code: Optional[str] = None

class LineItemCreate(LineItemBase):
    pass

class LineItemResponse(LineItemBase):
    id: int
    document_id: int

    model_config = ConfigDict(from_attributes=True)


class ValidationFlag(BaseModel):
    code: str
    severity: str # "WARNING" | "ERROR" | "INFO"
    message: str


class DocumentBase(BaseModel):
    filename: str
    file_type: str
    vendor_name: Optional[str] = None
    document_number: Optional[str] = None
    document_date: Optional[str] = None
    subtotal: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0
    currency: str = "USD"
    status: str = "PENDING_REVIEW"
    confidence_score: float = 1.0
    validation_flags: List[dict] = []

class DocumentCreate(DocumentBase):
    file_path: str
    raw_text: Optional[str] = None
    line_items: List[LineItemCreate] = []

class DocumentUpdate(BaseModel):
    vendor_name: Optional[str] = None
    document_number: Optional[str] = None
    document_date: Optional[str] = None
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    line_items: Optional[List[LineItemBase]] = None

class AuditLogResponse(BaseModel):
    id: int
    action: str
    details: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentResponse(DocumentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    line_items: List[LineItemResponse] = []
    audit_logs: List[AuditLogResponse] = []

    model_config = ConfigDict(from_attributes=True)


class DashboardMetrics(BaseModel):
    total_documents: int
    pending_review: int
    flagged_discrepancies: int
    approved_count: int
    exported_count: int
    total_reconciled_volume: float
    est_hours_saved: float


class BatchExportRequest(BaseModel):
    document_ids: List[int]
    format: str = "csv" # "csv" | "json" | "webhook"
    webhook_url: Optional[str] = None
