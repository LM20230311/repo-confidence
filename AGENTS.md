# AGENTS.md

## Mission

Repo Confidence helps developers use AI to understand unfamiliar repositories, make safe changes, and grow into accountable maintainers.

The project optimizes for durable human confidence, not maximum documentation volume or autonomous code generation.

## Repository Structure

- `README.md`: public project story, positioning, and quick start
- `docs/methodology.md`: detailed confidence-building methodology
- `docs/roadmap.md`: phased project direction
- `skills/repository-onboarding-coach/`: first Codex Skill implementation
- `tests/`: deterministic tests for bundled scripts

## Non-Negotiable Principles

- Separate `Verified`, `Inferred`, and `Unknown` claims.
- Require evidence for high-impact repository conclusions.
- Preserve human decision-making at security, billing, migration, compatibility, and destructive-change boundaries.
- Prefer progressive disclosure over exhaustive generated documentation.
- Treat known unknowns as a first-class artifact.
- Keep analysis local-first and never expose repository secrets.
- Measure success by maintenance behavior, not generated page count.
- Keep normal delivery efficient; pause for teach-back only when learning mode is explicit.

## Skill Changes

- Keep `SKILL.md` concise and procedural.
- Put detailed schemas and rubrics in `references/`.
- Put copyable output templates in `assets/`.
- Use `scripts/` only for deterministic repeated work.
- Do not add README or changelog files inside a Skill directory.
- Regenerate `agents/openai.yaml` when Skill behavior or positioning changes.
- Validate the Skill after changes:

```bash
python3 /path/to/skill-creator/scripts/quick_validate.py \
  skills/repository-onboarding-coach
```

## Script Changes

- Prefer the Python standard library.
- Keep repository inspection read-only by default.
- Do not read or print file contents unless the command explicitly requires it.
- Do not print Git remote credentials, environment secrets, or configuration values.
- Support non-Git directories when practical.
- Add or update deterministic tests.

Run tests with:

```bash
python3 -m unittest discover -s tests -v
```

## Documentation Changes

- Keep README focused on the problem, value, workflow, and adoption path.
- Keep detailed method explanations in `docs/`.
- Update claims and roadmap checkboxes only when the corresponding behavior exists.
- Prefer stable symbol names and Git commits over fragile line-only references.
- Avoid promising complete understanding or guaranteed correctness.

## Contribution Standard

Every meaningful change should explain:

- which developer-confidence problem it addresses;
- how the behavior is verified;
- what uncertainty remains;
- whether the Skill, templates, tests, or methodology must be updated together.
