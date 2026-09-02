from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.enums import ScenarioStatus
from app.models.company import Company
from app.models.scenario import Scenario, SimulationRun
from app.schemas.scenario import (
    ExperimentResult,
    ScenarioCreate,
    ScenarioRead,
    ScenarioUpdate,
    SimulationRunCreate,
    SimulationRunRead,
)
from app.services.scenario_runner import seed_builtin_scenarios
from app.services.scenario_runner import seed_builtin_scenarios

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.post("/seed-builtins", response_model=dict)
def seed_builtins(db: Session = Depends(get_db)) -> dict:
    """Seed built-in scenarios if they don't exist."""
    seed_builtin_scenarios(db)
    return {"message": "Built-in scenarios seeded successfully"}


@router.get("", response_model=list[ScenarioRead])
def list_scenarios(db: Session = Depends(get_db), limit: int = 100) -> list[dict]:
    scenarios = list(
        db.execute(select(Scenario).order_by(Scenario.updated_at.desc()).limit(limit))
        .scalars()
        .all()
    )
    result = []
    for s in scenarios:
        run_count = db.execute(
            select(func.count(SimulationRun.id)).where(SimulationRun.scenario_id == s.id)
        ).scalar() or 0
        result.append({
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "category": s.category,
            "is_builtin": s.is_builtin,
            "configuration": s.configuration,
            "run_count": run_count,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        })
    return result


@router.post("", response_model=ScenarioRead, status_code=201)
def create_scenario(payload: ScenarioCreate, db: Session = Depends(get_db)) -> dict:
    config = payload.configuration.model_dump() if payload.configuration else {}
    scenario = Scenario(
        name=payload.name,
        description=payload.description or "",
        category=payload.category or "custom",
        is_builtin=False,
        configuration=config,
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return {
        "id": scenario.id,
        "name": scenario.name,
        "description": scenario.description,
        "category": scenario.category,
        "is_builtin": scenario.is_builtin,
        "configuration": scenario.configuration,
        "run_count": 0,
        "created_at": scenario.created_at.isoformat() if scenario.created_at else None,
        "updated_at": scenario.updated_at.isoformat() if scenario.updated_at else None,
    }


@router.get("/{scenario_id}", response_model=ScenarioRead)
def get_scenario(scenario_id: int, db: Session = Depends(get_db)) -> dict:
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    run_count = db.execute(
        select(func.count(SimulationRun.id)).where(SimulationRun.scenario_id == scenario.id)
    ).scalar() or 0
    return {
        "id": scenario.id,
        "name": scenario.name,
        "description": scenario.description,
        "category": scenario.category,
        "is_builtin": scenario.is_builtin,
        "configuration": scenario.configuration,
        "run_count": run_count,
        "created_at": scenario.created_at.isoformat() if scenario.created_at else None,
        "updated_at": scenario.updated_at.isoformat() if scenario.updated_at else None,
    }


@router.put("/{scenario_id}", response_model=ScenarioRead)
def update_scenario(
    scenario_id: int, payload: ScenarioUpdate, db: Session = Depends(get_db)
) -> dict:
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if scenario.is_builtin:
        raise HTTPException(status_code=403, detail="Cannot edit built-in scenarios")

    if payload.name is not None:
        scenario.name = payload.name
    if payload.description is not None:
        scenario.description = payload.description
    if payload.category is not None:
        scenario.category = payload.category
    if payload.configuration is not None:
        scenario.configuration = payload.configuration.model_dump()

    db.commit()
    db.refresh(scenario)
    run_count = db.execute(
        select(func.count(SimulationRun.id)).where(SimulationRun.scenario_id == scenario.id)
    ).scalar() or 0
    return {
        "id": scenario.id,
        "name": scenario.name,
        "description": scenario.description,
        "category": scenario.category,
        "is_builtin": scenario.is_builtin,
        "configuration": scenario.configuration,
        "run_count": run_count,
        "created_at": scenario.created_at.isoformat() if scenario.created_at else None,
        "updated_at": scenario.updated_at.isoformat() if scenario.updated_at else None,
    }


@router.delete("/{scenario_id}", status_code=204)
def delete_scenario(scenario_id: int, db: Session = Depends(get_db)) -> None:
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if scenario.is_builtin:
        raise HTTPException(status_code=403, detail="Cannot delete built-in scenarios")
    db.delete(scenario)
    db.commit()


@router.post("/{scenario_id}/duplicate", response_model=ScenarioRead, status_code=201)
def duplicate_scenario(scenario_id: int, db: Session = Depends(get_db)) -> dict:
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")

    new_scenario = Scenario(
        name=f"{scenario.name} (Copy)",
        description=scenario.description,
        category=scenario.category,
        is_builtin=False,
        configuration=scenario.configuration,
    )
    db.add(new_scenario)
    db.commit()
    db.refresh(new_scenario)
    return {
        "id": new_scenario.id,
        "name": new_scenario.name,
        "description": new_scenario.description,
        "category": new_scenario.category,
        "is_builtin": new_scenario.is_builtin,
        "configuration": new_scenario.configuration,
        "run_count": 0,
        "created_at": new_scenario.created_at.isoformat() if new_scenario.created_at else None,
        "updated_at": new_scenario.updated_at.isoformat() if new_scenario.updated_at else None,
    }


# --- Simulation Runs ---


@router.post("/{scenario_id}/runs", response_model=SimulationRunRead, status_code=201)
def create_run(
    scenario_id: int, payload: SimulationRunCreate, db: Session = Depends(get_db)
) -> dict:
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")

    run = SimulationRun(
        scenario_id=scenario_id,
        seed=payload.seed,
        simulation_days=payload.simulation_days,
        status=ScenarioStatus.PENDING,
        configuration_snapshot=scenario.configuration,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return {
        "id": run.id,
        "scenario_id": run.scenario_id,
        "company_id": run.company_id,
        "seed": run.seed,
        "status": run.status.value,
        "simulation_days": run.simulation_days,
        "configuration_snapshot": run.configuration_snapshot,
        "final_metrics": run.final_metrics,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "error_message": run.error_message,
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }


@router.get("/{scenario_id}/runs", response_model=list[SimulationRunRead])
def list_runs(scenario_id: int, db: Session = Depends(get_db), limit: int = 100) -> list[dict]:
    if db.get(Scenario, scenario_id) is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    limit = max(1, min(limit, 1000))
    runs = list(
        db.execute(
            select(SimulationRun)
            .where(SimulationRun.scenario_id == scenario_id)
            .order_by(SimulationRun.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return [
        {
            "id": r.id,
            "scenario_id": r.scenario_id,
            "company_id": r.company_id,
            "seed": r.seed,
            "status": r.status.value,
            "simulation_days": r.simulation_days,
            "configuration_snapshot": r.configuration_snapshot,
            "final_metrics": r.final_metrics,
            "started_at": r.started_at,
            "completed_at": r.completed_at,
            "error_message": r.error_message,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in runs
    ]


@router.post("/runs/{run_id}/execute", response_model=SimulationRunRead)
def execute_run_endpoint(run_id: int, db: Session = Depends(get_db)) -> dict:
    """Execute a simulation run."""
    run = db.get(SimulationRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    from app.services.scenario_runner import execute_run
    execute_run(db, run)

    return {
        "id": run.id,
        "scenario_id": run.scenario_id,
        "company_id": run.company_id,
        "seed": run.seed,
        "status": run.status.value,
        "simulation_days": run.simulation_days,
        "configuration_snapshot": run.configuration_snapshot,
        "final_metrics": run.final_metrics,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "error_message": run.error_message,
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }


@router.post("/{scenario_id}/run-experiment", response_model=list[SimulationRunRead])
def run_experiment(
    scenario_id: int, num_runs: int = 3, simulation_days: int = 50, db: Session = Depends(get_db)
) -> list[dict]:
    """Run multiple simulation runs for a scenario with different seeds."""
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")

    from app.services.scenario_runner import execute_run

    runs = []
    base_seed = 1000

    for i in range(num_runs):
        seed = base_seed + (i * 100) + (scenario_id * 7)
        run = SimulationRun(
            scenario_id=scenario_id,
            seed=seed,
            simulation_days=simulation_days,
            status=ScenarioStatus.PENDING,
            configuration_snapshot=scenario.configuration,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        runs.append(run)

    # Execute runs sequentially
    for run in runs:
        try:
            execute_run(db, run)
        except Exception:
            pass  # Status already updated by execute_run

    # Return final state of all runs
    result = []
    for run in runs:
        db.refresh(run)
        result.append({
            "id": run.id,
            "scenario_id": run.scenario_id,
            "company_id": run.company_id,
            "seed": run.seed,
            "status": run.status.value,
            "simulation_days": run.simulation_days,
            "configuration_snapshot": run.configuration_snapshot,
            "final_metrics": run.final_metrics,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
            "error_message": run.error_message,
            "created_at": run.created_at.isoformat() if run.created_at else None,
        })
    return result


@router.get("/runs/{run_id}", response_model=SimulationRunRead)
def get_run(run_id: int, db: Session = Depends(get_db)) -> dict:
    run = db.get(SimulationRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "id": run.id,
        "scenario_id": run.scenario_id,
        "company_id": run.company_id,
        "seed": run.seed,
        "status": run.status.value,
        "simulation_days": run.simulation_days,
        "configuration_snapshot": run.configuration_snapshot,
        "final_metrics": run.final_metrics,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "error_message": run.error_message,
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }


# --- Experiment Results ---


@router.get("/{scenario_id}/experiment", response_model=ExperimentResult)
def get_experiment_results(scenario_id: int, db: Session = Depends(get_db)) -> dict:
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")

    runs = list(
        db.execute(
            select(SimulationRun).where(
                SimulationRun.scenario_id == scenario_id,
                SimulationRun.status == ScenarioStatus.COMPLETED,
            )
        )
        .scalars()
        .all()
    )

    run_results = []
    for run in runs:
        if run.final_metrics:
            run_results.append({
                "run_id": run.id,
                "seed": run.seed,
                "status": run.status.value,
                "simulation_days": run.simulation_days,
                "final_day": run.final_metrics.get("current_day", 0),
                "metrics": run.final_metrics,
            })

    summary = _calculate_summary(run_results)

    return {
        "scenario_id": scenario_id,
        "scenario_name": scenario.name,
        "total_runs": len(runs),
        "completed_runs": len(run_results),
        "runs": run_results,
        "summary": summary,
    }


def _calculate_summary(run_results: list[dict]) -> dict:
    """Calculate aggregate statistics for experiment results."""
    if not run_results:
        return {}

    numeric_metrics = [
        "cash", "revenue", "expenses", "profit", "active_customers",
        "market_share", "valuation", "runway_days", "current_day",
    ]

    summary = {}
    for metric in numeric_metrics:
        values = [
            r["metrics"].get(metric, 0)
            for r in run_results
            if r["metrics"].get(metric) is not None
        ]
        if values:
            values_sorted = sorted(values)
            n = len(values_sorted)
            summary[metric] = {
                "best": max(values),
                "worst": min(values),
                "average": round(sum(values) / n, 2),
                "median": round(values_sorted[n // 2], 2) if n % 2 == 1 else round(
                    (values_sorted[n // 2 - 1] + values_sorted[n // 2]) / 2, 2
                ),
            }

    return summary
