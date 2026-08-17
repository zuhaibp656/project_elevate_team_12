"""Agent entry point for ADK Web and CLI tools."""
from .orchestrator import root_agent, run_query, run_query_traced, main

__all__ = ["root_agent", "run_query", "run_query_traced", "main"]

if __name__ == "__main__":
    main()
