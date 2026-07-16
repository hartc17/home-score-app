from __future__ import annotations

from app.schemas import Rubric, RubricGates

# Mirror of apps/web/src/rubric/merge.ts. Stated gates must never overwrite the
# quiz-derived parts of a rubric.


def merge_gates(rubric: Rubric, gates: RubricGates) -> Rubric:
    return rubric.model_copy(update={"gates": gates})


def compose_forward(account: Rubric | None, incoming: Rubric) -> Rubric:
    # Claiming an anonymous rubric onto an account: the fresh quiz taste
    # (directions, weights, archetype) is preserved, and the account's stated
    # gates carry forward only when the incoming rubric has none. Neither side
    # is clobbered.
    if account is None:
        return incoming
    gates = incoming.gates or account.gates
    return incoming.model_copy(update={"gates": gates})
