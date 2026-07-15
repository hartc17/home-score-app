from __future__ import annotations

from app.schemas import Rubric, RubricGates

# Mirror of apps/web/src/rubric/merge.ts. The quiz-derived parts of a rubric must
# never be overwritten by the stated gates, and neither side clobbers the other.


def has_quiz_signal(rubric: Rubric) -> bool:
    return len(rubric.item_weights) > 0


def merge_gates(rubric: Rubric, gates: RubricGates) -> Rubric:
    return rubric.model_copy(update={"gates": gates})


def compose_forward(anonymous: Rubric, account: Rubric) -> Rubric:
    quiz_source = anonymous if has_quiz_signal(anonymous) else account
    return Rubric(
        version=quiz_source.version,
        gates=account.gates or anonymous.gates,
        category_weights=quiz_source.category_weights,
        item_weights=quiz_source.item_weights,
        directions=quiz_source.directions,
        archetype=quiz_source.archetype,
        confidence=quiz_source.confidence,
    )
