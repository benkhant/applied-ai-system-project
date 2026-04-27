# Model Card: PawPal+ AI-Assisted Scheduler

## 1. Model/System Overview

**System name:** PawPal+ AI-Assisted Scheduler  
**Project type:** Applied AI system for multi-pet care planning  
**Primary files:**

- [pawpal_system.py](pawpal_system.py)
- [app.py](app.py)
- [reliability_eval.py](reliability_eval.py)
- [tests/test_pawpal.py](tests/test_pawpal.py)

PawPal+ combines deterministic scheduling with a retrieval-augmented scoring layer. The system retrieves care guidance snippets from an internal knowledge base, adjusts task urgency scores, validates outputs with guardrails, and falls back to rule-based scheduling when validation fails.

## 2. Intended Use

### Intended users

- Pet owners who want structured daily planning support.
- Instructors/reviewers evaluating applied AI system design.

### Intended use cases

- Prioritize daily pet care tasks.
- Surface scheduling conflicts.
- Provide transparent rationale for ranking decisions.

### Out-of-scope use

- Veterinary diagnosis or treatment decisions.
- Emergency care triage.
- Replacement for professional medical advice.

## 3. Base Project (Modules 1-3)

This project extends the earlier **PawPal Starter Scheduler** prototype from Modules 1-3.

The original system provided core OOP planning: pets, tasks, owner constraints, priority ranking, time sorting, and simple conflict checks. The final system adds retrieval-augmented AI scoring, guardrail validation with fallback, structured logging, and reliability evaluation.

## 4. System Architecture and Data Flow

Architecture diagram:

- [assets/diagrams/system_architecture.mmd](assets/diagrams/system_architecture.mmd)

Flow summary:

1. User enters owner/pet/task data in Streamlit.
2. Planner runs in rule-based mode or AI-assisted mode.
3. AI-assisted mode retrieves relevant care guidance and boosts urgency score.
4. Guardrails validate output quality and completeness.
5. If guardrails fail, system falls back to safe rule-based ranking.
6. Output and rationale are shown in UI and logged for auditability.

## 5. AI Collaboration Summary

### Helpful suggestion from AI

A helpful AI suggestion was to integrate retrieval, guardrails, and fallback directly into the scheduler path rather than placing AI logic in a standalone script. This made AI behavior part of production app logic and improved rubric alignment.

### Flawed or incorrect suggestion from AI

An early AI-suggested weight setup under-prioritized medication tasks relative to medium-priority play tasks. This was corrected by tuning retrieval urgency boosts and adding regression tests to enforce expected behavior.

## 6. Reliability and Testing Results

### Automated tests

- Current status: **14/14 tests passed**.
- Coverage includes core scheduling behavior, AI prioritization, and guardrail fallback.

### Reliability evaluation

From [reliability_eval.py](reliability_eval.py):

- Trials: 20
- Unique plan orderings: 1
- Consistency rate: 100.00%
- Guardrail failure rate: 0.00%
- Fallback usage rate: 0.00%

### Logging and error handling

- Structured planner events and guardrail issues are recorded in [logs/pawpal.log](logs/pawpal.log).
- Validation failures trigger fallback to rule-based planning.

### Human evaluation

- Schedule outputs and AI rationale are reviewed in the Streamlit UI.
- README sample interactions are used to verify expected behavior manually.

## 7. Limitations and Biases

- Retrieval knowledge base is small and hand-authored, which can bias behavior toward included keywords/patterns.
- Species handling is simplified and may miss nuanced medical or breed-specific context.
- Conflict detection identifies exact same-time collisions but does not yet compute duration-overlap conflicts.
- Reliability metrics are strong on tested scenarios but do not represent all real-world edge cases.

## 8. Misuse Risks and Mitigations

### Potential misuse

Users may over-trust the system as a clinical authority for pet health decisions.

### Mitigations

- Guardrails prevent malformed outputs from being accepted.
- Fallback path ensures safe deterministic behavior if AI-assisted validation fails.
- Transparent rationale and logs make outputs inspectable.
- Documentation clarifies this is a planning assistant, not a diagnostic tool.

## 9. Ethical Reflection

This project reinforced that responsible AI is about system behavior under failure, not just ideal outputs. The most important practices were keeping AI decisions observable (rationale + logs), testable (unit + reliability checks), and reversible (guardrail fallback). The main future improvement area is broader scenario testing to reduce blind spots.

## 10. Reproducibility

Run steps:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
python -m pytest -q
python reliability_eval.py
```

Supporting documentation:

- [README.md](README.md)
- [reflection.md](reflection.md)
