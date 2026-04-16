"""Debate agent for adversarial world review."""

from __future__ import annotations

from agents.base.base_agent import BaseAgent
from agents.debate.prompts import build_prompt
from agents.schemas import CriticCitation, DebateInput, DebateResult


class DebateAgent(BaseAgent[DebateInput, DebateResult]):
    """Stress-test a world by asking what could be wrong with it."""

    agent_name = "debate"

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("client", self._noop_client)
        kwargs.setdefault("model", "deterministic-critic")
        super().__init__(*args, **kwargs)

    async def _noop_client(self, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("No LLM client configured for debate/critic fallback mode.")

    async def run(self, input: DebateInput) -> DebateResult:
        """Return a risk-weighted critique of the proposed world."""

        validated_input = DebateInput.model_validate(input)
        if self.model and not str(self.model).startswith("deterministic") and self.client is not None:
            payload = validated_input.model_dump(mode="json")
            prompt = build_prompt(payload)
            try:
                result = await self.call_llm(prompt, DebateResult)
            except Exception:  # noqa: BLE001
                return self._deterministic_result(validated_input)

            normalized_payload = result.model_dump(mode="json")
            normalized_payload["world_id"] = validated_input.world.world_id
            normalized_payload.setdefault("fallback_used", False)
            return DebateResult.model_validate(normalized_payload)

        return self._deterministic_result(validated_input)

    def _deterministic_result(self, input_data: DebateInput) -> DebateResult:
        world = input_data.world
        compliance = input_data.compliance_result
        duty = input_data.duty_result
        valuation = input_data.valuation_result

        risk_score = 0.1
        critiques: list[str] = []
        strengths: list[str] = []

        if not compliance.is_compliant:
            risk_score += 0.35
            critiques.append("Compliance review found blocking violations that must be cleared before filing.")
        elif compliance.warnings:
            risk_score += 0.12
            critiques.append("Compliance review surfaced warnings that should be resolved before submission.")
        else:
            strengths.append("Compliance review did not identify blocking issues.")

        if valuation and valuation.verdict == "under_invoiced":
            severity_penalty = {"low": 0.08, "medium": 0.18, "high": 0.3}.get(valuation.severity, 0.08)
            risk_score += severity_penalty
            critiques.append(
                f"Valuation screen flagged the declaration as {valuation.verdict.replace('_', ' ')} "
                f"with {valuation.severity} severity."
            )
        elif valuation and valuation.verdict == "within_range":
            strengths.append("Valuation screen is within the deterministic benchmark range.")

        if duty.duty_rate_percent >= 15:
            risk_score += 0.08
            critiques.append("High duty exposure increases the cost of getting the classification wrong.")
        else:
            strengths.append("Duty exposure is comparatively manageable under the selected tariff path.")

        if world.risk_flags:
            risk_score += min(0.2, len(world.risk_flags) * 0.04)
            critiques.append(f"World generation flagged additional review items: {', '.join(world.risk_flags)}.")
        else:
            strengths.append("World generation did not add extra structural risk flags.")

        risk_score += max(0.0, 0.15 - (world.confidence_score * 0.15))
        risk_score = round(min(1.0, risk_score), 4)

        if not compliance.is_compliant or (valuation and valuation.verdict == "under_invoiced" and valuation.severity == "high"):
            recommendation = "reject"
        elif risk_score >= 0.45:
            recommendation = "review"
        else:
            recommendation = "accept"

        citations = self._deterministic_citations(input_data)
        if not critiques:
            critiques.append("No critical weaknesses were surfaced by the deterministic critic.")
        if not strengths:
            strengths.append("The current world still has enough structured support to proceed to analyst review.")

        return DebateResult(
            world_id=world.world_id,
            risk_score=risk_score,
            critiques=critiques,
            strengths=strengths,
            recommendation=recommendation,
            citations=citations,
            fallback_used=True,
        )

    def _deterministic_citations(self, input_data: DebateInput) -> list[CriticCitation]:
        world = input_data.world
        compliance = input_data.compliance_result
        duty = input_data.duty_result
        valuation = input_data.valuation_result

        citations: list[CriticCitation] = []
        if valuation is not None:
            citations.append(
                CriticCitation(
                    title="Valuation Screen",
                    detail=valuation.explanation,
                )
            )

        citations.append(
            CriticCitation(
                title="Compliance Rules",
                detail="; ".join(compliance.applicable_rules[:2]) or "No explicit compliance citations were generated.",
            )
        )
        citations.append(
            CriticCitation(
                title="Tariff Calculation",
                detail=duty.calculation_breakdown,
            )
        )

        if len(citations) < 3:
            citations.append(
                CriticCitation(
                    title="World Context",
                    detail=world.generation_reasoning or world.label,
                )
            )

        return citations[:3]
