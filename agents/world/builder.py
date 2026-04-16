"""Helpers for deterministic, scenario-aware world generation."""

from __future__ import annotations

from agents.schemas import ExtractionResult, HSCodeCandidate, World


class WorldBuilder:
    """Create customs worlds that carry strategy assumptions and support context."""

    def build(self, extraction_result: ExtractionResult, candidates: list[HSCodeCandidate]) -> list[World]:
        """Turn ranked HS candidates into richer scenario objects."""

        ordered_candidates = sorted(
            candidates,
            key=lambda candidate: candidate.confidence_score,
            reverse=True,
        )
        if not ordered_candidates:
            return []

        top_confidence = ordered_candidates[0].confidence_score
        worlds: list[World] = []
        for index, candidate in enumerate(ordered_candidates):
            strategy_type = self._strategy_type(
                rank=index,
                candidate_confidence=candidate.confidence_score,
                top_confidence=top_confidence,
            )
            risk_flags = self._build_risk_flags(
                extraction_result=extraction_result,
                candidate=candidate,
                rank=index,
            )
            assumptions = self._build_assumptions(
                extraction_result=extraction_result,
                candidate=candidate,
                rank=index,
                strategy_type=strategy_type,
            )
            required_documents = self._build_required_documents(
                extraction_result=extraction_result,
                candidate=candidate,
                strategy_type=strategy_type,
            )

            worlds.append(
                World(
                    hs_code=candidate.hs_code,
                    confidence_score=self._adjust_confidence(
                        candidate.confidence_score,
                        rank=index,
                        risk_flags=risk_flags,
                    ),
                    extraction_data=extraction_result,
                    label=self._label_for(index, strategy_type),
                    strategy_type=strategy_type,
                    assumptions=assumptions,
                    required_documents=required_documents,
                    risk_flags=risk_flags,
                    generation_reasoning=self._build_reasoning(
                        candidate=candidate,
                        strategy_type=strategy_type,
                        assumptions=assumptions,
                        risk_flags=risk_flags,
                    ),
                )
            )
        return worlds

    def _strategy_type(self, *, rank: int, candidate_confidence: float, top_confidence: float) -> str:
        """Assign a deterministic strategy label for each candidate rank."""

        if rank == 0 and candidate_confidence >= 0.8:
            return "baseline"
        if rank == 0:
            return "review_primary"
        if rank == 1 and (top_confidence - candidate_confidence) <= 0.08:
            return "close_alternative"
        return "fallback_classification"

    def _build_assumptions(
        self,
        *,
        extraction_result: ExtractionResult,
        candidate: HSCodeCandidate,
        rank: int,
        strategy_type: str,
    ) -> list[str]:
        """Describe the scenario assumptions that make a world distinct."""

        assumptions = [
            f"Classify the shipment under HS code {candidate.hs_code} ({candidate.description}).",
        ]
        if rank == 0:
            assumptions.append("Use the highest-confidence candidate as the submission baseline.")
        else:
            assumptions.append("Treat this as an alternate classification path that deserves comparison.")

        origin_country = extraction_result.origin_country
        destination_country = extraction_result.destination_country
        if origin_country and destination_country:
            assumptions.append(
                f"Evaluate the shipment as trade from {origin_country} into {destination_country}."
            )

        if extraction_result.hs_code_hint:
            if extraction_result.hs_code_hint == candidate.hs_code:
                assumptions.append("The extracted HS code hint supports this classification.")
            else:
                assumptions.append("This world overrides the extracted HS code hint and needs stronger support.")
        else:
            assumptions.append("No document HS code hint is available, so the product description drives classification.")

        if strategy_type == "fallback_classification":
            assumptions.append("Use this world as a contingency if stronger candidates are rejected during review.")

        return assumptions

    def _build_required_documents(
        self,
        *,
        extraction_result: ExtractionResult,
        candidate: HSCodeCandidate,
        strategy_type: str,
    ) -> list[str]:
        """List the extra support documents this world is likely to need."""

        required_documents = ["Commercial invoice", "Bill of lading"]

        if extraction_result.origin_country and extraction_result.destination_country:
            if extraction_result.origin_country.strip().lower() != extraction_result.destination_country.strip().lower():
                required_documents.append("Certificate of origin")

        if extraction_result.declared_value_usd is None:
            required_documents.append("Valuation worksheet")

        if strategy_type != "baseline" or candidate.confidence_score < 0.8:
            required_documents.append("Product specification sheet")

        return self._dedupe(required_documents)

    def _build_risk_flags(
        self,
        *,
        extraction_result: ExtractionResult,
        candidate: HSCodeCandidate,
        rank: int,
    ) -> list[str]:
        """Surface why a world might be harder to defend or operationalize."""

        risk_flags: list[str] = []
        if candidate.confidence_score < 0.75:
            risk_flags.append("Low HS confidence score")
        if rank > 0:
            risk_flags.append("Not the top-ranked HS candidate")
        if not extraction_result.origin_country:
            risk_flags.append("Missing origin country")
        if not extraction_result.incoterms:
            risk_flags.append("Missing incoterms")
        if extraction_result.declared_value_usd is None:
            risk_flags.append("Missing declared customs value")
        if extraction_result.hs_code_hint and extraction_result.hs_code_hint != candidate.hs_code:
            risk_flags.append("Conflicts with extracted HS code hint")
        return self._dedupe(risk_flags)

    def _build_reasoning(
        self,
        *,
        candidate: HSCodeCandidate,
        strategy_type: str,
        assumptions: list[str],
        risk_flags: list[str],
    ) -> str:
        """Assemble a compact explanation for why the world exists."""

        support_level = "strong" if strategy_type == "baseline" else "comparative"
        risk_summary = "No material generation risks identified." if not risk_flags else f"Key risks: {', '.join(risk_flags)}."
        return (
            f"{support_level.capitalize()} scenario built from HS candidate reasoning: {candidate.reasoning} "
            f"Core assumption: {assumptions[0]} {risk_summary}"
        )

    def _label_for(self, index: int, strategy_type: str) -> str:
        """Create stable user-facing world labels."""

        prefix = f"World {chr(65 + index)}"
        label_map = {
            "baseline": "Baseline classification",
            "review_primary": "Review-heavy primary",
            "close_alternative": "Close alternative classification",
            "fallback_classification": "Fallback classification",
        }
        return f"{prefix} - {label_map.get(strategy_type, 'Candidate classification')}"

    def _adjust_confidence(self, score: float, *, rank: int, risk_flags: list[str]) -> float:
        """Translate raw HS confidence into world confidence with light scenario penalties."""

        penalty = rank * 0.04 + len(risk_flags) * 0.015
        adjusted = max(0.0, min(1.0, score - penalty))
        return round(adjusted, 4)

    def _dedupe(self, items: list[str]) -> list[str]:
        """Preserve ordering when removing repeated support details."""

        seen: set[str] = set()
        deduped: list[str] = []
        for item in items:
            if item and item not in seen:
                seen.add(item)
                deduped.append(item)
        return deduped
