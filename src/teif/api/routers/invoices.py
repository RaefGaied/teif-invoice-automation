from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session

from ....db.session import get_db
from ....db.services import InvoiceService, CompanyService
from ....schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    Invoice as InvoiceSchema,
    InvoiceLineCreate,
    InvoiceLine as InvoiceLineSchema,
    InvoiceStatus
)

router = APIRouter(prefix="/invoices", tags=["invoices"])

@router.get("/", response_model=List[InvoiceSchema])
async def list_invoices(
    skip: int = 0,
    limit: int = 100,
    status: Optional[InvoiceStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    company_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    List all invoices with optional filtering and pagination.
    """
    service = InvoiceService(db)
    
    if start_date or end_date:
        # If date range is provided, use the date range query
        return service.get_invoices_by_date_range(
            start_date=start_date or date.min,
            end_date=end_date or date.max,
            company_id=company_id,
            status=status,
            skip=skip,
            limit=limit
        )
    
    # Otherwise, use the basic query
    query = db.query(service.repository.model)
    if status:
        query = query.filter(service.repository.model.status == status)
    if company_id:
        query = query.filter(
            (service.repository.model.supplier_id == company_id) |
            (service.repository.model.customer_id == company_id)
        )
    
    return query.offset(skip).limit(limit).all()

@router.post("/", response_model=InvoiceSchema, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new invoice.
    """
    service = InvoiceService(db)
    
    # Create empty lines if not provided
    lines_data = invoice_data.lines or []
    
    # Remove lines from the invoice data as they'll be handled separately
    invoice_dict = invoice_data.dict(exclude={"lines"})
    
    return service.create_invoice(
        invoice_data=invoice_dict,
        lines_data=lines_data
    )

@router.get("/{invoice_id}", response_model=InvoiceSchema)
async def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """
    Get an invoice by ID with all details.
    """
    service = InvoiceService(db)
    invoice = service.get_invoice_with_details(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID {invoice_id} not found"
        )
    return invoice

@router.put("/{invoice_id}", response_model=InvoiceSchema)
async def update_invoice(
    invoice_id: int,
    invoice_in: InvoiceUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an invoice.
    """
    service = InvoiceService(db)
    invoice = service.get(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID {invoice_id} not found"
        )
    return service.update(db_obj=invoice, obj_in=invoice_in)

@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an invoice.
    """
    service = InvoiceService(db)
    invoice = service.get(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID {invoice_id} not found"
        )
    service.remove(id=invoice_id)
    return None

@router.post("/{invoice_id}/status/{status}", response_model=InvoiceSchema)
async def update_invoice_status(
    invoice_id: int,
    status: InvoiceStatus,
    db: Session = Depends(get_db)
):
    """
    Update the status of an invoice.
    """
    service = InvoiceService(db)
    try:
        return service.update_invoice_status(
            invoice_id=invoice_id,
            new_status=status,
            updated_by="api"  # In a real app, this would be the current user
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{invoice_id}/lines", response_model=List[InvoiceLineSchema])
async def get_invoice_lines(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all lines for an invoice.
    """
    service = InvoiceService(db)
    invoice = service.get_invoice_with_details(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID {invoice_id} not found"
        )
    return invoice.lines

@router.post("/{invoice_id}/lines", response_model=InvoiceLineSchema, status_code=status.HTTP_201_CREATED)
async def add_invoice_line(
    invoice_id: int,
    line: InvoiceLineCreate,
    db: Session = Depends(get_db)
):
    """
    Add a line to an invoice.
    """
    service = InvoiceService(db)
    invoice = service.get(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID {invoice_id} not found"
        )
    
    # In a real implementation, you would add the line to the invoice
    # For now, we'll just return the line data
    return line

@router.get("/statistics/")
async def get_invoice_statistics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    company_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get invoice statistics for a given period.
    """
    service = InvoiceService(db)
    return service.get_invoice_statistics(
        start_date=start_date or date.min,
        end_date=end_date or date.max,
        company_id=company_id
    )

@router.post("/upload/", response_model=InvoiceSchema, status_code=status.HTTP_201_CREATED)
async def upload_invoice_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a PDF invoice for processing.
    """
    # In a real implementation, you would:
    # 1. Save the uploaded file
    # 2. Extract data from the PDF
    # 3. Create an invoice from the extracted data
    # 4. Return the created invoice
    
    # For now, we'll just return a placeholder response
    return {
        "id": 1,
        "document_number": "INV-2023-001",
        "status": "draft",
        "message": "Invoice processing is not yet implemented"
    }
