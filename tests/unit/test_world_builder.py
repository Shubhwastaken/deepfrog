from agents.schemas import ExtractionResult, HSCodeCandidate
from agents.world.builder import WorldBuilder


def test_world_builder_creates_richer_baseline_and_alternative_worlds():
    builder = WorldBuilder()
    extraction = ExtractionResult(
        product_description="Portable computer",
        hs_code_hint="847130",
        origin_country="China",
        destination_country="United States",
        declared_value_usd=1200.0,
        incoterms="FOB",
    )
    candidates = [
        HSCodeCandidate(
            hs_code="847130",
            description="Portable automatic data processing machines",
            confidence_score=0.91,
            reasoning="Matches the product description for a laptop computer.",
        ),
        HSCodeCandidate(
            hs_code="847141",
            description="Other digital automatic data processing machines",
            confidence_score=0.86,
            reasoning="Could apply if the product is treated as another ADP machine configuration.",
        ),
    ]

    worlds = builder.build(extraction, candidates)

    assert len(worlds) == 2
    assert worlds[0].label == "World A - Baseline classification"
    assert worlds[0].strategy_type == "baseline"
    assert "The extracted HS code hint supports this classification." in worlds[0].assumptions
    assert "Certificate of origin" in worlds[0].required_documents

    assert worlds[1].label == "World B - Close alternative classification"
    assert worlds[1].strategy_type == "close_alternative"
    assert "Not the top-ranked HS candidate" in worlds[1].risk_flags
    assert "Conflicts with extracted HS code hint" in worlds[1].risk_flags
    assert worlds[1].confidence_score < candidates[1].confidence_score


def test_world_builder_marks_low_confidence_primary_for_review():
    builder = WorldBuilder()
    extraction = ExtractionResult(
        product_description="Plastic storage box",
        destination_country="United States",
    )
    candidates = [
        HSCodeCandidate(
            hs_code="392310",
            description="Plastic boxes, cases, crates and similar articles",
            confidence_score=0.74,
            reasoning="The description suggests a plastic packing article, but supporting details are thin.",
        ),
    ]

    worlds = builder.build(extraction, candidates)

    assert len(worlds) == 1
    assert worlds[0].strategy_type == "review_primary"
    assert "Missing origin country" in worlds[0].risk_flags
    assert "Missing incoterms" in worlds[0].risk_flags
    assert "Missing declared customs value" in worlds[0].risk_flags
    assert "Valuation worksheet" in worlds[0].required_documents
    assert "Product specification sheet" in worlds[0].required_documents
