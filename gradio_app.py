"""Gradio web UI for the Legal Multi-Agent System (Stage 5).

Requires backend services to be running:
    ./start_all.sh

Then launch this UI:
    uv run python gradio_app.py
"""

from __future__ import annotations

import gradio as gr

from common.customer_client import CUSTOMER_AGENT_URL, CustomerAgentError, ask_legal_question

EXAMPLE_QUESTIONS = [
    "If a company breaks a contract and avoids taxes, what are the legal consequences?",
    "Công ty vi phạm hợp đồng lao động bằng cách sa thải nhân viên không có lý do chính đáng thì phải chịu trách nhiệm pháp lý gì?",
    "A tech company shared user data without consent (GDPR violation). What are the privacy consequences?",
]


async def respond(message: str, history: list) -> str:
    """Handle a user message and return the multi-agent legal analysis."""
    if not message.strip():
        return "Please enter a legal question."

    try:
        text, elapsed = await ask_legal_question(message)
        return f"{text}\n\n---\n⏱️ Latency: {elapsed:.2f}s (Customer → Law → Tax/Compliance)"
    except CustomerAgentError as exc:
        return (
            f"**Could not reach the agent system**\n\n{exc}\n\n"
            "Start backend services first:\n"
            "```bash\n./start_all.sh\n```"
        )


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Legal Multi-Agent Assistant") as demo:
        gr.Markdown(
            f"""
# Legal Multi-Agent Assistant
Ask a legal question — your request flows through **Customer Agent → Law Agent → Tax & Compliance Agents** (A2A protocol).

**Backend:** `{CUSTOMER_AGENT_URL}` — run `./start_all.sh` before using this UI.
"""
        )

        gr.ChatInterface(
            fn=respond,
            examples=EXAMPLE_QUESTIONS,
            title=None,
            description="Educational legal analysis only — not legal advice.",
        )

    return demo


if __name__ == "__main__":
    demo = build_ui()
    demo.launch(server_name="127.0.0.1", server_port=7860)
