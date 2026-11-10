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
    total_overbilling_caught: float = 0.0
    avg_confidence_score: float = 1.0


class BatchExportRequest(BaseModel):
    document_ids: List[int]
    format: str = "csv" # "csv" | "json" | "webhook"
    webhook_url: Optional[str] = None


class RoiCalculationRequest(BaseModel):
    monthly_invoice_volume: int = Field(default=600, ge=1)
    avg_invoice_value: float = Field(default=1250.0, ge=0.0)
    hourly_staff_rate: float = Field(default=24.0, ge=1.0)
    minutes_per_manual_doc: float = Field(default=15.0, ge=0.5)
    overbilling_error_rate_pct: float = Field(default=2.1, ge=0.0, le=100.0)
    monthly_retainer_fee: float = Field(default=350.0, ge=0.0)
    setup_fee: float = Field(default=2500.0, ge=0.0)


class RoiCalculationResponse(BaseModel):
    monthly_hours_saved: float
    monthly_labor_savings: float
    monthly_overbilling_prevented: float
    gross_monthly_value: float
    net_monthly_profit: float
    annual_net_roi: float
    payback_period_days: int
    roi_multiple: float


class ProposalGeneratorRequest(BaseModel):
    client_company: str
    industry_niche: str = "Logistics & 3PL"
    contact_name: str = "Operations Director"
    monthly_volume: int = 600
    avg_invoice_value: float = 1250.0
    hourly_wage: float = 24.0
    setup_fee: float = 2500.0
    monthly_retainer: float = 350.0
    target_erp: str = "QuickBooks Enterprise"


class ProposalGeneratorResponse(BaseModel):
    client_company: str
    generated_at: str
    executive_summary: str
    roi_breakdown: RoiCalculationResponse
    statement_of_work_markdown: str
    sla_guarantees: List[str]

