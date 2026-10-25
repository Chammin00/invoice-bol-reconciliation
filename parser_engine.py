import re
import csv
import io
from typing import Dict, Any, List, Tuple
from pypdf import PdfReader
from schemas import LineItemCreate

class DocumentParser:
    """
    Intelligent document extraction engine for operational documents
    (Invoices, Bills of Lading, Purchase Orders, Expense Slips, CSV feeds).
    """

    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        pdf_stream = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_stream)
        text_pages = []
        for i, page in enumerate(reader.pages):
            extracted = page.extract_text()
            if extracted:
                text_pages.append(extracted)
        return "\n".join(text_pages)

    @classmethod
    def parse_document(cls, filename: str, content_bytes: bytes) -> Dict[str, Any]:
        file_lower = filename.lower()
        if file_lower.endswith(".pdf"):
            raw_text = cls.extract_text_from_pdf(content_bytes)
            return cls._parse_text_payload(filename, raw_text, file_type="PDF")
        elif file_lower.endswith(".csv"):
            return cls._parse_csv_payload(filename, content_bytes)
        else: # plain text or default
            raw_text = content_bytes.decode("utf-8", errors="ignore")
            return cls._parse_text_payload(filename, raw_text, file_type="TXT")

    @classmethod
    def _parse_csv_payload(cls, filename: str, content_bytes: bytes) -> Dict[str, Any]:
        text = content_bytes.decode("utf-8", errors="ignore")
        reader = csv.DictReader(io.StringIO(text))
        line_items: List[LineItemCreate] = []
        subtotal = 0.0
        
        vendor = "CSV Inbound Feed"
        doc_number = f"CSV-{abs(hash(filename)) % 100000}"
        doc_date = None

        for row in reader:
            desc = row.get("description") or row.get("item") or row.get("name") or "CSV Line Item"
            qty_str = row.get("quantity") or row.get("qty") or "1"
            price_str = row.get("unit_price") or row.get("price") or row.get("rate") or "0"
            total_str = row.get("total") or row.get("amount") or "0"
            
            try:
                qty = float(re.sub(r"[^\d.]", "", qty_str) or 1.0)
                price = float(re.sub(r"[^\d.]", "", price_str) or 0.0)
                total = float(re.sub(r"[^\d.]", "", total_str) or (qty * price))
            except Exception:
                qty, price, total = 1.0, 0.0, 0.0
            
            subtotal += total
            line_items.append(LineItemCreate(
                description=desc.strip(),
                quantity=qty,
                unit_price=price,
                total_price=round(total, 2),
                item_code=row.get("item_code") or row.get("sku")
            ))
            
            if not doc_date and ("date" in row or "Date" in row):
                doc_date = row.get("date") or row.get("Date")

        return {
            "filename": filename,
            "file_type": "CSV",
            "vendor_name": vendor,
            "document_number": doc_number,
            "document_date": doc_date or "2026-09-07",
            "subtotal": round(subtotal, 2),
            "tax_amount": 0.0,
            "total_amount": round(subtotal, 2),
            "currency": "USD",
            "raw_text": text,
            "line_items": line_items,
            "confidence_score": 0.95
        }

    @classmethod
    def _parse_text_payload(cls, filename: str, text: str, file_type: str = "TXT") -> Dict[str, Any]:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        
        vendor_name = cls._extract_vendor(lines, text)
        doc_number = cls._extract_doc_number(text)
        doc_date = cls._extract_date(text)
        subtotal, tax, total = cls._extract_totals(text)
        line_items = cls._extract_line_items(lines)

        # If subtotal or total was not found or 0, fallback to items calculation
        if subtotal == 0.0 and line_items:
            subtotal = sum(item.total_price for item in line_items)
        if total == 0.0 and line_items:
            total = subtotal + tax

        confidence = 0.95 if (vendor_name and doc_number and total > 0) else 0.75

        return {
            "filename": filename,
            "file_type": file_type,
            "vendor_name": vendor_name,
            "document_number": doc_number,
            "document_date": doc_date,
            "subtotal": round(subtotal, 2),
            "tax_amount": round(tax, 2),
            "total_amount": round(total, 2),
            "currency": "USD",
            "raw_text": text,
            "line_items": line_items,
            "confidence_score": confidence
        }

    @staticmethod
    def _extract_vendor(lines: List[str], full_text: str) -> str:
        m = re.search(r"(?:Vendor|Supplier|From|Company|Billed By):\s*([^\n\r,]+)", full_text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        for line in lines[:5]:
            if any(term in line.lower() for term in ["inc", "llc", "corp", "supply", "logistics", "dispatch", "services", "lab", "group"]):
                clean = re.sub(r"(INVOICE|ORDER|BILL OF LADING|FREIGHT BILL)", "", line, flags=re.IGNORECASE).strip()
                if clean:
                    return clean
        return lines[0] if lines else "Unknown Vendor"

    @staticmethod
    def _extract_doc_number(text: str) -> str:
        # High-specificity patterns first (Invoice #, BOL #, PO #)
        patterns = [
            r"(?:Invoice\s*#|Inv\s*#|BOL\s*#|PO\s*#|Order\s*#)\s*[:\-]?\s*([A-Za-z0-9\-]+)",
            r"(?:Document|Tracking\s*#)\s*[:\-]?\s*([A-Za-z0-9\-]+)",
            r"#\s*([0-9]{4,10})"
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                if val.upper() not in ["INVOICE", "FREIGHT", "ORDER", "DOCUMENT"]:
                    return val
        return f"DOC-{abs(hash(text[:100])) % 100000}"

    @staticmethod
    def _extract_date(text: str) -> str:
        patterns = [
            r"(?:Date|Invoice Date|Issued):\s*([0-9]{1,4}[/\-\.][0-9]{1,2}[/\-\.][0-9]{1,4})",
            r"([0-9]{4}-[0-9]{2}-[0-9]{2})",
            r"([A-Za-z]+\s+[0-9]{1,2},?\s+[0-9]{4})",
            r"([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})"
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return "2026-09-07"

    @staticmethod
    def _extract_totals(text: str) -> Tuple[float, float, float]:
        subtotal, tax, total = 0.0, 0.0, 0.0
        
        # 1. Subtotal extraction
        m_sub = re.search(r"\b(?:Subtotal|Sub Total|Net Amount)\b\s*[:\-]?\s*\$?\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
        if m_sub:
            subtotal = float(m_sub.group(1).replace(",", ""))

        # 2. Tax extraction
        m_tax = re.search(r"\b(?:Tax|Sales Tax|VAT)\b\s*[:\-]?\s*\$?\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
        if m_tax:
            tax = float(m_tax.group(1).replace(",", ""))

        # 3. Grand total extraction (strict: Grand Total, Total Due, Total Amount, or isolated Total)
        m_total = re.search(r"\b(?:Grand Total|Total Due|Total Amount|Balance Due)\b\s*[:\-]?\s*\$?\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
        if not m_total:
            # Match Total that is not preceded by Sub
            m_total = re.search(r"(?<!Sub)(?<!Sub )\bTotal\b\s*[:\-]?\s*\$?\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
            
        if m_total:
            total = float(m_total.group(1).replace(",", ""))

        return subtotal, tax, total

    @classmethod
    def _extract_line_items(cls, lines: List[str]) -> List[LineItemCreate]:
        items: List[LineItemCreate] = []
        
        # 1. First attempt: Single-line row regex
        item_regex = re.compile(
            r"^(?P<desc>[A-Za-z0-9\s\-_\.,#/()]+?)\s+(?P<qty>\d+(?:\.\d+)?)\s+\$?(?P<unit>[\d,]+\.\d{2})\s+\$?(?P<total>[\d,]+\.\d{2})$"
        )
        
        for line in lines:
            line_str = line.strip()
            if any(h in line_str.lower() for h in ["description", "qty", "unit price", "subtotal", "total due", "sales tax", "grand total"]):
                continue
            
            match = item_regex.match(line_str)
            if match:
                desc = match.group("desc").strip()
                qty = float(match.group("qty"))
                unit = float(match.group("unit").replace(",", ""))
                tot = float(match.group("total").replace(",", ""))
                items.append(LineItemCreate(
                    description=desc,
                    quantity=qty,
                    unit_price=unit,
                    total_price=tot
                ))

        # 2. Second attempt: Multi-line table cells (e.g. from PDF table text streams)
        if not items:
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                # If we encounter a potential description followed by qty and currency lines
                if i + 3 < len(lines):
                    l_desc = lines[i].strip()
                    l_qty = lines[i+1].strip()
                    l_unit = lines[i+2].strip()
                    l_tot = lines[i+3].strip()

                    # Check if line 2 is numeric qty, line 3 is $price, line 4 is $price
                    if (
                        re.match(r"^\d+(?:\.\d+)?$", l_qty) and
                        re.match(r"^\$?[\d,]+\.\d{2}$", l_unit) and
                        re.match(r"^\$?[\d,]+\.\d{2}$", l_tot) and
                        not any(kw in l_desc.lower() for kw in ["subtotal", "tax", "total", "description", "qty", "unit price"])
                    ):
                        qty = float(l_qty)
                        unit = float(l_unit.replace("$", "").replace(",", ""))
                        tot = float(l_tot.replace("$", "").replace(",", ""))
                        items.append(LineItemCreate(
                            description=l_desc,
                            quantity=qty,
                            unit_price=unit,
                            total_price=tot
                        ))
                        i += 4
                        continue
                i += 1

        return items
