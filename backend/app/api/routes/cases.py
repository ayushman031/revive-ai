import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload, joinedload

from app.core.database import get_db
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.schemas.case import PaginatedCasesResponse, RecoveryCaseDetail

router = APIRouter(prefix="/api/v1/cases", tags=["cases"])

@router.get("", response_model=PaginatedCasesResponse)
def list_cases(
    merchant_id: uuid.UUID = Query(..., description="The ID of the merchant to fetch cases for"),
    status: str | None = Query(None, description="Optional status filter (e.g. OPEN, RECOVERED)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_db)
):
    """List recovery cases with pagination and merchant isolation."""
    query = select(RecoveryCase).options(joinedload(RecoveryCase.payment)).where(RecoveryCase.merchant_id == merchant_id)
    count_query = select(func.count(RecoveryCase.id)).where(RecoveryCase.merchant_id == merchant_id)

    if status:
        query = query.where(RecoveryCase.status == status)
        count_query = count_query.where(RecoveryCase.status == status)

    total = session.scalar(count_query) or 0

    query = query.order_by(RecoveryCase.created_at.desc()).limit(limit).offset(offset)
    cases = session.execute(query).scalars().all()

    items = []
    for case in cases:
        items.append({
            "id": case.id,
            "scenario": case.scenario,
            "status": case.status,
            "revenue_at_risk": case.revenue_at_risk,
            "currency": case.currency,
            "created_at": case.created_at,
            "closed_at": case.closed_at,
            "razorpay_order_id": case.payment.razorpay_order_id if case.payment else None
        })

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset
    }

from app.models.recommendation import Recommendation
from app.models.policy_decision import PolicyDecision

@router.get("/{case_id}", response_model=RecoveryCaseDetail)
def get_case_detail(
    case_id: uuid.UUID,
    merchant_id: uuid.UUID = Query(..., description="The ID of the merchant to ensure isolation"),
    session: Session = Depends(get_db)
):
    """Get the full timeline of a recovery case."""
    query = (
        select(RecoveryCase)
        .options(
            selectinload(RecoveryCase.trigger_attempt),
            selectinload(RecoveryCase.diagnoses),
            selectinload(RecoveryCase.predictions),
            selectinload(RecoveryCase.recovery_actions),
            selectinload(RecoveryCase.measurement),
        )
        .where(RecoveryCase.id == case_id)
        .where(RecoveryCase.merchant_id == merchant_id)
    )

    case_obj = session.execute(query).scalar_one_or_none()

    if not case_obj:
        raise HTTPException(status_code=404, detail="Recovery case not found or not owned by merchant")

    # Manually fetch Recommendations and PolicyDecisions since they lack explicit backrefs on RecoveryCase
    recommendations = session.execute(
        select(Recommendation).where(Recommendation.recovery_case_id == case_id)
    ).scalars().all()

    policy_decisions = session.execute(
        select(PolicyDecision).where(PolicyDecision.recovery_case_id == case_id)
    ).scalars().all()

    # We construct the payload manually to match the Pydantic schema precisely
    payload = {
        "id": case_obj.id,
        "merchant_id": case_obj.merchant_id,
        "scenario": case_obj.scenario,
        "status": case_obj.status,
        "revenue_at_risk": case_obj.revenue_at_risk,
        "currency": case_obj.currency,
        "created_at": case_obj.created_at,
        "closed_at": case_obj.closed_at,
        "payment_attempt": case_obj.trigger_attempt,
        "diagnoses": case_obj.diagnoses,
        "predictions": case_obj.predictions,
        "recommendations": recommendations,
        "policy_decisions": policy_decisions,
        "recovery_actions": case_obj.recovery_actions,
        "measurement": case_obj.measurement,
    }

    return payload
