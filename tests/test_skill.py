"""
Validation tests for the Agentic Company Simulator skill.

These tests validate the skill itself — not a simulation engine (there is none).
They check file integrity, content coverage, and cross-references.

Run: python tests/test_skill.py
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REQUIRED_FILES = [
    "SKILL.md",
    "README.md",
    "skills/company-simulation/SKILL.md",
    "skills/company-simulation/core/simulation.md",
    "skills/company-simulation/core/state.md",
    "skills/company-simulation/core/decision-making.md",
    "skills/company-simulation/core/events.md",
    "skills/company-simulation/core/progression.md",
    "skills/company-simulation/core/outcomes.md",
    "skills/company-simulation/roles/founder.md",
    "skills/company-simulation/roles/ceo.md",
    "skills/company-simulation/roles/cto.md",
    "skills/company-simulation/roles/cmo.md",
    "skills/company-simulation/roles/engineer.md",
    "skills/company-simulation/roles/salesperson.md",
    "skills/company-simulation/roles/employee.md",
    "skills/company-simulation/systems/finance.md",
    "skills/company-simulation/systems/product.md",
    "skills/company-simulation/systems/engineering.md",
    "skills/company-simulation/systems/marketing.md",
    "skills/company-simulation/systems/sales.md",
    "skills/company-simulation/systems/workforce.md",
    "skills/company-simulation/systems/market.md",
    "skills/company-simulation/systems/competition.md",
    "skills/company-simulation/systems/fundraising.md",
    "skills/company-simulation/schemas/company-state.md",
    "skills/company-simulation/schemas/agent-state.md",
    "skills/company-simulation/schemas/decision.md",
    "skills/company-simulation/schemas/event.md",
    "skills/company-simulation/examples/startup.md",
    "skills/company-simulation/examples/saas.md",
    "skills/company-simulation/examples/consumer-company.md",
    "examples/prompts/nova-flow-ai.md",
    "examples/simulations/nova-flow-ai.md",
    "docs/usage.md",
    "docs/architecture.md",
    "docs/skill-development.md",
]

REQUIRED_ROOT_SECTIONS = [
    "Quick Start",
    "Core Simulation Loop",
    "State Model",
    "Agent System",
    "Decision Framework",
    "Systems",
    "Events",
    "Interaction Modes",
    "Output Format",
    "Persistence",
    "Outcomes",
    "Realism Rules",
    "Causal Reasoning",
    "Uncertainty",
]

REQUIRED_SYSTEMS = [
    "Finance",
    "Product",
    "Engineering",
    "Marketing",
    "Sales",
    "Workforce",
    "Market",
    "Competition",
    "Fundraising",
]

REQUIRED_ROLES = [
    "Founder",
    "CEO",
    "CTO",
    "CMO",
    "Engineer",
    "Salesperson",
    "Employee",
]


def read_file(rel_path):
    path = os.path.join(ROOT, rel_path)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return f.read()


def test_required_files_exist():
    """All required skill files must exist."""
    missing = []
    for f in REQUIRED_FILES:
        if not os.path.exists(os.path.join(ROOT, f)):
            missing.append(f)
    assert not missing, f"Missing files: {missing}"


def test_root_skill_has_frontmatter():
    """SKILL.md must have YAML frontmatter."""
    content = read_file("SKILL.md")
    assert content is not None
    assert content.startswith("---"), "SKILL.md must start with YAML frontmatter"
    assert "name:" in content.split("---")[1], "Frontmatter must have 'name'"


def test_root_skill_has_required_sections():
    """Root SKILL.md must contain all required sections."""
    content = read_file("SKILL.md")
    for section in REQUIRED_ROOT_SECTIONS:
        assert section in content, f"SKILL.md missing section: {section}"


def test_root_skill_covers_all_systems():
    """Root SKILL.md Section 5 must cover all 9 systems."""
    content = read_file("SKILL.md")
    for system in REQUIRED_SYSTEMS:
        assert system in content, f"SKILL.md missing system: {system}"


def test_root_skill_covers_all_roles():
    """Root SKILL.md must cover all 7 agent roles."""
    content = read_file("SKILL.md")
    for role in REQUIRED_ROLES:
        assert role in content, f"SKILL.md missing role: {role}"


def test_simulation_loop_defined():
    """SKILL.md must define the simulation loop steps."""
    content = read_file("SKILL.md")
    assert "simulation loop" in content.lower() or "Core Simulation Loop" in content
    # Check that key steps are mentioned
    for step in ["Advance time", "external events", "individual agent decisions", "finance", "Outcome"]:
        assert step in content, f"Simulation loop missing step: {step}"


def test_state_schema_complete():
    """Company state schema must include all required domains."""
    content = read_file("skills/company-simulation/schemas/company-state.md")
    for domain in ["company", "finance", "product", "market", "workforce", "goals", "risks", "events", "history", "status"]:
        assert domain in content, f"State schema missing domain: {domain}"


def test_state_invariants_defined():
    """State schema must define invariants."""
    content = read_file("skills/company-simulation/schemas/company-state.md")
    assert "Invariant" in content, "State schema must define invariants"


def test_finance_system_has_formulas():
    """Finance system must define burn, runway, health tiers."""
    content = read_file("skills/company-simulation/systems/finance.md")
    assert "burn" in content.lower()
    assert "runway" in content.lower()
    assert "Health" in content or "health" in content.lower()


def test_product_system_has_stages():
    """Product system must define stages and progression."""
    content = read_file("skills/company-simulation/systems/product.md")
    assert "idea" in content
    assert "prototype" in content
    assert "mvp" in content
    assert "launch" in content
    assert "progress" in content.lower()


def test_market_system_has_variables():
    """Market system must define market variables and evolution."""
    content = read_file("skills/company-simulation/systems/market.md")
    assert "demand" in content.lower()
    assert "competition" in content.lower()
    assert "sentiment" in content.lower()
    assert "segment" in content.lower()


def test_competition_system_defined():
    """Competition system must define competitor profiles and actions."""
    content = read_file("skills/company-simulation/systems/competition.md")
    assert "competitor" in content.lower()
    assert "strategy" in content.lower()
    assert "market_share" in content.lower()


def test_workforce_system_defined():
    """Workforce system must define hiring and morale."""
    content = read_file("skills/company-simulation/systems/workforce.md")
    assert "hiring" in content.lower() or "Hiring" in content
    assert "morale" in content.lower()
    assert "capacity" in content.lower()


def test_fundraising_system_defined():
    """Fundraising system must define pipeline and valuation."""
    content = read_file("skills/company-simulation/systems/fundraising.md")
    assert "pipeline" in content.lower()
    assert "valuation" in content.lower()
    assert "investor" in content.lower()


def test_decision_framework_defined():
    """Decision framework must define the observe-evaluate-choose process."""
    content = read_file("skills/company-simulation/core/decision-making.md")
    for step in ["Observe", "Prioritize", "Evaluate", "Choose", "Explain"]:
        assert step in content, f"Decision framework missing: {step}"


def test_role_authority_defined():
    """Each role file must define authority and decision scope."""
    for role_file in ["founder", "ceo", "cto", "cmo", "engineer", "salesperson", "employee"]:
        content = read_file(f"skills/company-simulation/roles/{role_file}.md")
        assert content is not None, f"Missing role file: {role_file}.md"
        assert "Authority" in content or "authority" in content.lower(), f"{role_file} missing authority"


def test_events_defined():
    """Events system must define types and probabilities."""
    content = read_file("skills/company-simulation/core/events.md")
    assert "event" in content.lower()
    assert "probabilit" in content.lower() or "probability" in content.lower()


def test_outcomes_defined():
    """Outcomes must define success and failure conditions."""
    content = read_file("skills/company-simulation/core/outcomes.md")
    assert "uccess" in content, "Outcomes must define success conditions"
    assert "ailure" in content, "Outcomes must define failure conditions"


def test_interaction_modes_defined():
    """SKILL.md must define all 5 interaction modes."""
    content = read_file("SKILL.md")
    for mode in ["Autonomous", "Founder", "Advisory", "Scenario", "Comparison"]:
        assert mode in content, f"SKILL.md missing interaction mode: {mode}"


def test_uncertainty_handling_defined():
    """SKILL.md must address uncertainty."""
    content = read_file("SKILL.md")
    assert "ncertain" in content or "Uncertainty" in content, "SKILL.md must address uncertainty"
    assert "confidence" in content.lower(), "SKILL.md must mention confidence levels"


def test_causal_reasoning_defined():
    """SKILL.md must define causal reasoning."""
    content = read_file("SKILL.md")
    assert "ausal" in content, "SKILL.md must address causal reasoning"


def test_realism_rules_defined():
    """SKILL.md must define realism rules."""
    content = read_file("SKILL.md")
    assert "ealism" in content or "Realism" in content, "SKILL.md must define realism rules"


def test_example_simulation_exists():
    """An example simulation must exist showing state changes."""
    content = read_file("examples/simulations/nova-flow-ai.md")
    assert content is not None, "Example simulation missing"
    assert "DAY" in content.upper(), "Example must show day-by-day simulation"
    assert "Decision" in content, "Example must show agent decisions"
    assert "Consequence" in content, "Example must show consequences"
    assert "Cash" in content, "Example must show financials"
    assert "Competitor" in content, "Example must show competitor activity"


def test_example_shows_failure_risk():
    """Example must demonstrate that the company can face failure risk."""
    content = read_file("examples/simulations/nova-flow-ai.md")
    assert "isk" in content, "Example must show risks"


def test_state_compression_defined():
    """SKILL.md must define state compression for long simulations."""
    content = read_file("SKILL.md")
    assert "ompress" in content.lower() or "compress" in content.lower(), "SKILL.md must define state compression"


def test_no_obsolete_references():
    """SKILL.md must not reference obsolete infrastructure."""
    content = read_file("SKILL.md")
    for term in ["FastAPI", "PostgreSQL", "Django", "docker", "WebSocket", "REST API", "SQLAlchemy"]:
        assert term not in content, f"SKILL.md references obsolete tech: {term}"
    # "React" check uses word boundary to avoid matching "Reactions"
    if re.search(r'\bReact\b', content):
        assert False, "SKILL.md references obsolete tech: React"


def test_agents_vs_roles_distinguished():
    """Agent state schema must distinguish agents from roles."""
    content = read_file("skills/company-simulation/schemas/agent-state.md")
    assert content is not None
    assert "Agents vs Roles" in content
    assert "acting" in content.lower(), "Agent state must cover acting responsibilities"


def test_no_fictional_cto_cmo():
    """Example simulation must not feature fictional CTO/CMO people."""
    content = read_file("examples/simulations/nova-flow-ai.md")
    assert content is not None
    # Should reference acting CTO / acting CMO as responsibility labels, not people
    assert "Acting" in content or "acting" in content
    assert "acting cto" in content.lower()


def test_example_has_no_action_declarations():
    """Example simulation must show NO_ACTION declarations."""
    content = read_file("examples/simulations/nova-flow-ai.md")
    assert content is not None
    assert "NO_ACTION" in content, "Example must demonstrate NO_ACTION as a valid decision"


def test_example_has_agent_reactions():
    """Example simulation must show agents reacting to other agents' decisions."""
    content = read_file("examples/simulations/nova-flow-ai.md")
    assert content is not None
    assert "Reaction" in content, "Example must show agent reactions"


def test_example_has_conflict_resolution():
    """Example simulation must show conflict resolution."""
    content = read_file("examples/simulations/nova-flow-ai.md")
    assert content is not None
    assert "Conflict" in content, "Example must demonstrate conflict resolution"


def test_example_has_independent_decisions():
    """Example must show each agent making independent decisions."""
    content = read_file("examples/simulations/nova-flow-ai.md")
    assert content is not None
    assert "Casey" in content
    assert "Remy" in content
    assert "Avery" in content
    # Each agent should have decision context (Situation) and rationale
    assert content.count("Situation:") >= 3, "Each agent should assess their situation"
    assert content.count("Rationale:") >= 3, "Each agent should explain their rationale"


def test_example_shows_consequence_chains():
    """Example must show consequence chains across days."""
    content = read_file("examples/simulations/nova-flow-ai.md")
    assert content is not None
    assert "Consequence" in content, "Example must show consequences"
    assert "Multi-Agent Behaviors" in content, "Example must have a multi-agent behaviors summary"


def test_skill_md_multi_agent_coverage():
    """Root SKILL.md must cover multi-agent architecture concepts."""
    content = read_file("SKILL.md")
    assert content is not None
    assert "acting" in content.lower(), "SKILL.md must cover acting responsibilities"
    assert "NO_ACTION" in content, "SKILL.md must cover NO_ACTION"
    assert "Agent" in content, "SKILL.md must cover multi-agent concept"


def test_example_prompts_exist():
    """Example prompts must exist for user reference."""
    content = read_file("examples/prompts/nova-flow-ai.md")
    assert content is not None, "Example prompt missing"
    assert "Create a startup" in content, "Prompt must include company creation"


def test_documentation_exists():
    """Documentation files must exist."""
    for doc in ["docs/usage.md", "docs/architecture.md", "docs/skill-development.md"]:
        content = read_file(doc)
        assert content is not None, f"Missing doc: {doc}"
        assert len(content) > 100, f"Doc too short: {doc}"


def test_no_code_files_in_skill():
    """The skill should not require Python backends or React frontends."""
    # Check that no .py files exist in skills/
    for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, "skills")):
        for f in filenames:
            assert not f.endswith(".py"), f"Unexpected Python file in skills: {f}"


if __name__ == "__main__":
    tests = [
        (n, f) for n, f in globals().items()
        if n.startswith("test_") and callable(f)
    ]
    passed = 0
    failed = 0
    for name, func in sorted(tests):
        try:
            func()
            passed += 1
            print(f"  PASS  {name}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL  {name}: {e}")
        except Exception as e:
            failed += 1
            print(f"  ERROR {name}: {e}")
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
