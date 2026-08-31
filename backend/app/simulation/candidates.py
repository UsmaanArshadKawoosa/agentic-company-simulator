"""Candidate generation and evaluation system.

Candidates are generated deterministically from company seed + simulation day + candidate index.
"""

from __future__ import annotations

import logging
import random

from sqlalchemy import select

from app.models.candidate import Candidate
from app.models.job_opening import JobOpening
from app.simulation.domain import SimulationContext

logger = logging.getLogger("agent_company_simulator")

CANDIDATE_NAMES = [
    "Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Hank",
    "Ivy", "Jack", "Kate", "Liam", "Maya", "Noah", "Olivia", "Pavel",
    "Quinn", "Rita", "Sam", "Tina", "Umar", "Vera", "Will", "Xena",
    "Yuri", "Zara", "Adam", "Bella", "Carl", "Diana",
]

CANDIDATE_SKILLS = {
    "ENGINEER": ["python", "javascript", "sql", "docker", "react", "node", "go", "rust"],
    "SENIOR_ENGINEER": ["architecture", "python", "javascript", "sql", "docker", "react", "node", "go", "rust", "leadership"],
    "DESIGNER": ["figma", "ui", "ux", "css", "research"],
    "PRODUCT_MANAGER": ["strategy", "analytics", "roadmap", "communication", "agile"],
    "SALES": ["negotiation", "crm", "prospecting", "communication"],
    "MARKETING": ["seo", "content", "analytics", "social", "campaigns"],
    "CUSTOMER_SUCCESS": ["support", "communication", "retention", "onboarding"],
    "DATA_ANALYST": ["sql", "python", "visualization", "statistics", "ml"],
    "FINANCE": ["accounting", "budgeting", "forecasting", "compliance"],
    "OPERATIONS": ["logistics", "process", "scaling", "automation"],
}


def generate_candidates(
    ctx: SimulationContext,
    job_opening: JobOpening,
    count: int = 3,
) -> list[Candidate]:
    """Generate deterministic candidates for a job opening.

    Uses company seed + simulation day + candidate index to produce
    reproducible candidate attributes.
    """
    rng = random.Random(ctx.company.seed * 10_000 + ctx.day + job_opening.id)
    candidates: list[Candidate] = []
    skills_pool = CANDIDATE_SKILLS.get(job_opening.role.upper(), ["general"])

    for i in range(count):
        name = CANDIDATE_NAMES[rng.randint(0, len(CANDIDATE_NAMES) - 1)]
        experience = round(rng.uniform(0.5, 8.0), 1)
        productivity_potential = round(rng.uniform(0.3, 1.0), 2)
        culture_fit = round(rng.uniform(0.3, 1.0), 2)
        reliability = round(rng.uniform(0.4, 1.0), 2)
        salary_expectation = round(
            job_opening.salary_min + rng.random() * (job_opening.salary_max - job_opening.salary_min), 2
        )
        num_skills = rng.randint(1, min(4, len(skills_pool)))
        candidate_skills = rng.sample(skills_pool, num_skills)

        candidate = Candidate(
            company_id=ctx.company.id,
            job_opening_id=job_opening.id,
            name=name,
            role=job_opening.role,
            skills=candidate_skills,
            experience=experience,
            salary_expectation=salary_expectation,
            productivity_potential=productivity_potential,
            culture_fit=culture_fit,
            reliability=reliability,
            hiring_score=0.0,
            status="CANDIDATE",
        )
        ctx.db.add(candidate)
        ctx.db.flush()
        candidates.append(candidate)

    logger.info(
        "Generated %d candidates for job opening %d on day %d",
        len(candidates),
        job_opening.id,
        ctx.day,
    )
    return candidates


def evaluate_candidate(
    ctx: SimulationContext,
    candidate: Candidate,
    evaluator_agent_id: int,
) -> Candidate:
    """Evaluate a candidate and compute a hiring score.

    Score is deterministic based on candidate attributes and job requirements.
    """
    job = ctx.db.get(JobOpening, candidate.job_opening_id)
    if job is None:
        return candidate

    score = 0.0
    # Skills match (simple overlap).
    required = set(job.required_skills or [])
    have = set(candidate.skills or [])
    if required:
        skill_match = len(required & have) / len(required)
    else:
        skill_match = 0.5
    score += skill_match * 0.3

    # Experience (bounded 0..1).
    score += min(1.0, candidate.experience / 5.0) * 0.2

    # Salary fit (lower is better, within range).
    if job.salary_max > job.salary_min:
        salary_fit = 1.0 - (candidate.salary_expectation - job.salary_min) / (job.salary_max - job.salary_min)
        salary_fit = max(0.0, min(1.0, salary_fit))
    else:
        salary_fit = 0.5
    score += salary_fit * 0.2

    # Productivity potential.
    score += candidate.productivity_potential * 0.15

    # Culture fit.
    score += candidate.culture_fit * 0.1

    # Reliability.
    score += candidate.reliability * 0.05

    candidate.hiring_score = round(max(0.0, min(1.0, score)), 2)
    candidate.evaluated_by = evaluator_agent_id
    candidate.evaluated_day = ctx.day
    candidate.status = "INTERVIEWING"
    ctx.db.flush()

    logger.info(
        "Evaluated candidate %s for %s: score=%.2f",
        candidate.name,
        job.role,
        candidate.hiring_score,
    )
    return candidate


def candidates_for_opening(ctx: SimulationContext, job_opening_id: int) -> list[Candidate]:
    """Return candidates for a job opening."""
    return list(
        ctx.db.execute(
            select(Candidate).where(Candidate.job_opening_id == job_opening_id)
        )
        .scalars()
        .all()
    )
