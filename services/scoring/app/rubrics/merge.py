from __future__ import annotations

from app.schemas import Rubric, RubricGates

# Mirror of apps/web/src/rubric/merge.ts. Stated gates must never overwrite the
# quiz-derived parts of a rubric.


def merge_gates(rubric: Rubric, gates: RubricGates) -> Rubric:
    return rubric.model_copy(update={"gates": gates})
