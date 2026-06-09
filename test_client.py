"""End-to-end test client for the Legal Multi-Agent System.

Sends a legal question to the Customer Agent and prints the response.
"""

import asyncio
import sys

from dotenv import load_dotenv

from common.customer_client import CUSTOMER_AGENT_URL, CustomerAgentError, ask_legal_question

load_dotenv()

QUESTION = (
    "If a company breaks a contract and avoids taxes, "
    "what are the legal and regulatory consequences?"
)


async def main() -> None:
    print(f"Connecting to Customer Agent at {CUSTOMER_AGENT_URL}")
    print(f"Question: {QUESTION}")
    print("-" * 60)

    try:
        result_text, elapsed = await ask_legal_question(QUESTION)
    except CustomerAgentError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    print("RESPONSE:")
    print("=" * 60)
    print(result_text)
    print("=" * 60)
    print(f"\nLatency: {elapsed:.2f}s (end-to-end, Customer Agent → Law → specialists)")

    if "Error code: 402" in result_text:
        print()
        print("HINT: OpenRouter free credits are low. Add credits at")
        print("https://openrouter.ai/settings/credits or set in .env:")
        print("  OPENROUTER_MAX_TOKENS=512")
        print("Then restart services: ./stop_all.sh && ./start_all.sh")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
