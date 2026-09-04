# Skill Development Guide

## Philosophy

This skill is a **portable artifact** that encodes business simulation logic as structured instructions for LLMs. It replaces thousands of lines of Python code with clear, maintainable markdown.

## Structure

- **`SKILL.md`** (root) — The product. Self-contained, complete, downloadable.
- **`skills/company-simulation/`** — Modular breakdown for maintenance. Edit here, sync to root.
- **`examples/`** — User-facing examples (prompts and worked simulations).
- **`docs/`** — User and developer documentation.
- **`tests/`** — Validation that the skill is complete and self-consistent.

## Editing the Skill

### Adding a New Role

1. Create `skills/company-simulation/roles/<role>.md`
2. Define: authority level, responsibilities, decision scope, decision process.
3. Reference the role in `schemas/agent-state.md`.
4. Update the root `SKILL.md` Section 3 (Agent System) with the new role.
5. Run `python tests/test_skill.py` to validate.

### Adding a New System

1. Create `skills/company-simulation/systems/<system>.md`
2. Define: variables, formulas, rules, constraints.
3. Reference the system in `core/simulation.md` (simulation loop step).
4. Update the root `SKILL.md` Section 5 (Systems).
5. Update `schemas/company-state.md` with new state fields.
6. Run tests.

### Modifying State Schema

1. Edit `schemas/company-state.md`.
2. Update the root `SKILL.md` Section 2 (State Model).
3. Ensure all invariants still hold.
4. Run tests.

## Testing

```bash
python tests/test_skill.py
```

Tests validate:
- File existence and reference integrity
- Required sections present in each file
- No broken cross-references
- State schema completeness
- Role coverage
- System coverage

## Versioning

- Update `version` in YAML frontmatter of `SKILL.md`.
- Breaking changes → major version bump.
- New features → minor version bump.
- Fixes → patch version bump.
