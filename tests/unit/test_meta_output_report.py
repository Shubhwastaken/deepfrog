import asyncio

from agents.meta.scorer import calculate_scores
from agents.output import OutputAgent
from agents.report.agent import ReportAgent
from agents.schemas import (
    CriticCitation,
    ComplianceResult,
    DebateResult,
    DutyResult,
    EvaluationBundle,
    ExtractionResult,
    MetaResult,
    MetaScoringConfig,
    OutputInput,
    ReportInput,
    ValuationResult,
    World,
)


async def _unused_client(**kwargs):
    raise AssertionError(f"Unexpected LLM call: {kwargs}")


def _make_world(
    *,
    label: str,
    hs_code: str,
    confidence_score: float,
    strategy_type: str,
    risk_flags: list[str],
) -> World:
    return World(
        hs_code=hs_code,
        confidence_score=confidence_score,
        extraction_data=ExtractionResult(
            product_description="Laptop computer",
            origin_country="China",
            destination_country="United States",
            declared_value_usd=1000.0,
            incoterms="FOB",
        ),
        label=label,
        strategy_type=strategy_type,
        assumptions=["Classify based on the supplied product description."],
        required_documents=["Commercial invoice", "Bill of lading", "Certificate of origin"],
        risk_flags=risk_flags,
        generation_reasoning="Built from ranked HS candidates and shipment context.",
    )


def _make_bundle(
    *,
    world: World,
    is_compliant: bool = True,
    landed_cost: float = 1100.0,
    risk_score: float = 0.2,
    recommendation: str = "accept",
    violations: list[str] | None = None,
    warnings: list[str] | None = None,
    applicable_rules: list[str] | None = None,
    critiques: list[str] | None = None,
    strengths: list[str] | None = None,
    citations: list[CriticCitation] | None = None,
    valuation_result: ValuationResult | None = None,
) -> EvaluationBundle:
    return EvaluationBundle(
        world=world,
        compliance_result=ComplianceResult(
            world_id=world.world_id,
            is_compliant=is_compliant,
            violations=violations or [],
            warnings=warnings or [],
            applicable_rules=applicable_rules or ["General import documentation required."],
        ),
        valuation_result=valuation_result,
        duty_result=DutyResult(
            world_id=world.world_id,
            duty_rate_percent=5.0,
            estimated_duty_usd=50.0,
            tax_usd=50.0,
            total_landed_cost_usd=landed_cost,
            calculation_breakdown="Applied a 5% duty and 5% tax for the destination.",
        ),
        debate_result=DebateResult(
            world_id=world.world_id,
            risk_score=risk_score,
            critiques=critiques or [],
            strengths=strengths or ["Supported by available product information."],
            recommendation=recommendation,
            citations=citations or [],
        ),
    )


def test_calculate_scores_uses_world_confidence_and_generation_flags():
    baseline_world = _make_world(
        label="World A - Baseline classification",
        hs_code="847130",
        confidence_score=0.92,
        strategy_type="baseline",
        risk_flags=[],
    )
    fallback_world = _make_world(
        label="World B - Fallback classification",
        hs_code="847141",
        confidence_score=0.76,
        strategy_type="fallback_classification",
        risk_flags=["Low HS confidence score", "Conflicts with extracted HS code hint"],
    )

    baseline_bundle = _make_bundle(world=baseline_world, landed_cost=1100.0, risk_score=0.2)
    fallback_bundle = _make_bundle(world=fallback_world, landed_cost=1100.0, risk_score=0.2)

    scores = calculate_scores(
        [baseline_bundle, fallback_bundle],
        MetaScoringConfig(),
    )

    assert scores[str(baseline_world.world_id)] > scores[str(fallback_world.world_id)]


def test_output_and_report_include_world_generation_context():
    winning_world = _make_world(
        label="World A - Baseline classification",
        hs_code="847130",
        confidence_score=0.9,
        strategy_type="baseline",
        risk_flags=[],
    )
    alternative_world = _make_world(
        label="World B - Close alternative classification",
        hs_code="847141",
        confidence_score=0.81,
        strategy_type="close_alternative",
        risk_flags=["Not the top-ranked HS candidate"],
    )

    winning_valuation = ValuationResult(
        world_id=winning_world.world_id,
        declared_unit_value_usd=1000.0,
        reference_median_unit_value_usd=950.0,
        ratio_to_reference=1.0526,
        verdict="within_range",
        severity="none",
        explanation="Declared value is within the expected benchmark range.",
        evidence=["Declared value: 1000.0 USD", "Reference median: 950.0 USD"],
    )
    winning_bundle = _make_bundle(
        world=winning_world,
        landed_cost=1120.0,
        risk_score=0.18,
        warnings=["Retain the certificate of origin in the filing packet."],
        applicable_rules=["General import documentation required.", "Origin evidence should be retained."],
        critiques=["Analyst should confirm the product description is not overly broad."],
        strengths=["The baseline candidate aligns with the extracted HS hint."],
        citations=[CriticCitation(title="Tariff Calculation", detail="Applied a 5% duty and 5% tax for the destination.")],
        valuation_result=winning_valuation,
    )
    alternative_valuation = ValuationResult(
        world_id=alternative_world.world_id,
        declared_unit_value_usd=1000.0,
        reference_median_unit_value_usd=1400.0,
        ratio_to_reference=0.7143,
        verdict="under_invoiced",
        severity="low",
        explanation="Declared value is below the benchmark and should be reviewed.",
        evidence=["Declared value: 1000.0 USD", "Reference median: 1400.0 USD"],
    )
    alternative_bundle = _make_bundle(
        world=alternative_world,
        landed_cost=1140.0,
        risk_score=0.28,
        recommendation="review",
        violations=["Specification sheet is required before filing under the alternative path."],
        warnings=["Alternative path needs stronger catalog support."],
        applicable_rules=["General import documentation required.", "Product specification sheet required."],
        critiques=["Alternative classification has weaker documentary support than the baseline."],
        strengths=["Duty exposure remains moderate under this alternate code."],
        citations=[CriticCitation(title="Compliance Rules", detail="Product specification sheet required.")],
        valuation_result=alternative_valuation,
    )

    output_agent = OutputAgent(client=_unused_client, model="test-model")
    output_result = asyncio.run(
        output_agent.run(
            OutputInput(
                meta_result=MetaResult(
                    winning_world_id=winning_world.world_id,
                    final_hs_code=winning_world.hs_code,
                    score_breakdown={
                        str(winning_world.world_id): 0.91,
                        str(alternative_world.world_id): 0.78,
                    },
                    reasoning="The baseline world has stronger support and lower overall risk.",
                    alternatives=[alternative_world.world_id],
                ),
                evaluations=[winning_bundle, alternative_bundle],
            )
        )
    )

    assert output_result.winner_details.strategy_type == "baseline"
    assert output_result.winner_details.assumptions == winning_world.assumptions
    assert output_result.winner_details.generation_reasoning == winning_world.generation_reasoning
    assert output_result.winner_details.compliance_warnings == [
        "Retain the certificate of origin in the filing packet."
    ]
    assert output_result.winner_details.valuation_explanation == "Declared value is within the expected benchmark range."
    assert output_result.winner_details.critic_critiques == [
        "Analyst should confirm the product description is not overly broad."
    ]
    assert output_result.alternatives[0].strategy_type == "close_alternative"
    assert output_result.alternatives[0].compliance_violations == [
        "Specification sheet is required before filing under the alternative path."
    ]
    assert output_result.alternatives[0].duty_calculation_breakdown == "Applied a 5% duty and 5% tax for the destination."
    assert output_result.alternatives[0].valuation_explanation == "Declared value is below the benchmark and should be reviewed."
    assert output_result.alternatives[0].critic_citations[0].title == "Compliance Rules"
    assert "world confidence score of 0.90" in output_result.plain_language_summary

    report_agent = ReportAgent(client=_unused_client, model="test-model")
    report_result = asyncio.run(report_agent.run(ReportInput(output_result=output_result)))

    assert "## World Generation Reasoning" in report_result.report_markdown
    assert "## World Assumptions" in report_result.report_markdown
    assert "## Required Documents" in report_result.report_markdown
    assert "Strategy Type: Baseline" in report_result.report_markdown
    assert "World B - Close alternative classification" in report_result.report_markdown
