"""Backward-compatible entrypoint for the shopping analysis LangGraph."""

from app.services.graph.graph_builder import _analysis_graph, analyze_shopping

__all__ = ["analyze_shopping"]
