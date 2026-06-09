"""Tax Agent LangGraph definition.

Uses create_react_agent with a tax-specialised system prompt.
No tools — it answers purely from LLM knowledge.
"""

from __future__ import annotations

from langgraph.prebuilt import create_react_agent

from common.llm import get_llm

TAX_SYSTEM_PROMPT = """You are a specialist tax attorney. Answer concisely in under 150 words.

Cover only the most relevant points:
- Civil vs. criminal penalties (IRC §§ 6651, 6662, 6663; 18 U.S.C. § 7201)
- IRS enforcement and back taxes
- Individual vs. corporate liability

End with a one-line disclaimer: educational purposes only; consult a licensed attorney.
"""


def create_graph():
    """Return a compiled LangGraph create_react_agent for tax questions."""
    llm = get_llm()
    graph = create_react_agent(
        model=llm,
        tools=[],
        prompt=TAX_SYSTEM_PROMPT,
    )
    return graph