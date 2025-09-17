import traceback
from typing import List, Optional, Union, Dict, Any
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, Response
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, or_
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse

from src.teif.db.session import get_db
from src.teif.db.services.invoice_service import InvoiceService
from src.teif.db.services.company_service import CompanyService

from src.teif.db.models.tax import LineTax, InvoiceTax, InvoiceMonetaryAmount
from src.teif.db.models.payment import PaymentTerm, PaymentMean
from src.teif.db.models.signature import InvoiceSignature, GeneratedXmlFile
from src.teif.db.models.company import Company, CompanyContact, ContactCommunication
from src.teif.db.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    Invoice as InvoiceSchema,
    InvoiceLineCreate,
    InvoiceLine as InvoiceLineSchema,
    InvoiceStatus,
)
from src.teif.generator import TEIFGenerator
import logging

from teif.db.models.invoice import InvoiceLine, InvoiceStatus
# Add these imports at the top of the file
from src.teif.db.models.invoice import Invoice as InvoiceModel, InvoiceLine as InvoiceLineModel
from src.teif.db.schemas.invoice import InvoiceLine as InvoiceLineSchema

logger = logging.getLogger(__name__)

router = APIRouter()

class InvoiceResponse(BaseModel):
    """Pydantic model for invoice response."""
    id: int
    teif_version: str = Field(..., alias="teif_version")
    controlling_agency: str = Field(..., alias="controlling_agency")
    sender_identifier: str = Field(..., alias="sender_identifier")
    receiver_identifier: str = Field(..., alias="receiver_identifier")
    message_identifier: Optional[str] = Field(None, alias="message_identifier")
    message_datetime: datetime = Field(..., alias="message_datetime")
    document_number: str = Field(..., alias="document_number")
    document_type: str = Field(..., alias="document_type")
    document_type_label: str = Field(..., alias="document_type_label")
    document_status: str = Field(..., alias="document_status")
    invoice_date: date = Field(..., alias="invoice_date")
    due_date: Optional[date] = Field(None, alias="due_date")
    period_start_date: Optional[date] = Field(None, alias="period_start_date")
    period_end_date: Optional[date] = Field(None, alias="period_end_date")
    supplier_id: int = Field(..., alias="supplier_id")
    customer_id: int = Field(..., alias="customer_id")
    delivery_party_id: Optional[int] = Field(None, alias="delivery_party_id")
    currency: str = Field(..., alias="currency")
    currency_code_list: Optional[str] = Field(None, alias="currency_code_list")
    capital_amount: float = Field(..., alias="capital_amount")
    total_with_tax: float = Field(..., alias="total_with_tax")
    total_without_tax: float = Field(..., alias="total_without_tax")
    tax_base_amount: float = Field(..., alias="tax_base_amount")
    tax_amount: float = Field(..., alias="tax_amount")
    payment_terms: Optional[str] = Field(None, alias="payment_terms")
    payment_means_code: Optional[str] = Field(None, alias="payment_means_code")
    payment_means_text: Optional[str] = Field(None, alias="payment_means_text")
    notes: Optional[str] = Field(None, alias="notes")
    additional_info: Optional[Dict[str, Any]] = Field(None, alias="additional_info")
    created_at: datetime = Field(..., alias="created_at")
    updated_at: Optional[datetime] = Field(None, alias="updated_at")
    
    class Config:
        orm_mode = True
        allow_population_by_field_name = True

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
    return service.get_multi(skip=skip, limit=limit, status=status, company_id=company_id)

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
    document_number: str = Form(...),
    invoice_date: date = Form(...),
    due_date: date = Form(...),
    supplier_id: int = Form(...),
    customer_id: int = Form(...),
    status: InvoiceStatus = Form(InvoiceStatus.PROCESSING),
    currency: str = Form("TND"),
    notes: Optional[str] = Form(None),
    terms: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a PDF invoice for processing.
    
    Required form fields:
    - document_number: Invoice number (e.g., 'INV-2023-001')
    - invoice_date: Invoice date (YYYY-MM-DD)
    - due_date: Payment due date (YYYY-MM-DD)
    - supplier_id: ID of the supplier company
    - customer_id: ID of the customer company
    
    Optional form fields:
    - status: Invoice status (default: 'processing')
    - currency: Currency code (default: 'TND')
    - notes: Additional notes
    - terms: Payment terms
    - file: The PDF file to upload
    """
    try:
        # Create the invoice data dictionary
        invoice_data = {
            "document_number": document_number,
            "invoice_date": invoice_date,
            "due_date": due_date,
            "supplier_id": supplier_id,
            "customer_id": customer_id,
            "status": status,
            "currency": currency,
            "notes": notes,
            "terms": terms,
            "lines": []  # We'll process lines from the PDF later
        }
        
        # Save the uploaded file to a temporary location
        # In a real implementation, you would save this to a proper storage
        file_location = f"temp/{file.filename}"
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())
        
        # TODO: Process the PDF and extract invoice lines
        # For now, we'll create an invoice with no lines
        
        # Create the invoice in the database
        invoice_service = InvoiceService(db)
        created_invoice = invoice_service.create_invoice(
            invoice_data=InvoiceCreate(**invoice_data),
            created_by="api_upload"
        )
        
        # In a real implementation, you would:
        # 1. Process the PDF to extract line items
        # 2. Add the extracted lines to the invoice
        # 3. Update the invoice totals
        
        return created_invoice
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing invoice: {str(e)}"
        )

@router.get("/export/", response_model=List[InvoiceResponse])
async def export_invoices(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    invoice_status: Optional[InvoiceStatus] = None,
    company_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Export invoices with filtering by date range, status, and company.
    
    Parameters:
    - start_date: Filter invoices from this date (inclusive)
    - end_date: Filter invoices until this date (inclusive)
    - invoice_status: Filter by invoice status (draft, uploading, uploaded, processing, generated, error, archived)
    - company_id: Filter by company ID (either as supplier or customer)
    - skip: Number of records to skip for pagination
    - limit: Maximum number of records to return
    """
    try:
        service = InvoiceService(db)
        
        # If date range is provided, use the date range query
        if start_date or end_date:
            invoices = service.get_invoices_by_date_range(
                start_date=start_date or date.min,
                end_date=end_date or date.max,
                company_id=company_id,
                status=invoice_status,
                skip=skip,
                limit=limit
            )
            total = service.invoice_repo.db.query(InvoiceModel).filter(
                InvoiceModel.invoice_date.between(
                    start_date or date.min, 
                    end_date or date.max
                )
            ).count()
        else:
            # Otherwise, use the basic query
            invoices = service.get_multi(
                skip=skip, 
                limit=limit, 
                status=invoice_status, 
                company_id=company_id
            )
            total = service.invoice_repo.count()
        
        # Create response with headers
        response = JSONResponse(
            content=[InvoiceResponse.from_orm(invoice).dict() for invoice in invoices]
        )
        response.headers["X-Total-Count"] = str(total)
        response.headers["X-Page-Size"] = str(limit)
        response.headers["X-Page"] = str(skip // limit + 1 if limit > 0 else 1)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in export_invoices: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,  
            detail=f"Error exporting invoices: {str(e)}"
        )

@router.get("/{invoice_id}/xml", response_class=Response, responses={
    200: {
        "content": {"application/xml": {}},
        "description": "Retourne le XML de la facture au format TEIF",
    }
})
async def generate_invoice_xml(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """
    Génère le XML d'une facture selon le standard TEIF.
    
    Args:
        invoice_id: L'ID de la facture à exporter
        
    Returns:
        Response: Le contenu XML de la facture avec l'en-tête Content-Type approprié
    """
    # Récupérer la facture avec toutes les relations nécessaires
    invoice = db.query(InvoiceModel)\
        .options(
            joinedload(InvoiceModel.supplier).joinedload(Company.contacts).joinedload(CompanyContact.communications),
            joinedload(InvoiceModel.customer).joinedload(Company.contacts).joinedload(CompanyContact.communications),
            joinedload(InvoiceModel.lines).joinedload(InvoiceLine.taxes),
            joinedload(InvoiceModel.taxes),
            joinedload(InvoiceModel.payment_terms),
            joinedload(InvoiceModel.special_conditions)
        )\
        .filter(InvoiceModel.id == invoice_id)\
        .first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Facture avec l'ID {invoice_id} non trouvée"
        )
    
    try:
        # Convertir la facture en dictionnaire pour le générateur
        invoice_dict = {
            "header": {
                "invoice_number": invoice.document_number,
                "invoice_date": invoice.invoice_date.isoformat(),
                "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
                "currency": invoice.currency or "TND",
                "notes": invoice.notes,
                "status": invoice.status if invoice.status else "draft"
            },
            "seller": {
                "identifier": invoice.supplier.identifier if invoice.supplier else "",
                "name": invoice.supplier.name if invoice.supplier else "",
                "vat_number": invoice.supplier.vat_number if invoice.supplier else "",
                "tax_identifier": invoice.supplier.vat_number if invoice.supplier else "",
                "address": {
                    "street": invoice.supplier.address_street if invoice.supplier else "",
                    "city": invoice.supplier.address_city if invoice.supplier else "",
                    "postal_code": invoice.supplier.address_postal_code if invoice.supplier else "",
                    "country": invoice.supplier.address_country_code if invoice.supplier else "TN"
                },
                "contact": {
                    "name": next((c.contact_name for c in (invoice.supplier.contacts if invoice.supplier else []) if c.function_code == "SU"), ""),
                    "email": next((c.communications[0].communication_value for c in (invoice.supplier.contacts if invoice.supplier else []) if c.function_code == "SU" and c.communications and c.communications[0].communication_type == "EM"), ""),
                    "phone": next((c.communications[0].communication_value for c in (invoice.supplier.contacts if invoice.supplier else []) if c.function_code == "SU" and c.communications and c.communications[0].communication_type == "TE"), "")
                }
            },
            "buyer": {
                # Use getattr with a default empty string to safely access the identifier
                "identifier": getattr(invoice.customer, 'identifier', '') if invoice.customer else "",
                "name": invoice.customer.name if invoice.customer else "",
                "vat_number": getattr(invoice.customer, 'vat_number', '') if invoice.customer else "",
                "tax_identifier": getattr(invoice.customer, 'vat_number', '') if invoice.customer else "",
                "address": {
                    "street": getattr(invoice.customer, 'address_street', '') if invoice.customer else "",
                    "city": getattr(invoice.customer, 'address_city', '') if invoice.customer else "",
                    "postal_code": getattr(invoice.customer, 'address_postal_code', '') if invoice.customer else "",
                    "country": getattr(invoice.customer, 'address_country_code', 'TN') if invoice.customer else "TN"
                },
                "contact": {
                    "name": next((c.contact_name for c in (invoice.customer.contacts if invoice.customer else []) if c.function_code == "BY"), ""),
                    "email": next((c.communications[0].communication_value for c in (invoice.customer.contacts if invoice.customer else []) if c.function_code == "BY" and c.communications and c.communications[0].communication_type == "EM"), ""),
                    "phone": next((c.communications[0].communication_value for c in (invoice.customer.contacts if invoice.customer else []) if c.function_code == "BY" and c.communications and c.communications[0].communication_type == "TE"), "")
                }
            },
            "lines": [
                {
                    "item_code": line.item_code or "",
                    "description": line.description,
                    "quantity": float(line.quantity) if line.quantity else 1.0,
                    "unit_price": float(line.unit_price) if line.unit_price else 0.0,
                    "tax_rate": float(line.taxes[0].rate) if line.taxes and line.taxes[0] else 0.0,
                    "discount": float(line.discount_amount) if line.discount_amount else 0.0,
                    "currency": line.currency or "TND"
                }
                for line in invoice.lines
            ],
            "summary": {
                "total_without_tax": float(invoice.total_without_tax) if invoice.total_without_tax else 0.0,
                "total_tax": float(invoice.tax_amount) if invoice.tax_amount else 0.0,
                "total_with_tax": float(invoice.total_with_tax) if invoice.total_with_tax else 0.0,
                "currency": invoice.currency or "TND"
            },
            "payment_terms": invoice.payment_terms[0].description if invoice.payment_terms else "",
            "additional_notes": "\n".join([f"{cond.sequence_number}. {cond.condition_text}" for cond in invoice.special_conditions]) if invoice.special_conditions else ""
        }
        
        # Générer le XML
        generator = TEIFGenerator()
        xml_content = generator.generate_teif_xml(invoice_dict)
        
        # Retourner la réponse XML
        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={
                "Content-Disposition": f"attachment; filename=facture_{invoice.document_number}.xml"
            }
        )
    except Exception as e:
        # Journaliser l'erreur pour le débogage
        logger.error(f"Erreur lors de la génération du XML pour la facture {invoice_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération du XML: {str(e)}"
        )
