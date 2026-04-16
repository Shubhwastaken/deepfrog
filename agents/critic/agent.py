"""Critic agent wrapper around the deterministic debate implementation."""

from agents.debate.agent import DebateAgent


class CriticAgent(DebateAgent):
    """Compatibility wrapper exposing the deterministic critic stage."""

    agent_name = "critic"
