"""Deterministic valuation-screening agent."""

from __future__ import annotations

import json
from pathlib import Path

from agents.base.base_agent import BaseAgent
from agents.schemas import ValuationBenchmark, ValuationInput, ValuationResult, World


class ValuationAgent(BaseAgent[ValuationInput, ValuationResult]):
    """Flag suspicious invoice values using deterministic benchmark screening."""

    agent_name = "valuation"

    def __init__(self, *args, benchmarks_path: Path | None = None, **kwargs) -> None:
        kwargs.setdefault("client", self._noop_client)
        kwargs.setdefault("model", "deterministic-valuation")
        super().__init__(*args, **kwargs)
        self.benchmarks_path = benchmarks_path or Path(__file__).resolve().parent / "benchmarks.json"
        self._benchmarks = self._load_benchmarks()

    async def _noop_client(self, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("ValuationAgent does not require an LLM client.")

    async def run(self, input: ValuationInput) -> ValuationResult:
        """Return a deterministic invoice-screening verdict for one world."""

        validated_input = ValuationInput.model_validate(input)
        world = validated_input.world
        declared_unit_value = self._declared_unit_value(world)
        benchmark = self._match_benchmark(world)

        if declared_unit_value is None or benchmark is None:
            return ValuationResult(
                world_id=world.world_id,
                declared_unit_value_usd=declared_unit_value,
                reference_median_unit_value_usd=benchmark.median_unit_value_usd if benchmark else None,
                ratio_to_reference=None,
                verdict="insufficient_data",
                severity="low",
                explanation="Unable to complete deterministic valuation screening because the declaration or benchmark data is incomplete.",
                evidence=self._build_evidence(world, benchmark),
            )

        ratio = round(declared_unit_value / benchmark.median_unit_value_usd, 4)
        verdict, severity = self._classify_ratio(ratio)
        return ValuationResult(
            world_id=world.world_id,
            declared_unit_value_usd=round(declared_unit_value, 4),
            reference_median_unit_value_usd=benchmark.median_unit_value_usd,
            ratio_to_reference=ratio,
            verdict=verdict,
            severity=severity,
            explanation=(
                f"Declared unit value ${declared_unit_value:.2f} versus reference median "
                f"${benchmark.median_unit_value_usd:.2f} ({ratio:.2%} of reference) "
                f"results in a {verdict.replace('_', ' ')} determination with {severity} severity."
            ),
            evidence=self._build_evidence(world, benchmark),
        )

    def _load_benchmarks(self) -> list[ValuationBenchmark]:
        with self.benchmarks_path.open("r", encoding="utf-8") as file_obj:
            payload = json.load(file_obj)
        return [ValuationBenchmark.model_validate(item) for item in payload.get("benchmarks", [])]

    def _match_benchmark(self, world: World) -> ValuationBenchmark | None:
        description = (world.extraction_data.product_description or "").lower()
        ranked = sorted(self._benchmarks, key=lambda item: len(item.hs_prefix or ""), reverse=True)
        for benchmark in ranked:
            if benchmark.hs_prefix and not world.hs_code.startswith(benchmark.hs_prefix):
                continue
            if benchmark.product_keywords and not any(
                keyword.lower() in description for keyword in benchmark.product_keywords
            ):
                continue
            return benchmark
        return None

    def _declared_unit_value(self, world: World) -> float | None:
        declared_value = world.extraction_data.declared_value_usd
        if declared_value is None:
            return None
        quantity = world.extraction_data.quantity
        if quantity and quantity > 0:
            return declared_value / quantity
        return declared_value

    def _classify_ratio(self, ratio: float) -> tuple[str, str]:
        if ratio < 0.25:
            return "under_invoiced", "high"
        if ratio < 0.5:
            return "under_invoiced", "medium"
        if ratio <= 1.5:
            return "within_range", "none"
        if ratio > 2.5:
            return "over_invoiced", "high"
        return "over_invoiced", "medium"

    def _build_evidence(self, world: World, benchmark: ValuationBenchmark | None) -> list[str]:
        evidence = [
            f"Declared value: {world.extraction_data.declared_value_usd if world.extraction_data.declared_value_usd is not None else 'unknown'} USD",
            f"Quantity: {world.extraction_data.quantity if world.extraction_data.quantity is not None else 'unknown'}",
        ]
        if benchmark is not None:
            evidence.append(
                f"Reference median: {benchmark.median_unit_value_usd} USD ({benchmark.description})"
            )
            if benchmark.source_note:
                evidence.append(benchmark.source_note)
        return evidence
