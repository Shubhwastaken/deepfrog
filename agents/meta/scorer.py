"""Scoring helpers for ranking candidate worlds."""

from __future__ import annotations

from typing import Iterable

from agents.schemas import EvaluationBundle, MetaScoringConfig


def calculate_scores(
    evaluations: Iterable[EvaluationBundle],
    scoring_config: MetaScoringConfig,
) -> dict[str, float]:
    """Compute composite scores for every evaluation bundle."""

    evaluation_list = list(evaluations)
    costs = [bundle.duty_result.total_landed_cost_usd for bundle in evaluation_list]
    min_cost = min(costs)
    max_cost = max(costs)

    results: dict[str, float] = {}
    for bundle in evaluation_list:
        compliance_score = 1.0 if bundle.compliance_result.is_compliant else 0.0
        inverse_duty_score = _inverse_cost_score(
            bundle.duty_result.total_landed_cost_usd,
            min_cost=min_cost,
            max_cost=max_cost,
        )
        inverse_risk_score = max(0.0, min(1.0, 1.0 - bundle.debate_result.risk_score))
        composite = (
            scoring_config.compliance_weight * compliance_score
            + scoring_config.cost_weight * inverse_duty_score
            + scoring_config.risk_weight * inverse_risk_score
        )
        results[str(bundle.world.world_id)] = round(composite, 6)
    return results


def rank_world_ids(score_breakdown: dict[str, float]) -> list[str]:
    """Return world IDs ranked by score descending."""

    return [
        world_id
        for world_id, _ in sorted(
            score_breakdown.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    ]


def _inverse_cost_score(cost: float, *, min_cost: float, max_cost: float) -> float:
    """Normalize landed cost so lower cost maps to a higher score."""

    if max_cost == min_cost:
        return 1.0
    return max(0.0, min(1.0, 1.0 - ((cost - min_cost) / (max_cost - min_cost))))
