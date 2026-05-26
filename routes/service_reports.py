import json
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from config.database import get_db
import models.models as models
import models.schemas as schemas

router = APIRouter(prefix="/operations/service-reports", tags=["Service Reports"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def process_service_manifest(request: Request, payload: schemas.ServiceReportCreatePayload, db: Session = Depends(get_db)):
    sig_check = db.query(models.Upload).filter(models.Upload.id == payload.acknowledgement.signature_png_upload_id).first()
    if not sig_check:
        raise HTTPException(status_code=404, detail={"error": {"code": "SR_PHOTOS_MISSING", "message": "Signature mapping violation: ID not found in registry."}})

    do_check = db.query(models.DeliveryOrder).filter(models.DeliveryOrder.do_no == payload.do_no).first()
    if not do_check:
        raise HTTPException(status_code=404, detail={"error": {"code": "SR_DO_MISMATCH", "message": f"Delivery Order reference {payload.do_no} does not exist."}})

    existing_sr = db.query(models.ServiceReport).filter(models.ServiceReport.sr_no == payload.sr_no).first()
    if existing_sr:
        raise HTTPException(status_code=400, detail={"error": {"code": "VALIDATION_FAILED", "message": f"Conflict Error: Report number {payload.sr_no} is already locked."}})

    try:
        # Step 1: Insert parent entry
        db_report = models.ServiceReport(
            sr_no=payload.sr_no,
            do_id=do_check.id,
            ticket_id=payload.ticket_id,
            wo_number=payload.wo_number,
            remedy_number=payload.remedy_number,
            client_company=payload.client.company,
            client_addr_json=json.dumps(payload.client.company_address),
            store_type=payload.client.store_type,
            store_name=payload.client.store_name,
            pic_name=payload.client.pic_name,
            pic_tel=payload.client.pic_tel,
            diagnostic=payload.diagnostic,
            action_taken=payload.action_taken,
            before_photos_json="[]",
            after_photos_json="[]",
            ack_signed_by=payload.acknowledgement.signed_by,
            ack_signature_upload_id=sig_check.id,
            ack_signed_at=datetime.now(timezone.utc),
            created_by=request.state.user.get("id", 1) if hasattr(request.state, "user") and isinstance(request.state.user, dict) else 1
        )
        db.add(db_report)
        db.flush()
        
        if payload.ticket_id:
            ticket = db.query(models.Ticket).filter(models.Ticket.id == payload.ticket_id).first()
            if ticket:
                ticket.status = 'resolved'
                db.add(ticket)
        
        # Fetch the Delivery Order to get the correct maxis_centre_id for installations
        do_record = db.query(models.DeliveryOrder).filter(models.DeliveryOrder.id == db_report.do_id).first()

        # Step 2: Loop through hardware swaps
        if payload.hardware_swaps:
            for swap in payload.hardware_swaps:
                db_swap = models.SrHardware(
                    sr_id=db_report.id,
                    direction=swap.direction,
                    sku_id=swap.sku_id,
                    item_code=swap.item_code,
                    reason=swap.reason,
                    is_faulty=swap.is_faulty
                )
                db.add(db_swap)
                
                # Step 3: Mutate asset_skus
                asset = db.query(models.AssetSku).filter(models.AssetSku.id == swap.sku_id).first()
                if not asset:
                    raise Exception(f"Asset SKU ID {swap.sku_id} not found in inventory registry.")
                    
                if swap.direction == 'removed':
                    asset.state = 'to be disposed' if swap.is_faulty else 'unassign'
                    asset.maxis_centre_id = None
                elif swap.direction == 'installed':
                    asset.state = 'deployed'
                    asset.maxis_centre_id = do_record.maxis_centre_id
                    
                db.add(asset)
                db.flush()

        db.commit()
        return {"status": "Success", "message": f"Ledger entries completely synchronized for {payload.sr_no}"}
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=500, detail={"error": {"code": "SERVER_ERROR", "message": f"Database state breakdown: {str(err)}"}})

@router.get("/{sr_no}/download")
async def extract_service_pdf(sr_no: str, db: Session = Depends(get_db)):
    report_record = db.query(models.ServiceReport).filter(models.ServiceReport.sr_no == sr_no).first()
    if not report_record:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Target document reference not found."}})
    return {"status": "Mock Stream Pass", "msg": f"Ready to download report {sr_no}"}
