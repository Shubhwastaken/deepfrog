"""Shared Pydantic schemas for the Customs Brain agent layer."""

from __future__ import annotations

from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class CustomsBrainModel(BaseModel):
    """Base schema with strict field handling across all agents."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ExtractionInput(CustomsBrainModel):
    """Raw shipping documents provided to the extraction agent."""

    invoice_text: str = Field(..., min_length=1)
    bill_of_lading_text: str = Field(..., min_length=1)


class ExtractionResult(CustomsBrainModel):
    """Normalized document facts consumed by downstream agents."""

    product_description: str
    hs_code_hint: str | None = None
    declared_value_usd: float | None = Field(default=None, ge=0)
    quantity: float | None = Field(default=None, ge=0)
    unit: str | None = None
    origin_country: str | None = None
    destination_country: str | None = None
    currency: str | None = None
    incoterms: str | None = None


class HSCodeInput(CustomsBrainModel):
    """Input contract for the HS code classification agent."""

    extraction_result: ExtractionResult


class HSCodeCandidate(CustomsBrainModel):
    """A single HS classification hypothesis."""

    hs_code: str = Field(..., pattern=r"^\d{6}$")
    description: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    reasoning: str


class HSCodeResult(CustomsBrainModel):
    """Ranked HS code candidates for a product."""

    candidates: list[HSCodeCandidate] = Field(..., min_length=1, max_length=4)


class World(CustomsBrainModel):
    """One candidate classification world considered by the system."""

    world_id: UUID = Field(default_factory=uuid4)
    hs_code: str = Field(..., pattern=r"^\d{6}$")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    extraction_data: ExtractionResult
    label: str
    strategy_type: str = "baseline"
    assumptions: list[str] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    generation_reasoning: str = ""


class WorldGenerationInput(CustomsBrainModel):
    """Input contract for generating candidate worlds."""

    hs_code_result: HSCodeResult
    extraction_result: ExtractionResult


class WorldGenerationResult(CustomsBrainModel):
    """Deterministically generated candidate worlds."""

    worlds: list[World] = Field(..., min_length=1)


class ComplianceInput(CustomsBrainModel):
    """Input contract for evaluating a single world for compliance."""

    world: World


class ComplianceRule(CustomsBrainModel):
    """A country rule applied during deterministic compliance checks."""

    hs_prefix: str | None = None
    product_keywords: list[str] = Field(default_factory=list)
    description: str
    citation: str | None = None
    compliant: bool = True
    warning: str | None = None
    violation: str | None = None


class ComplianceRuleSet(CustomsBrainModel):
    """Country-specific compliance rules stored in JSON files."""

    country: str
    applicable_rules: list[str] = Field(default_factory=list)
    hs_rules: list[ComplianceRule] = Field(default_factory=list)
    prohibited_keywords: list[str] = Field(default_factory=list)
    required_incoterms: list[str] = Field(default_factory=list)
    restricted_origins: list[str] = Field(default_factory=list)
    default_warnings: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ComplianceResult(CustomsBrainModel):
    """Compliance outcome for a single world."""

    world_id: UUID
    is_compliant: bool
    violations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    applicable_rules: list[str] = Field(default_factory=list)


class ValuationBenchmark(CustomsBrainModel):
    """Reference benchmark used to screen for invoice anomalies."""

    hs_prefix: str | None = None
    product_keywords: list[str] = Field(default_factory=list)
    median_unit_value_usd: float = Field(..., gt=0.0)
    description: str
    source_note: str | None = None


class ValuationInput(CustomsBrainModel):
    """Input contract for valuation screening."""

    world: World


class ValuationResult(CustomsBrainModel):
    """Deterministic valuation-screening output for a world."""

    world_id: UUID
    declared_unit_value_usd: float | None = Field(default=None, ge=0.0)
    reference_median_unit_value_usd: float | None = Field(default=None, ge=0.0)
    ratio_to_reference: float | None = Field(default=None, ge=0.0)
    verdict: Literal["under_invoiced", "within_range", "over_invoiced", "insufficient_data"]
    severity: Literal["none", "low", "medium", "high"]
    explanation: str
    evidence: list[str] = Field(default_factory=list)


class DutyInput(CustomsBrainModel):
    """Input contract for estimating duties for a single world."""

    world: World


class TariffRateRule(CustomsBrainModel):
    """A tariff lookup row matched by HS prefix."""

    hs_prefix: str = Field(..., min_length=2, max_length=6, pattern=r"^\d{2,6}$")
    duty_rate_percent: float = Field(..., ge=0.0)
    tax_rate_percent: float | None = Field(default=None, ge=0.0)
    description: str | None = None


class TariffRuleSet(CustomsBrainModel):
    """Country-specific tariff data stored in JSON files."""

    country: str
    currency: str = "USD"
    default_duty_rate_percent: float | None = Field(default=None, ge=0.0)
    default_tax_rate_percent: float = Field(default=0.0, ge=0.0)
    rates: list[TariffRateRule] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class DutyResult(CustomsBrainModel):
    """Duty and landed-cost estimate for a single world."""

    world_id: UUID
    duty_rate_percent: float = Field(..., ge=0.0)
    estimated_duty_usd: float = Field(..., ge=0.0)
    tax_usd: float = Field(..., ge=0.0)
    total_landed_cost_usd: float = Field(..., ge=0.0)
    calculation_breakdown: str


class CriticCitation(CustomsBrainModel):
    """A compact evidence citation produced by the critic."""

    title: str
    detail: str


class DebateInput(CustomsBrainModel):
    """Input contract for the devil's-advocate review."""

    world: World
    compliance_result: ComplianceResult
    duty_result: DutyResult
    valuation_result: ValuationResult | None = None


class DebateResult(CustomsBrainModel):
    """Risk-oriented review of a candidate world."""

    world_id: UUID
    risk_score: float = Field(..., ge=0.0, le=1.0)
    critiques: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    recommendation: Literal["accept", "reject", "review"]
    citations: list[CriticCitation] = Field(default_factory=list)
    fallback_used: bool = False


class EvaluationBundle(CustomsBrainModel):
    """A fully evaluated world used by the meta and output agents."""

    world: World
    compliance_result: ComplianceResult
    valuation_result: ValuationResult | None = None
    duty_result: DutyResult
    debate_result: DebateResult
    critic_result: DebateResult | None = None


class MetaScoringConfig(CustomsBrainModel):
    """Weights applied by the meta scorer."""

    compliance_weight: float = Field(default=0.4, ge=0.0)
    cost_weight: float = Field(default=0.2, ge=0.0)
    risk_weight: float = Field(default=0.2, ge=0.0)
    confidence_weight: float = Field(default=0.2, ge=0.0)


class MetaInput(CustomsBrainModel):
    """Input contract for final world selection."""

    evaluations: list[EvaluationBundle] = Field(..., min_length=1)
    scoring_config: MetaScoringConfig = Field(default_factory=MetaScoringConfig)


class MetaResult(CustomsBrainModel):
    """Winner selection and score summary from the meta agent."""

    winning_world_id: UUID
    final_hs_code: str = Field(..., pattern=r"^\d{6}$")
    score_breakdown: dict[str, float]
    reasoning: str
    alternatives: list[UUID] = Field(default_factory=list)


class AlternativeSummary(CustomsBrainModel):
    """Serialized summary for a non-winning world."""

    world_id: UUID
    label: str
    hs_code: str = Field(..., pattern=r"^\d{6}$")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    is_compliant: bool
    duty_rate_percent: float = Field(..., ge=0.0)
    estimated_duty_usd: float = Field(..., ge=0.0)
    total_landed_cost_usd: float = Field(..., ge=0.0)
    risk_score: float = Field(..., ge=0.0, le=1.0)
    composite_score: float
    recommendation: Literal["accept", "reject", "review"]
    strategy_type: str = ""
    assumptions: list[str] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    generation_reasoning: str = ""
    compliance_violations: list[str] = Field(default_factory=list)
    compliance_warnings: list[str] = Field(default_factory=list)
    applicable_rules: list[str] = Field(default_factory=list)
    duty_calculation_breakdown: str = ""
    valuation_verdict: str | None = None
    valuation_severity: str | None = None
    valuation_explanation: str | None = None
    valuation_evidence: list[str] = Field(default_factory=list)
    critic_critiques: list[str] = Field(default_factory=list)
    critic_strengths: list[str] = Field(default_factory=list)
    critic_citations: list[CriticCitation] = Field(default_factory=list)


class WinnerDetails(CustomsBrainModel):
    """Winner details surfaced to the API and frontend."""

    world_id: UUID
    label: str
    hs_code: str = Field(..., pattern=r"^\d{6}$")
    product_description: str
    destination_country: str | None = None
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    is_compliant: bool
    duty_rate_percent: float = Field(..., ge=0.0)
    estimated_duty_usd: float = Field(..., ge=0.0)
    total_landed_cost_usd: float = Field(..., ge=0.0)
    risk_score: float = Field(..., ge=0.0, le=1.0)
    recommendation: Literal["accept", "reject", "review"]
    reasoning: str
    strategy_type: str = ""
    assumptions: list[str] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    generation_reasoning: str = ""
    compliance_violations: list[str] = Field(default_factory=list)
    compliance_warnings: list[str] = Field(default_factory=list)
    applicable_rules: list[str] = Field(default_factory=list)
    duty_calculation_breakdown: str = ""
    valuation_verdict: str | None = None
    valuation_severity: str | None = None
    valuation_explanation: str | None = None
    valuation_evidence: list[str] = Field(default_factory=list)
    critic_critiques: list[str] = Field(default_factory=list)
    critic_strengths: list[str] = Field(default_factory=list)
    critic_citations: list[CriticCitation] = Field(default_factory=list)


class ComparisonTableRow(CustomsBrainModel):
    """Flat row representation of a world for UI display."""

    world_id: UUID
    label: str
    hs_code: str = Field(..., pattern=r"^\d{6}$")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    is_compliant: bool
    duty_rate_percent: float = Field(..., ge=0.0)
    estimated_duty_usd: float = Field(..., ge=0.0)
    total_landed_cost_usd: float = Field(..., ge=0.0)
    risk_score: float = Field(..., ge=0.0, le=1.0)
    recommendation: Literal["accept", "reject", "review"]
    composite_score: float
    valuation_verdict: str | None = None
    valuation_severity: str | None = None


class OutputInput(CustomsBrainModel):
    """Input contract for producing an API-ready response object."""

    meta_result: MetaResult
    evaluations: list[EvaluationBundle] = Field(..., min_length=1)


class OutputResult(CustomsBrainModel):
    """Flat, serializable output returned by the worker orchestration layer."""

    winning_world_id: UUID
    final_hs_code: str = Field(..., pattern=r"^\d{6}$")
    winner_details: WinnerDetails
    alternatives: list[AlternativeSummary] = Field(default_factory=list)
    comparison_table: list[ComparisonTableRow] = Field(default_factory=list)
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    meta_reasoning: str
    plain_language_summary: str


class ReportInput(CustomsBrainModel):
    """Input contract for the report agent."""

    output_result: OutputResult


class ReportResult(CustomsBrainModel):
    """Markdown report generated from the final output payload."""

    report_markdown: str
    filename_suggestion: str
