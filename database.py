import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
from sqlalchemy import create_engine

DATABASE_URL = "sqlite:///./pipeline_records.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_path = Column(String)
    file_type = Column(String)
    vendor_name = Column(String, index=True, nullable=True)
    document_number = Column(String, index=True, nullable=True)
    document_date = Column(String, nullable=True)
    
    subtotal = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    currency = Column(String, default="USD")
    
    status = Column(String, default="PENDING_REVIEW") # PENDING_REVIEW, FLAGGED, APPROVED, EXPORTED
    confidence_score = Column(Float, default=1.0)
    
    validation_flags = Column(JSON, default=list) # List of warnings/errors e.g. ["Math mismatch", "Duplicate"]
    raw_text = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    line_items = relationship("LineItem", back_populates="document", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="document", cascade="all, delete-orphan")


class LineItem(Base):
    __tablename__ = "line_items"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    
    description = Column(String)
    quantity = Column(Float, default=1.0)
    unit_price = Column(Float, default=0.0)
    total_price = Column(Float, default=0.0)
    item_code = Column(String, nullable=True)

    document = relationship("Document", back_populates="line_items")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    action = Column(String) # e.g. UPLOADED, FLAGGED, EDITED, APPROVED, EXPORTED
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    document = relationship("Document", back_populates="audit_logs")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
