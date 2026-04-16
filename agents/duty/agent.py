"""Duty estimation agent."""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import Field

from agents.base.base_agent import BaseAgent
from agents.duty.prompts import build_prompt
from agents.schemas import CustomsBrainModel, DutyInput, DutyResult, TariffRuleSet, World


class DutyEstimatePayload(CustomsBrainModel):
    """Intermediate LLM payload used when no tariff file exists."""

    duty_rate_percent: float = Field(..., ge=0.0)
    tax_rate_percent: float = Field(default=0.0, ge=0.0)
    calculation_breakdown: str


class DutyAgent(BaseAgent[DutyInput, DutyResult]):
    """Estimate duty and landed cost for a single world."""

    agent_name = "duty"

    def __init__(self, *args, rules_dir: Path | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.rules_dir = rules_dir or Path(__file__).resolve().parent / "rules"

    async def run(self, input: DutyInput) -> DutyResult:
        """Return duty and tax estimates for a single world."""

        validated_input = DutyInput.model_validate(input)
        world = validated_input.world
        destination_country = world.extraction_data.destination_country
        tariff_rules = self._load_ruleset(destination_country)

        if tariff_rules is None:
            prompt = build_prompt(world.model_dump(mode="json"))
            estimate = await self.call_llm(prompt, DutyEstimatePayload)
            return self._calculate_from_rates(
                world=world,
                duty_rate_percent=estimate.duty_rate_percent,
                tax_rate_percent=estimate.tax_rate_percent,
                breakdown=estimate.calculation_breakdown,
            )

        return self._calculate_with_rules(world, tariff_rules)

    def _calculate_with_rules(self, world: World, tariff_rules: TariffRuleSet) -> DutyResult:
        """Calculate landed cost from a matching tariff ruleset."""

        matched_rule = None
        for rule in sorted(tariff_rules.rates, key=lambda item: len(item.hs_prefix), reverse=True):
            if world.hs_code.startswith(rule.hs_prefix):
                matched_rule = rule
                break

        duty_rate_percent = (
            matched_rule.duty_rate_percent
            if matched_rule is not None
            else float(tariff_rules.default_duty_rate_percent or 0.0)
        )
        tax_rate_percent = (
            matched_rule.tax_rate_percent
            if matched_rule is not None and matched_rule.tax_rate_percent is not None
            else float(tariff_rules.default_tax_rate_percent)
        )

        matched_text = matched_rule.description if matched_rule and matched_rule.description else "default country tariff"
        breakdown = (
            f"Applied {matched_text} for {tariff_rules.country}: "
            f"duty {duty_rate_percent:.2f}% and tax {tax_rate_percent:.2f}%."
        )
        if tariff_rules.notes:
            breakdown = f"{breakdown} Notes: {' '.join(tariff_rules.notes)}"

        return self._calculate_from_rates(
            world=world,
            duty_rate_percent=duty_rate_percent,
            tax_rate_percent=tax_rate_percent,
            breakdown=breakdown,
        )

    def _calculate_from_rates(
        self,
        *,
        world: World,
        duty_rate_percent: float,
        tax_rate_percent: float,
        breakdown: str,
    ) -> DutyResult:
        """Convert percentage rates into dollar estimates."""

        customs_value = float(world.extraction_data.declared_value_usd or 0.0)
        estimated_duty_usd = round(customs_value * duty_rate_percent / 100, 2)
        tax_base = customs_value + estimated_duty_usd
        tax_usd = round(tax_base * tax_rate_percent / 100, 2)
        total_landed_cost_usd = round(customs_value + estimated_duty_usd + tax_usd, 2)

        return DutyResult(
            world_id=world.world_id,
            duty_rate_percent=round(duty_rate_percent, 4),
            estimated_duty_usd=estimated_duty_usd,
            tax_usd=tax_usd,
            total_landed_cost_usd=total_landed_cost_usd,
            calculation_breakdown=breakdown,
        )

    def _load_ruleset(self, country: str | None) -> TariffRuleSet | None:
        """Load tariff data for a destination country, if present."""

        if not country:
            return None

        for path in self._candidate_rule_paths(country):
            if path.exists():
                with path.open("r", encoding="utf-8") as file_obj:
                    payload = json.load(file_obj)
                return TariffRuleSet.model_validate(payload)
        return None

    def _candidate_rule_paths(self, country: str) -> list[Path]:
        """Build normalized tariff filename candidates for a country name."""

        normalized = re.sub(r"[^a-z0-9]+", "_", country.strip().lower()).strip("_")
        candidates = [normalized]
        if normalized.endswith("_arab_emirates"):
            candidates.append("uae")
        if normalized == "united_states":
            candidates.append("usa")
        return [self.rules_dir / f"{candidate}.json" for candidate in dict.fromkeys(candidates)]
