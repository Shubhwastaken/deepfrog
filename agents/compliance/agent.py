"""Compliance evaluation agent."""

from __future__ import annotations

import json
import re
from pathlib import Path

from agents.base.base_agent import BaseAgent
from agents.compliance.prompts import build_prompt
from agents.schemas import ComplianceInput, ComplianceResult, ComplianceRuleSet, World


class ComplianceAgent(BaseAgent[ComplianceInput, ComplianceResult]):
    """Evaluate a world against destination-specific compliance rules."""

    agent_name = "compliance"

    def __init__(self, *args, rules_dir: Path | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.rules_dir = rules_dir or Path(__file__).resolve().parent / "rules"

    async def run(self, input: ComplianceInput) -> ComplianceResult:
        """Return a compliance decision for a single candidate world."""

        validated_input = ComplianceInput.model_validate(input)
        world = validated_input.world
        destination_country = world.extraction_data.destination_country
        ruleset = self._load_ruleset(destination_country)

        if ruleset is None:
            prompt = build_prompt(world.model_dump(mode="json"))
            llm_result = await self.call_llm(prompt, ComplianceResult)
            payload = llm_result.model_dump(mode="json")
            payload["world_id"] = world.world_id
            return ComplianceResult.model_validate(payload)

        return self._evaluate_with_rules(world, ruleset)

    def _evaluate_with_rules(self, world: World, ruleset: ComplianceRuleSet) -> ComplianceResult:
        """Apply a country ruleset without needing an LLM call."""

        description = (world.extraction_data.product_description or "").lower()
        origin_country = (world.extraction_data.origin_country or "").strip().lower()
        incoterms = (world.extraction_data.incoterms or "").strip().upper()

        violations: list[str] = []
        warnings = list(ruleset.default_warnings)
        applicable_rules = list(ruleset.applicable_rules)

        for rule in ruleset.hs_rules:
            if rule.hs_prefix and not world.hs_code.startswith(rule.hs_prefix):
                continue
            applicable_rules.append(rule.description)
            if rule.warning:
                warnings.append(rule.warning)
            if not rule.compliant:
                violations.append(rule.violation or rule.description)

        for keyword in ruleset.prohibited_keywords:
            if keyword.lower() in description:
                violations.append(f"Product description contains prohibited keyword '{keyword}'.")

        if ruleset.required_incoterms:
            if not incoterms:
                warnings.append(
                    f"Destination rules prefer one of these incoterms: {', '.join(ruleset.required_incoterms)}."
                )
            elif incoterms not in {term.upper() for term in ruleset.required_incoterms}:
                violations.append(
                    f"Incoterms '{incoterms}' are not in the allowed set: {', '.join(ruleset.required_incoterms)}."
                )

        if origin_country and origin_country in {country.lower() for country in ruleset.restricted_origins}:
            violations.append(
                f"Origin country '{world.extraction_data.origin_country}' is restricted for destination {ruleset.country}."
            )

        return ComplianceResult(
            world_id=world.world_id,
            is_compliant=not violations,
            violations=self._dedupe(violations),
            warnings=self._dedupe(warnings),
            applicable_rules=self._dedupe(applicable_rules + ruleset.notes),
        )

    def _load_ruleset(self, country: str | None) -> ComplianceRuleSet | None:
        """Load the destination-country JSON ruleset when available."""

        if not country:
            return None

        for path in self._candidate_rule_paths(country):
            if path.exists():
                with path.open("r", encoding="utf-8") as file_obj:
                    payload = json.load(file_obj)
                return ComplianceRuleSet.model_validate(payload)
        return None

    def _candidate_rule_paths(self, country: str) -> list[Path]:
        """Build normalized filename candidates for a country name."""

        normalized = re.sub(r"[^a-z0-9]+", "_", country.strip().lower()).strip("_")
        candidates = [normalized]
        if normalized.endswith("_arab_emirates"):
            candidates.append("uae")
        if normalized == "united_states":
            candidates.append("usa")
        return [self.rules_dir / f"{candidate}.json" for candidate in dict.fromkeys(candidates)]

    def _dedupe(self, items: list[str]) -> list[str]:
        """Preserve order while removing duplicate messages."""

        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            if item and item not in seen:
                seen.add(item)
                result.append(item)
        return result
