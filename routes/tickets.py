from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from config.database import get_db
import models.models as models
import models.schemas as schemas

router = APIRouter(prefix="/tickets", tags=["Tickets"])

@router.post("", response_model=schemas.TicketResponse, status_code=201)
def create_ticket(request: Request, ticket: schemas.TicketCreate, db: Session = Depends(get_db)):
    VALID_CATEGORIES = {'Signal Loss', 'Hardware Crash', 'Screen Damage', 'Maintenance'}
    VALID_PRIORITIES = {'Low', 'Medium', 'High', 'Critical'}
    VALID_STATUSES = {'open', 'assigned', 'in_progress', 'resolved', 'closed'}
    
    if ticket.category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category: {ticket.category}")
        
    if ticket.priority not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail=f"Invalid priority: {ticket.priority}")
        
    if ticket.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {ticket.status}")
        
    existing = db.query(models.Ticket).filter(models.Ticket.ticket_no == ticket.ticket_no).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Ticket {ticket.ticket_no} already exists")
        
    outlet = db.query(models.Outlet).filter(models.Outlet.maxis_centre_id == ticket.maxis_centre_id).first()
    if not outlet:
        raise HTTPException(status_code=400, detail=f"Maxis Centre ID {ticket.maxis_centre_id} not found")
        
    created_by_id = request.state.user.get("id", 1) if hasattr(request.state, "user") and isinstance(request.state.user, dict) else 1
    
    db_ticket = models.Ticket(
        ticket_no=ticket.ticket_no,
        maxis_centre_id=ticket.maxis_centre_id,
        category=ticket.category,
        priority=ticket.priority,
        status=ticket.status,
        description=ticket.description,
        created_by=created_by_id
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

@router.get("", response_model=List[schemas.TicketResponse])
def get_tickets(
    status: Optional[str] = None, 
    skip: int = Query(0, ge=0), 
    limit: int = Query(50, le=100), 
    db: Session = Depends(get_db)
):
    query = db.query(models.Ticket)
    if status:
        query = query.filter(models.Ticket.status == status)
        
    return query.offset(skip).limit(limit).all()
