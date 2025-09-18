# src/teif/api/routers/dashboard.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Dict, Any

from teif.db import get_db
from teif.db.models.invoice import Invoice
from teif.db.models.company import Company

# Create the router instance
router = APIRouter()

@router.get("/stats", response_model=Dict[str, Any])
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    try:
        # Get total counts
        total_invoices = db.query(Invoice).count()
        total_companies = db.query(Company).count()
        
        # Get financial totals
        financials = db.query(
            func.coalesce(func.sum(Invoice.total_with_tax), 0).label('total_with_tax'),
            func.coalesce(func.sum(Invoice.total_without_tax), 0).label('total_without_tax'),
            func.coalesce(func.sum(Invoice.tax_amount), 0).label('tax_amount')
        ).first()
        
        # Get invoice status counts
        status_counts = db.query(
            Invoice.status,
            func.count(Invoice.id)
        ).group_by(Invoice.status).all()
        
        return {
            "status": "success",
            "data": {
                "totals": {
                    "invoices": total_invoices,
                    "companies": total_companies,
                    "revenue": float(financials.total_with_tax) if financials else 0,
                    "tax": float(financials.tax_amount) if financials else 0,
                    "net": float(financials.total_without_tax) if financials else 0,
                },
                "status": dict(status_counts)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching dashboard stats: {str(e)}"
        )

@router.get("/monthly-stats", response_model=List[Dict[str, Any]])
async def get_monthly_stats(months: int = 6, db: Session = Depends(get_db)):
    """Get monthly statistics for the last N months"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30*months)
        
        monthly_data = db.query(
            func.date_trunc('month', Invoice.invoice_date).label('month'),
            func.count(Invoice.id).label('invoice_count'),
            func.coalesce(func.sum(Invoice.total_with_tax), 0).label('total_amount'),
            func.coalesce(func.sum(Invoice.tax_amount), 0).label('tax_amount')
        ).filter(
            Invoice.invoice_date.between(start_date, end_date)
        ).group_by(
            func.date_trunc('month', Invoice.invoice_date)
        ).order_by('month').all()
        
        return [{
            "month": month.strftime('%Y-%m'),
            "invoice_count": int(invoice_count),
            "total_amount": float(total_amount),
            "tax_amount": float(tax_amount)
        } for month, invoice_count, total_amount, tax_amount in monthly_data]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching monthly stats: {str(e)}"
        )

# Make sure the router is exported
__all__ = ["router"]