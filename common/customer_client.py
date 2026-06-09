"""Client helper for sending questions to the Customer Agent via A2A."""

from __future__ import annotations

import os
import time
from uuid import uuid4

import httpx
from dotenv import load_dotenv

load_dotenv()

CUSTOMER_AGENT_URL = os.getenv("CUSTOMER_AGENT_URL", "http://localhost:10100")


class CustomerAgentError(Exception):
    """Raised when the Customer Agent cannot be reached or returns an error."""


async def ask_legal_question(
    question: str,
    *,
    customer_agent_url: str | None = None,
) -> tuple[str, float]:
    """Send a question to the Customer Agent and return (response_text, latency_seconds)."""
    if not question.strip():
        raise CustomerAgentError("Question cannot be empty.")

    base_url = customer_agent_url or CUSTOMER_AGENT_URL
    card_url = f"{base_url}/.well-known/agent.json"

    async with httpx.AsyncClient(timeout=300.0) as http_client:
        try:
            card_resp = await http_client.get(card_url)
            card_resp.raise_for_status()
        except Exception as exc:
            raise CustomerAgentError(
                f"Could not reach Customer Agent at {card_url}. "
                "Make sure all services are running (./start_all.sh)."
            ) from exc

        from a2a.client import A2AClient
        from a2a.types import (
            AgentCard,
            Message,
            MessageSendParams,
            Part,
            Role,
            SendMessageRequest,
            TextPart,
        )

        agent_card = AgentCard.model_validate(card_resp.json())
        client = A2AClient(httpx_client=http_client, agent_card=agent_card)

        message = Message(
            role=Role.user,
            parts=[Part(root=TextPart(text=question))],
            message_id=str(uuid4()),
        )
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(message=message),
        )

        start = time.perf_counter()
        response = await client.send_message(request)
        elapsed = time.perf_counter() - start

        result_text = _extract_response_text(response)
        if not result_text:
            raise CustomerAgentError(f"No text response received: {response!r}")

        return result_text, elapsed


def _extract_response_text(response: object) -> str:
    """Parse text from an A2A SendMessage response."""
    result_text = ""
    if not hasattr(response, "root"):
        return result_text

    root = response.root
    if not hasattr(root, "result"):
        return result_text

    result = root.result

    if hasattr(result, "artifacts") and result.artifacts:
        for artifact in result.artifacts:
            for part in artifact.parts:
                p = part.root if hasattr(part, "root") else part
                if hasattr(p, "text"):
                    result_text += p.text
    elif (
        hasattr(result, "status")
        and result.status
        and getattr(result.status, "state", None) == "failed"
        and getattr(result.status, "message", None)
    ):
        msg = result.status.message
        if hasattr(msg, "parts") and msg.parts:
            for part in msg.parts:
                p = part.root if hasattr(part, "root") else part
                if hasattr(p, "text"):
                    result_text += p.text
    elif hasattr(result, "parts") and result.parts:
        for part in result.parts:
            p = part.root if hasattr(part, "root") else part
            if hasattr(p, "text"):
                result_text += p.text

    return result_text
