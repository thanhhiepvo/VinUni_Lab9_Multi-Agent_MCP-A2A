"""Animated HTML workflow diagram for the multi-agent A2A pipeline."""

from __future__ import annotations

WORKFLOW_STEPS = (
    "customer",
    "registry",
    "law",
    "routing",
    "parallel",
    "aggregate",
)

STEP_LABELS = {
    "idle": "Ready — submit a question to start the agent pipeline.",
    "customer": "Customer Agent (:10100) — understanding question & delegating…",
    "registry": "Registry (:10000) — discovering Law Agent endpoint…",
    "law": "Law Agent (:10101) — analyzing legal aspects…",
    "routing": "Law Agent — deciding which specialists are needed…",
    "parallel": "Tax (:10102) + Compliance (:10103) — running in parallel…",
    "aggregate": "Law Agent — aggregating specialist analyses…",
    "complete": "Done — response returned to you.",
    "error": "Pipeline stopped — check backend services.",
}

_BASE_CSS = """
<style>
  .wf-wrap {
    font-family: ui-sans-serif, system-ui, -apple-system, sans-serif;
    padding: 16px 12px 8px;
    border-radius: 12px;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    color: #e2e8f0;
    overflow-x: auto;
  }
  .wf-status {
    text-align: center;
    font-size: 0.9rem;
    color: #94a3b8;
    margin-bottom: 14px;
    min-height: 1.4em;
  }
  .wf-flow {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    flex-wrap: nowrap;
    min-width: max-content;
    padding-bottom: 8px;
  }
  .wf-node {
    position: relative;
    min-width: 88px;
    padding: 10px 8px;
    border-radius: 10px;
    border: 2px solid #334155;
    background: #1e293b;
    text-align: center;
    transition: all 0.35s ease;
  }
  .wf-node .wf-title { font-size: 0.72rem; font-weight: 700; color: #f1f5f9; }
  .wf-node .wf-port { font-size: 0.62rem; color: #64748b; margin-top: 2px; }
  .wf-node.active {
    border-color: #38bdf8;
    background: #0c4a6e;
    box-shadow: 0 0 18px rgba(56, 189, 248, 0.55);
    animation: wf-pulse 1.2s ease-in-out infinite;
  }
  .wf-node.done {
    border-color: #4ade80;
    background: #14532d;
  }
  .wf-arrow {
    color: #475569;
    font-size: 1.1rem;
    transition: color 0.35s ease;
    user-select: none;
  }
  .wf-arrow.active { color: #38bdf8; animation: wf-flow 0.8s linear infinite; }
  .wf-arrow.done { color: #4ade80; }
  .wf-parallel {
    display: flex;
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
  }
  .wf-parallel-bracket {
    font-size: 0.65rem;
    color: #64748b;
    text-align: center;
    letter-spacing: 0.05em;
  }
  @keyframes wf-pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.04); }
  }
  @keyframes wf-flow {
    0% { opacity: 0.4; }
    50% { opacity: 1; }
    100% { opacity: 0.4; }
  }
</style>
"""

_NODES = ("user", "customer", "registry", "law", "tax", "compliance", "response")

_NODE_META = {
    "user": ("User", ""),
    "customer": ("Customer", ":10100"),
    "registry": ("Registry", ":10000"),
    "law": ("Law Agent", ":10101"),
    "tax": ("Tax Agent", ":10102"),
    "compliance": ("Compliance", ":10103"),
    "response": ("Response", ""),
}

# Which nodes are done when a step completes (cumulative).
_STEP_DONE: dict[str, set[str]] = {
    "idle": set(),
    "customer": {"user"},
    "registry": {"user", "customer"},
    "law": {"user", "customer", "registry"},
    "routing": {"user", "customer", "registry", "law"},
    "parallel": {"user", "customer", "registry", "law"},
    "aggregate": {"user", "customer", "registry", "law", "tax", "compliance"},
    "complete": set(_NODES),
    "error": set(),
}

_STEP_ACTIVE: dict[str, set[str]] = {
    "idle": set(),
    "customer": {"customer"},
    "registry": {"registry"},
    "law": {"law"},
    "routing": {"law"},
    "parallel": {"tax", "compliance"},
    "aggregate": {"law"},
    "complete": {"response"},
    "error": set(),
}


def _node_class(name: str, step: str) -> str:
    active = name in _STEP_ACTIVE.get(step, set())
    done = name in _STEP_DONE.get(step, set())
    if step == "complete" and name == "response":
        return "wf-node active"
    if active:
        return "wf-node active"
    if done:
        return "wf-node done"
    return "wf-node"


def _arrow_class(left: str, right: str, step: str) -> str:
    if step == "idle" or step == "error":
        return "wf-arrow"
    right_active = right in _STEP_ACTIVE.get(step, set())
    right_done = right in _STEP_DONE.get(step, set())
    if right_active or right_done:
        return "wf-arrow active" if right_active else "wf-arrow done"
    return "wf-arrow"


def _render_node(name: str, step: str) -> str:
    title, port = _NODE_META[name]
    cls = _node_class(name, step)
    port_html = f'<div class="wf-port">{port}</div>' if port else ""
    return f'<div class="{cls}"><div class="wf-title">{title}</div>{port_html}</div>'


def render_workflow(step: str = "idle") -> str:
    """Return HTML for the animated workflow diagram at the given pipeline step."""
    if step not in STEP_LABELS:
        step = "idle"

    status = STEP_LABELS[step]

    return f"""{_BASE_CSS}
<div class="wf-wrap">
  <div class="wf-status">{status}</div>
  <div class="wf-flow">
    {_render_node("user", step)}
    <span class="{_arrow_class("user", "customer", step)}">→</span>
    {_render_node("customer", step)}
    <span class="{_arrow_class("customer", "registry", step)}">→</span>
    {_render_node("registry", step)}
    <span class="{_arrow_class("registry", "law", step)}">→</span>
    {_render_node("law", step)}
    <span class="{_arrow_class("law", "tax", step)}">→</span>
    <div class="wf-parallel">
      <div class="wf-parallel-bracket">parallel (Send API)</div>
      {_render_node("tax", step)}
      {_render_node("compliance", step)}
    </div>
    <span class="{_arrow_class("compliance", "response", step)}">→</span>
    {_render_node("response", step)}
  </div>
</div>"""
