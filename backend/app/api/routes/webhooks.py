"""API routes for webhook ingestion."""

import logging
from fastapi import APIRouter, Depends, Request, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_settings, Settings
from app.services.webhook_service import (
    ingest_razorpay_webhook,
    InvalidSignatureError,
    MalformedPayloadError,
    MissingEventIdError
)
from app.workers.webhook_tasks import process_webhook_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post("/razorpay", status_code=status.HTTP_200_OK)
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(None, alias="x-razorpay-signature"),
    x_razorpay_event_id: str | None = Header(None, alias="x-razorpay-event-id"),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """
    Ingest Razorpay webhooks securely.
    """
    if not settings.razorpay_webhook_secret:
        logger.error("RAZORPAY_WEBHOOK_SECRET is not configured.")
        raise HTTPException(status_code=500, detail="Server configuration error")

    if not x_razorpay_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing signature header"
        )

    # 1. Read raw body
    payload_body = await request.body()

    # 2. Ingest via service
    try:
        result = ingest_razorpay_webhook(
            payload_body=payload_body,
            signature=x_razorpay_signature,
            event_id=x_razorpay_event_id,
            secret=settings.razorpay_webhook_secret,
            session=session,
        )
    except MissingEventIdError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvalidSignatureError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except MalformedPayloadError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error during webhook ingestion")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

    # 3. Commit the transaction to ensure the row exists before Celery picks it up
    session.commit()

    # 4. Dispatch async processing ONLY if it's a new event
    if result.get("is_new"):
        logger.info(f"Dispatching task for new event {x_razorpay_event_id}")
        process_webhook_event.delay(result["event_uuid"])
    else:
        logger.info(f"Duplicate event {x_razorpay_event_id} safely ignored")

    return {"status": "ok"}
