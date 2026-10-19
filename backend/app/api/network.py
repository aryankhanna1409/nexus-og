"""Network KPI series and detected metric anomalies."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.common import MAX_PAGE, resolve_run
from app.api.deps import SessionDep, Viewer
from app.models import Anomaly as AnomalyRow
from app.models import NetworkMetric as MetricRow
from app.schemas.entities import Anomaly
from app.simulation.metrics import METRIC_NAMES

router = APIRouter(prefix="/api/network", tags=["network"])
CELL_PATTERN = r"^[0-9A-Za-z._-]{1,31}$"
METRIC_PATTERN = "^(" + "|".join(METRIC_NAMES) + ")$"


@router.get("/metrics")
def metrics(
    session: SessionDep, _: Viewer,
    metric: str = Query(..., pattern=METRIC_PATTERN),
    cell_id: str | None = Query(None, pattern=CELL_PATTERN),
    start: int | None = Query(None, ge=0, description="epoch seconds, inclusive"),
    end: int | None = Query(None, ge=0, description="epoch seconds, inclusive"),
    run_id: int | None = Query(None, ge=1),
) -> dict[str, Any]:
    """One series per cell for `metric` (all cells unless `cell_id` is given)."""
    run = resolve_run(session, run_id)
    query = select(MetricRow.cell_id, MetricRow.node_id, MetricRow.epoch, MetricRow.value).where(
        MetricRow.run_id == run.id, MetricRow.metric == metric)
    if cell_id is not None:
        query = query.where(MetricRow.cell_id == cell_id)
    if start is not None:
        query = query.where(MetricRow.epoch >= start)
    if end is not None:
        query = query.where(MetricRow.epoch <= end)
    series: dict[str, dict[str, Any]] = {}
    for cell, node, epoch, value in session.execute(query.order_by(MetricRow.cell_id, MetricRow.epoch)):
        entry = series.setdefault(cell, {"cell_id": cell, "node_id": node, "epochs": [], "values": []})
        entry["epochs"].append(epoch)
        entry["values"].append(value)
    return {"run_id": run.id, "metric": metric, "series": list(series.values())}


@router.get("/anomalies", response_model=list[Anomaly])
def anomalies(
    session: SessionDep, _: Viewer,
    run_id: int | None = Query(None, ge=1),
    cell_id: str | None = Query(None, pattern=CELL_PATTERN),
    metric: str | None = Query(None, pattern=METRIC_PATTERN),
    severity: str | None = Query(None, pattern="^(low|medium|high|critical)$"),
    limit: int = Query(500, ge=1, le=MAX_PAGE),
) -> list[AnomalyRow]:
    run = resolve_run(session, run_id)
    query = select(AnomalyRow).where(AnomalyRow.run_id == run.id)
    if cell_id:
        query = query.where(AnomalyRow.cell_id == cell_id)
    if metric:
        query = query.where(AnomalyRow.metric == metric)
    if severity:
        query = query.where(AnomalyRow.severity == severity)
    return list(session.scalars(query.order_by(AnomalyRow.start_epoch, AnomalyRow.cell_id).limit(limit)))
