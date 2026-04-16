"""Central registry for all agent implementations."""

from __future__ import annotations

from agents.compliance.agent import ComplianceAgent
from agents.critic.agent import CriticAgent
from agents.debate.agent import DebateAgent
from agents.duty.agent import DutyAgent
from agents.extraction.agent import ExtractionAgent
from agents.hs_code.agent import HSCodeAgent
from agents.meta.agent import MetaAgent
from agents.output.agent import OutputAgent
from agents.report.agent import ReportAgent
from agents.valuation.agent import ValuationAgent
from agents.world.agent import WorldAgent
from agents.world_generator.agent import WorldGeneratorAgent

AGENT_REGISTRY = {
    "extraction": ExtractionAgent,
    "hs_code": HSCodeAgent,
    "world": WorldAgent,
    "world_generator": WorldGeneratorAgent,
    "compliance": ComplianceAgent,
    "valuation": ValuationAgent,
    "duty": DutyAgent,
    "debate": DebateAgent,
    "critic": CriticAgent,
    "meta": MetaAgent,
    "output": OutputAgent,
    "report": ReportAgent,
}


def get_registered_agents() -> dict[str, type]:
    """Return a copy of the import-safe agent registry."""

    return dict(AGENT_REGISTRY)
