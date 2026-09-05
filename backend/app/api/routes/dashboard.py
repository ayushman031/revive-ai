import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.dashboard_service import DashboardMetricsService
from app.schemas.dashboard import DashboardMetricsResponse

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

@router.get("/metrics", response_model=DashboardMetricsResponse)
def get_dashboard_metrics(
    merchant_id: uuid.UUID = Query(..., description="The ID of the merchant to fetch metrics for"),
    session: Session = Depends(get_db)
):
    """Get aggregated metrics for the dashboard, scoped by merchant_id."""
    metrics = DashboardMetricsService.get_merchant_metrics(session, merchant_id)
    return metrics
