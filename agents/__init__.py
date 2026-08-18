"""Agents package for HR Multi-Agent System."""

def __getattr__(name):
    if name in ("root_agent", "run_query", "run_query_traced", "create_orchestrator_agent"):
        from . import orchestrator
        return getattr(orchestrator, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "root_agent",
    "run_query",
    "run_query_traced",
    "create_orchestrator_agent",
]
