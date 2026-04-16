"""Output shaping agent."""

from __future__ import annotations

from agents.base.base_agent import BaseAgent
from agents.output.formatter import build_plain_language_summary
from agents.schemas import (
    AlternativeSummary,
    ComparisonTableRow,
    OutputInput,
    OutputResult,
    WinnerDetails,
)


class OutputAgent(BaseAgent[OutputInput, OutputResult]):
    """Flatten evaluated world data into an API-ready response object."""

    agent_name = "output"

    async def run(self, input: OutputInput) -> OutputResult:
        """Build the worker-facing final response payload."""

        validated_input = OutputInput.model_validate(input)
        scores = validated_input.meta_result.score_breakdown
        score_lookup = {world_id: float(score) for world_id, score in scores.items()}

        sorted_evaluations = sorted(
            validated_input.evaluations,
            key=lambda bundle: score_lookup.get(str(bundle.world.world_id), 0.0),
            reverse=True,
        )

        comparison_table = [
            ComparisonTableRow(
                world_id=bundle.world.world_id,
                label=bundle.world.label,
                hs_code=bundle.world.hs_code,
                confidence_score=bundle.world.confidence_score,
                is_compliant=bundle.compliance_result.is_compliant,
                duty_rate_percent=bundle.duty_result.duty_rate_percent,
                estimated_duty_usd=bundle.duty_result.estimated_duty_usd,
                total_landed_cost_usd=bundle.duty_result.total_landed_cost_usd,
                risk_score=(bundle.critic_result or bundle.debate_result).risk_score,
                recommendation=(bundle.critic_result or bundle.debate_result).recommendation,
                composite_score=score_lookup.get(str(bundle.world.world_id), 0.0),
                valuation_verdict=bundle.valuation_result.verdict if bundle.valuation_result else None,
                valuation_severity=bundle.valuation_result.severity if bundle.valuation_result else None,
            )
            for bundle in sorted_evaluations
        ]

        winning_bundle = next(
            bundle
            for bundle in sorted_evaluations
            if bundle.world.world_id == validated_input.meta_result.winning_world_id
        )
        winner_details = WinnerDetails(
            world_id=winning_bundle.world.world_id,
            label=winning_bundle.world.label,
            hs_code=winning_bundle.world.hs_code,
            product_description=winning_bundle.world.extraction_data.product_description,
            destination_country=winning_bundle.world.extraction_data.destination_country,
            is_compliant=winning_bundle.compliance_result.is_compliant,
            duty_rate_percent=winning_bundle.duty_result.duty_rate_percent,
            estimated_duty_usd=winning_bundle.duty_result.estimated_duty_usd,
            total_landed_cost_usd=winning_bundle.duty_result.total_landed_cost_usd,
            risk_score=(winning_bundle.critic_result or winning_bundle.debate_result).risk_score,
            recommendation=(winning_bundle.critic_result or winning_bundle.debate_result).recommendation,
            reasoning=validated_input.meta_result.reasoning,
            confidence_score=winning_bundle.world.confidence_score,
            strategy_type=winning_bundle.world.strategy_type,
            assumptions=winning_bundle.world.assumptions,
            required_documents=winning_bundle.world.required_documents,
            risk_flags=winning_bundle.world.risk_flags,
            generation_reasoning=winning_bundle.world.generation_reasoning,
            **self._build_evidence_fields(winning_bundle),
        )

        alternatives = [
            AlternativeSummary(
                world_id=bundle.world.world_id,
                label=bundle.world.label,
                hs_code=bundle.world.hs_code,
                confidence_score=bundle.world.confidence_score,
                is_compliant=bundle.compliance_result.is_compliant,
                duty_rate_percent=bundle.duty_result.duty_rate_percent,
                estimated_duty_usd=bundle.duty_result.estimated_duty_usd,
                total_landed_cost_usd=bundle.duty_result.total_landed_cost_usd,
                risk_score=(bundle.critic_result or bundle.debate_result).risk_score,
                composite_score=score_lookup.get(str(bundle.world.world_id), 0.0),
                recommendation=(bundle.critic_result or bundle.debate_result).recommendation,
                strategy_type=bundle.world.strategy_type,
                assumptions=bundle.world.assumptions,
                required_documents=bundle.world.required_documents,
                risk_flags=bundle.world.risk_flags,
                generation_reasoning=bundle.world.generation_reasoning,
                **self._build_evidence_fields(bundle),
            )
            for bundle in sorted_evaluations
            if bundle.world.world_id != validated_input.meta_result.winning_world_id
        ]

        return OutputResult(
            winning_world_id=validated_input.meta_result.winning_world_id,
            final_hs_code=validated_input.meta_result.final_hs_code,
            winner_details=winner_details,
            alternatives=alternatives,
            comparison_table=comparison_table,
            score_breakdown=score_lookup,
            meta_reasoning=validated_input.meta_result.reasoning,
            plain_language_summary=build_plain_language_summary(winner_details, comparison_table),
        )

    def _build_evidence_fields(self, bundle) -> dict:
        """Flatten evaluation details used by the frontend inspector views."""

        critic_result = bundle.critic_result or bundle.debate_result
        valuation_result = bundle.valuation_result
        return {
            "compliance_violations": bundle.compliance_result.violations,
            "compliance_warnings": bundle.compliance_result.warnings,
            "applicable_rules": bundle.compliance_result.applicable_rules,
            "duty_calculation_breakdown": bundle.duty_result.calculation_breakdown,
            "valuation_verdict": valuation_result.verdict if valuation_result else None,
            "valuation_severity": valuation_result.severity if valuation_result else None,
            "valuation_explanation": valuation_result.explanation if valuation_result else None,
            "valuation_evidence": valuation_result.evidence if valuation_result else [],
            "critic_critiques": critic_result.critiques,
            "critic_strengths": critic_result.strengths,
            "critic_citations": critic_result.citations,
        }
