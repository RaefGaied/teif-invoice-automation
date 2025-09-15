from datetime import date, datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload, load_only, contains_eager
from sqlalchemy import and_, or_, func

from ..models.invoice import Invoice, InvoiceLine, InvoiceReference, AdditionalDocument, SpecialCondition
from ..models.tax import LineTax, InvoiceTax
from ..models.company import Company
from .base import BaseRepository
from teif.db.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceLineCreate, InvoiceLineUpdate
from teif.db.models.payment import PaymentTerm, PaymentMean

class InvoiceRepository(BaseRepository[Invoice, InvoiceCreate, InvoiceUpdate]):
    """Repository for invoice operations."""
    
    def __init__(self, db: Session):
        super().__init__(Invoice, db)
    
    def get_with_details(self, id: int) -> Optional[Invoice]:
        """Get an invoice by ID with all related data loaded."""
        from sqlalchemy.orm import load_only, contains_eager
        
        # Import models to reference their attributes
        from ..models.invoice import InvoiceLine, InvoiceReference, AdditionalDocument, SpecialCondition
        from ..models.tax import LineTax, InvoiceTax
        from ..models.payment import PaymentTerm, PaymentMean
        from ..models.company import Company
        
        # Define column sets using class attributes
        company_columns = [
            Company.id, Company.identifier, Company.name, Company.vat_number, 
            Company.tax_id, Company.commercial_register, Company.address_street,
            Company.address_city, Company.address_postal_code, 
            Company.address_country_code, Company.phone, Company.email,
            Company.fax, Company.website, Company.created_at
        ]
        
        line_columns = [
            InvoiceLine.id, InvoiceLine.invoice_id, InvoiceLine.line_number,
            InvoiceLine.parent_line_id, InvoiceLine.item_identifier,
            InvoiceLine.item_code, InvoiceLine.description, InvoiceLine.quantity,
            InvoiceLine.unit, InvoiceLine.unit_price, InvoiceLine.line_total_ht,
            InvoiceLine.discount_amount, InvoiceLine.discount_reason,
            InvoiceLine.currency, InvoiceLine.currency_code_list,
            InvoiceLine.line_date, InvoiceLine.created_at
        ]
        
        line_tax_columns = [
            LineTax.id, LineTax.line_id, LineTax.tax_code, 
            LineTax.tax_type, LineTax.tax_category, LineTax.tax_rate, 
            LineTax.taxable_amount, LineTax.tax_amount,
            LineTax.currency_code_list, LineTax.created_at
        ]
        
        invoice_tax_columns = [
            InvoiceTax.id, InvoiceTax.invoice_id, InvoiceTax.tax_code,
            InvoiceTax.tax_type, InvoiceTax.tax_category, InvoiceTax.tax_rate,
            InvoiceTax.taxable_amount, InvoiceTax.tax_amount,
            InvoiceTax.currency_code_list, InvoiceTax.created_at
        ]
        
        # First, load the invoice with basic relationships
        query = self.db.query(Invoice).options(
            joinedload(Invoice.lines, innerjoin=False).load_only(*line_columns),
            joinedload(Invoice.taxes, innerjoin=False).load_only(*invoice_tax_columns),
            joinedload(Invoice.references, innerjoin=False).load_only(
                InvoiceReference.id, InvoiceReference.invoice_id,
                InvoiceReference.reference_type, InvoiceReference.reference_value,
                InvoiceReference.description, InvoiceReference.created_at
            ),
            joinedload(Invoice.additional_documents, innerjoin=False).load_only(
                AdditionalDocument.id, AdditionalDocument.invoice_id,
                AdditionalDocument.document_id, AdditionalDocument.document_type,
                AdditionalDocument.document_name, AdditionalDocument.document_date,
                AdditionalDocument.description, AdditionalDocument.file_path,
                AdditionalDocument.created_at
            ),
            joinedload(Invoice.special_conditions, innerjoin=False).load_only(
                SpecialCondition.id, SpecialCondition.invoice_id,
                SpecialCondition.condition_text, SpecialCondition.language_code,
                SpecialCondition.sequence_number, SpecialCondition.created_at
            ),
            joinedload(Invoice.payment_terms, innerjoin=False).load_only(
                PaymentTerm.id, PaymentTerm.invoice_id,
                PaymentTerm.payment_terms_code, PaymentTerm.description,
                PaymentTerm.discount_percent, PaymentTerm.discount_due_date,
                PaymentTerm.payment_due_date, PaymentTerm.created_at
            ),
            joinedload(Invoice.payment_means, innerjoin=False).load_only(
                PaymentMean.id, PaymentMean.invoice_id,
                PaymentMean.payment_means_code, PaymentMean.payment_id,
                PaymentMean.due_date, PaymentMean.iban,
                PaymentMean.account_holder, PaymentMean.financial_institution,
                PaymentMean.branch_code, PaymentMean.created_at
            ),
            joinedload(Invoice.supplier, innerjoin=False).load_only(*company_columns),
            joinedload(Invoice.customer, innerjoin=False).load_only(*company_columns)
        ).filter(Invoice.id == id)
        
        # Then load the line taxes in a separate query to avoid the relationship issue
        invoice = query.first()
        if invoice and invoice.lines:
            # Load taxes for all lines in one query
            line_ids = [line.id for line in invoice.lines]
            if line_ids:
                line_taxes = self.db.query(LineTax)\
                    .with_entities(*line_tax_columns)\
                    .filter(LineTax.line_id.in_(line_ids))\
                    .all()
                
                # Assign taxes to their respective lines
                tax_map = {}
                for tax in line_taxes:
                    if tax.line_id not in tax_map:
                        tax_map[tax.line_id] = []
                    tax_map[tax.line_id].append(tax)
                
                for line in invoice.lines:
                    line.taxes = tax_map.get(line.id, [])
        
        return invoice
    
    def get_by_document_number(self, document_number: str) -> Optional[Invoice]:
        """Get an invoice by its document number."""
        return self.db.query(Invoice).filter(
            func.lower(Invoice.document_number) == func.lower(document_number)
        ).first()
    
    def get_invoices_by_date_range(
        self, 
        start_date: date, 
        end_date: date,
        company_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Invoice]:
        """Get invoices within a date range with pagination and optional filters."""
        query = self.db.query(Invoice).options(
            joinedload(Invoice.lines)
                .joinedload(InvoiceLine.taxes),  # Add eager loading for line taxes
            joinedload(Invoice.supplier),
            joinedload(Invoice.customer)
        ).filter(
            and_(
                Invoice.invoice_date >= start_date,
                Invoice.invoice_date <= end_date
            )
        )
        
        if company_id:
            query = query.filter(
                or_(
                    Invoice.supplier_id == company_id,
                    Invoice.customer_id == company_id
                )
            )
            
        if status:
            query = query.filter(Invoice.status == status)
        
        return query.order_by(Invoice.invoice_date.desc())\
                   .offset(skip)\
                   .limit(limit)\
                   .all()
    
    def get_invoices_by_supplier(
        self, 
        supplier_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Invoice]:
        """Get all invoices for a specific supplier."""
        return self.db.query(Invoice).filter(
            Invoice.supplier_id == supplier_id
        ).order_by(Invoice.invoice_date.desc()).offset(skip).limit(limit).all()
    
    def get_invoices_by_customer(
        self, 
        customer_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Invoice]:
        """Get all invoices for a specific customer."""
        return self.db.query(Invoice).filter(
            Invoice.customer_id == customer_id
        ).order_by(Invoice.invoice_date.desc()).offset(skip).limit(limit).all()
    
    def search_invoices(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Invoice]:
        """Search invoices by document number, customer name, or supplier name."""
        search = f"%{query}%"
        return self.db.query(Invoice).join(
            Invoice.customer
        ).join(
            Invoice.supplier
        ).filter(
            or_(
                Invoice.document_number.ilike(search),
                Company.name_ar.ilike(search),  
                Company.name_fr.ilike(search),  
                Company.name_ar.ilike(search),  
                Company.name_fr.ilike(search)   
            )
        ).order_by(Invoice.invoice_date.desc()).offset(skip).limit(limit).all()
    
    def create_with_lines(
        self, 
        obj_in: InvoiceCreate, 
        lines: List[InvoiceLineCreate]
    ) -> Invoice:
        """Create an invoice with its line items in a transaction."""
        try:
            # Start transaction
            db_invoice = Invoice(**obj_in.dict(exclude={"lines"}))
            self.db.add(db_invoice)
            self.db.flush()  # Get the invoice ID
            
            # Add lines
            for line_in in lines:
                db_line = InvoiceLine(
                    **line_in.dict(),
                    invoice_id=db_invoice.id
                )
                self.db.add(db_line)
            
            self.db.commit()
            self.db.refresh(db_invoice)
            return db_invoice
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def update_status(
        self, 
        db_obj: Invoice, 
        status: str,
        status_date: Optional[datetime] = None
    ) -> Invoice:
        """Update the status of an invoice."""
        db_obj.status = status
        if status_date:
            db_obj.status_date = status_date
        else:
            db_obj.status_date = datetime.utcnow()
            
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def get_totals_by_period(
        self,
        start_date: date,
        end_date: date,
        group_by: str = 'day'  # 'day', 'month', 'year', 'supplier', 'customer'
    ) -> List[Dict[str, Any]]:
        """Get invoice totals grouped by the specified period."""
        if group_by == 'day':
            date_part = func.date(Invoice.invoice_date)
        elif group_by == 'month':
            date_part = func.date_trunc('month', Invoice.invoice_date)
        elif group_by == 'year':
            date_part = func.date_trunc('year', Invoice.invoice_date)
        else:
            date_part = func.date(Invoice.invoice_date)
        
        return self.db.query(
            date_part.label('period'),
            func.count(Invoice.id).label('invoice_count'),
            func.sum(Invoice.total_amount_ht).label('total_ht'),
            func.sum(Invoice.total_amount_tva).label('total_tva'),
            func.sum(Invoice.total_amount_ttc).label('total_ttc')
        ).filter(
            and_(
                Invoice.invoice_date >= start_date,
                Invoice.invoice_date <= end_date
            )
        ).group_by('period').order_by('period').all()
    
    def get_invoice_statistics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        company_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get invoice statistics for a given period and optional filters.
        
        Args:
            start_date: Start date for the period
            end_date: End date for the period
            company_id: Optional company ID to filter by (supplier or customer)
            status: Optional invoice status filter
            
        Returns:
            Dictionary containing various invoice statistics
        """
        query = self.db.query(Invoice)
        
        # Apply date filters
        if start_date:
            query = query.filter(Invoice.invoice_date >= start_date)
        if end_date:
            query = query.filter(Invoice.invoice_date <= end_date)
            
        # Apply company filter if provided
        if company_id:
            query = query.filter(
                or_(
                    Invoice.supplier_id == company_id,
                    Invoice.customer_id == company_id
                )
            )
            
        # Apply status filter if provided
        if status:
            query = query.filter(Invoice.status == status)
            
        # Get total count and amounts
        total_invoices = query.count()
        total_amount = query.with_entities(func.coalesce(func.sum(Invoice.total_amount), 0)).scalar() or 0
        total_tax = query.with_entities(func.coalesce(func.sum(Invoice.total_tax_amount), 0)).scalar() or 0
        
        # Get status distribution
        status_distribution = dict(
            self.db.query(
                Invoice.status,
                func.count(Invoice.id)
            ).group_by(Invoice.status).all()
        )
        
        # Get monthly totals for the last 12 months
        monthly_totals = dict(
            self.db.query(
                func.date_trunc('month', Invoice.invoice_date).label('month'),
                func.sum(Invoice.total_amount).label('total')
            )
            .filter(Invoice.invoice_date >= func.date_trunc('month', func.current_date() - func.make_interval(months=11)))
            .group_by('month')
            .order_by('month')
            .all()
        )
        
        return {
            'total_invoices': total_invoices,
            'total_amount': float(total_amount),
            'total_tax': float(total_tax),
            'status_distribution': status_distribution,
            'monthly_totals': {str(k): float(v) for k, v in monthly_totals.items()}
        }

    def get_outstanding_invoices(
        self,
        company_id: int,
        as_supplier: bool = True,
        due_before: Optional[date] = None
    ) -> List[Invoice]:
        """
        Get all outstanding (unpaid) invoices for a company.
        
        Args:
            company_id: The company ID (supplier or customer)
            as_supplier: If True, get invoices where the company is the supplier,
                        if False, get invoices where the company is the customer
            due_before: Optional due date filter to get invoices due before a specific date
            
        Returns:
            List of outstanding invoices
        """
        query = self.db.query(Invoice).filter(
            Invoice.status == 'unpaid'
        )
        
        if as_supplier:
            query = query.filter(Invoice.supplier_id == company_id)
        else:
            query = query.filter(Invoice.customer_id == company_id)
            
        if due_before:
            query = query.filter(Invoice.due_date <= due_before)
            
        return query.order_by(Invoice.due_date).all()

    def get_invoices_by_status(
        self,
        status: str,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = 'invoice_date',
        sort_order: str = 'desc'
    ) -> List[Invoice]:
        """
        Get invoices by status with sorting and pagination.
        
        Args:
            status: Invoice status to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')
            
        Returns:
            List of invoices matching the status
        """
        query = self.db.query(Invoice).filter(
            Invoice.status == status
        )
        
        # Apply sorting
        sort_column = getattr(Invoice, sort_by, None)
        if sort_column is not None:
            if sort_order.lower() == 'desc':
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
                
        return query.offset(skip).limit(limit).all()

    def get_yearly_totals(
        self,
        year: int,
        company_id: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Get monthly invoice totals for a specific year.
        
        Args:
            year: The year to get totals for
            company_id: Optional company ID to filter by (supplier or customer)
            
        Returns:
            Dictionary with month numbers as keys and total amounts as values
        """
        query = self.db.query(
            func.extract('month', Invoice.invoice_date).label('month'),
            func.sum(Invoice.total_amount).label('total')
        ).filter(
            func.extract('year', Invoice.invoice_date) == year
        )
        
        if company_id:
            query = query.filter(
                or_(
                    Invoice.supplier_id == company_id,
                    Invoice.customer_id == company_id
                )
            )
            
        results = query.group_by('month').order_by('month').all()
        
        # Convert to a dictionary with month as key and total as value
        return {int(month): float(total) for month, total in results}

    def get_company_financial_overview(
        self,
        company_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get financial overview for a company.
        
        Args:
            company_id: The company ID
            start_date: Optional start date for the period
            end_date: Optional end date for the period
            
        Returns:
            Dictionary containing financial overview data
        """
        # Base queries
        as_supplier = self.db.query(
            func.count(Invoice.id).label('count'),
            func.coalesce(func.sum(Invoice.total_amount), 0).label('total')
        ).filter(Invoice.supplier_id == company_id)
        
        as_customer = self.db.query(
            func.count(Invoice.id).label('count'),
            func.coalesce(func.sum(Invoice.total_amount), 0).label('total')
        ).filter(Invoice.customer_id == company_id)
        
        # Apply date filters if provided
        if start_date:
            as_supplier = as_supplier.filter(Invoice.invoice_date >= start_date)
            as_customer = as_customer.filter(Invoice.invoice_date >= start_date)
            
        if end_date:
            as_supplier = as_supplier.filter(Invoice.invoice_date <= end_date)
            as_customer = as_customer.filter(Invoice.invoice_date <= end_date)
        
        # Execute queries
        supplier_stats = as_supplier.first()
        customer_stats = as_customer.first()
        
        # Get outstanding amounts
        outstanding_as_supplier = self.db.query(
            func.coalesce(func.sum(Invoice.total_amount - Invoice.paid_amount), 0)
        ).filter(
            Invoice.supplier_id == company_id,
            Invoice.status.in_(['unpaid', 'partially_paid'])
        ).scalar() or 0
        
        outstanding_as_customer = self.db.query(
            func.coalesce(func.sum(Invoice.total_amount - Invoice.paid_amount), 0)
        ).filter(
            Invoice.customer_id == company_id,
            Invoice.status.in_(['unpaid', 'partially_paid'])
        ).scalar() or 0
        
        return {
            'as_supplier': {
                'total_invoices': supplier_stats[0] if supplier_stats else 0,
                'total_amount': float(supplier_stats[1]) if supplier_stats else 0.0,
                'outstanding': float(outstanding_as_supplier)
            },
            'as_customer': {
                'total_invoices': customer_stats[0] if customer_stats else 0,
                'total_amount': float(customer_stats[1]) if customer_stats else 0.0,
                'outstanding': float(outstanding_as_customer)
            }
        }

    def get_multi(
        self, 
        *, 
        skip: int = 0, 
        limit: int = 100, 
        status: Optional[str] = None, 
        company_id: Optional[int] = None
    ) -> List[Invoice]:
        """Get multiple invoices with optional filtering by status and company.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Optional status to filter by
            company_id: Optional company ID to filter by (as supplier or customer)
            
        Returns:
            List of Invoice objects
        """
        query = self.db.query(Invoice)
        
        # Apply status filter if provided
        if status is not None:
            query = query.filter(Invoice.status == status)
            
        # Apply company filter if provided (matches either supplier or customer)
        if company_id is not None:
            query = query.filter(
                (Invoice.supplier_id == company_id) | 
                (Invoice.customer_id == company_id)
            )
            
        # Order by most recent first
        return query.order_by(
            Invoice.invoice_date.desc()
        ).offset(skip).limit(limit).all()