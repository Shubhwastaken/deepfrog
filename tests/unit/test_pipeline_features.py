import asyncio
import sys
from pathlib import Path

from agents.registry import get_registered_agents
from agents.compliance import ComplianceAgent, ComplianceInput
from agents.critic import CriticAgent
from agents.duty import DutyAgent, DutyInput
from agents.schemas import ComplianceResult, DebateInput, DutyResult, ExtractionResult, ValuationResult, World
from agents.valuation import ValuationAgent, ValuationInput


def _make_mobile_world(*, declared_value_usd: float, quantity: float = 1.0) -> World:
    return World(
        hs_code="851712",
        confidence_score=0.92,
        extraction_data=ExtractionResult(
            product_description="Smartphone mobile handset",
            declared_value_usd=declared_value_usd,
            destination_country="India",
            origin_country="China",
            quantity=quantity,
            incoterms="FOB",
        ),
        label="World A - Baseline classification",
        strategy_type="baseline",
        generation_reasoning="Built from the top handset candidate.",
    )


def test_agent_registry_includes_new_agents():
    registry = get_registered_agents()
    assert "valuation" in registry
    assert "critic" in registry
    assert "compliance" in registry
    assert "duty" in registry


def test_fastapi_routes_include_rerun_and_pipeline_metrics():
    sys.path.insert(0, str(Path("backend").resolve()))
    from app.main import app

    route_paths = {route.path for route in app.routes if getattr(route, "path", None)}
    assert len(route_paths) >= 13
    assert "/api/auth/refresh" in route_paths
    assert "/api/rerun/{job_id}" in route_paths
    assert "/api/metrics/pipeline" in route_paths


def test_valuation_flags_under_invoiced_mobile_handset():
    result = asyncio.run(ValuationAgent().run(ValuationInput(world=_make_mobile_world(declared_value_usd=0.5))))
    assert result.verdict == "under_invoiced"
    assert result.severity == "high"
    assert result.reference_median_unit_value_usd == 3.5


def test_duty_and_compliance_use_deterministic_india_rules():
    world = _make_mobile_world(declared_value_usd=100.0)

    duty_result = asyncio.run(DutyAgent(client=lambda **kwargs: None, model="unused").run(DutyInput(world=world)))
    assert duty_result.duty_rate_percent == 20.0
    assert duty_result.tax_usd == 21.6
    assert "Basic Customs Duty 20% plus IGST 18%" in duty_result.calculation_breakdown

    compliance_result = asyncio.run(
        ComplianceAgent(client=lambda **kwargs: None, model="unused").run(ComplianceInput(world=world))
    )
    applicable_rules = " ".join(compliance_result.applicable_rules)
    assert "BIS" in applicable_rules
    assert "IEC" in applicable_rules
    assert "FSSAI" in " ".join(compliance_result.applicable_rules + compliance_result.warnings + compliance_result.violations)
    assert "CDSCO" in " ".join(compliance_result.applicable_rules + compliance_result.warnings + compliance_result.violations)


def test_critic_fallback_produces_three_citations():
    world = _make_mobile_world(declared_value_usd=0.5)
    valuation = ValuationResult(
        world_id=world.world_id,
        declared_unit_value_usd=0.5,
        reference_median_unit_value_usd=3.5,
        ratio_to_reference=0.1429,
        verdict="under_invoiced",
        severity="high",
        explanation="Declared unit value $0.50 versus reference median $3.50.",
        evidence=["declared", "reference"],
    )
    compliance = ComplianceResult(
        world_id=world.world_id,
        is_compliant=True,
        violations=[],
        warnings=["Verify BIS CRS registration details."],
        applicable_rules=[
            "IEC required for commercial importers.",
            "BIS Compulsory Registration Scheme applies to mobile handsets.",
        ],
    )
    duty = DutyResult(
        world_id=world.world_id,
        duty_rate_percent=20.0,
        estimated_duty_usd=20.0,
        tax_usd=21.6,
        total_landed_cost_usd=141.6,
        calculation_breakdown="Applied India mobile handset tariff: Basic Customs Duty 20% plus IGST 18%.",
    )

    result = asyncio.run(
        CriticAgent().run(
            DebateInput(
                world=world,
                compliance_result=compliance,
                duty_result=duty,
                valuation_result=valuation,
            )
        )
    )

    assert result.fallback_used is True
    assert len(result.citations) == 3
    assert result.recommendation == "reject"
