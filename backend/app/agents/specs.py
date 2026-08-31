"""Default specifications for the initial company organization.

Hierarchy seeded on company creation:

    CEO
    ├── CTO
    │    └── Engineer
    └── CMO
"""

from app.enums import AgentRole

DEFAULT_ORG: list[dict] = [
    {
        "name": "Avery Chen",
        "role": AgentRole.CEO,
        "manager_role": None,
        "authority": 10,
        "salary": 1000.0,
        "budget": 50000.0,
        "personality": {
            "leadership": 0.9,
            "risk_tolerance": 0.5,
            "decisiveness": 0.8,
        },
        "skills": ["strategy", "leadership", "communication", "finance"],
    },
    {
        "name": "Blair Okafor",
        "role": AgentRole.CTO,
        "manager_role": AgentRole.CEO,
        "authority": 8,
        "salary": 800.0,
        "budget": 30000.0,
        "personality": {
            "technical_depth": 0.95,
            "curiosity": 0.85,
            "pragmatism": 0.7,
        },
        "skills": ["architecture", "engineering", "research", "infrastructure"],
    },
    {
        "name": "Casey Nguyen",
        "role": AgentRole.ENGINEER,
        "manager_role": AgentRole.CTO,
        "authority": 5,
        "salary": 600.0,
        "budget": 10000.0,
        "personality": {
            "diligence": 0.85,
            "creativity": 0.6,
            "teamwork": 0.8,
        },
        "skills": ["software-development", "testing", "devops"],
    },
    {
        "name": "Dana Reyes",
        "role": AgentRole.CMO,
        "manager_role": AgentRole.CEO,
        "authority": 7,
        "salary": 700.0,
        "budget": 20000.0,
        "personality": {
            "creativity": 0.9,
            "empathy": 0.85,
            "persuasiveness": 0.8,
        },
        "skills": ["marketing", "growth", "branding", "analytics"],
    },
]
