import os
import json
import requests
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# Mirrors the professor's role-based message pattern:
#
#   messages = [
#       SystemMessage(content="You explain concepts briefly."),
#       HumanMessage(content="What is a vector database?")
#   ]
#   response = llm.invoke(messages)
#
# Here the message list is POSTed to the n8n webhook as JSON.
# The system message is wired into the AI Agent's systemMessage field,
# and the human message becomes the prompt text.
# ---------------------------------------------------------------------------

WEBHOOK_PATH = "messages-chat"


def system_message(content: str) -> dict:
    """Equivalent of SystemMessage(content="...")."""
    return {"role": "system", "content": content.strip()}


def human_message(content: str) -> dict:
    """Equivalent of HumanMessage(content="...")."""
    return {"role": "human", "content": content.strip()}


def invoke(messages: list, timeout: int = 180) -> Optional[str]:
    """
    Send a list of role-based messages to the n8n workflow and return the reply.
    Equivalent to:  llm.invoke([SystemMessage(...), HumanMessage(...)])

    The payload shape:
        {
            "system": "You explain concepts briefly.",
            "human":  "What is a vector database?"
        }
    """
    base_url = os.getenv("N8N_BASE_URL", "http://localhost:5678").rstrip("/")
    webhook_url = f"{base_url}/webhook/{WEBHOOK_PATH}"

    # Build payload from the message list (last system + last human wins)
    payload = {}
    for msg in messages:
        payload[msg["role"]] = msg["content"]

    try:
        print("  Waiting for AI response …", end="", flush=True)
        resp = requests.post(webhook_url, json=payload, timeout=timeout)
        print(" done.")
        resp.raise_for_status()

        try:
            body = resp.json()
            if isinstance(body, list) and body:
                body = body[0]
            for key in ("output", "text", "message", "response", "content"):
                if isinstance(body, dict) and key in body:
                    return str(body[key])
            return json.dumps(body)
        except Exception:
            return resp.text

    except Exception as exc:
        print(f"\n  [error] {exc}")
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  MESSAGES CHAT — Role-based AI interaction via n8n")
    print("=" * 60)

    # Collect the system persona
    default_system = "You explain concepts briefly and clearly."
    system_input = input(
        f"\nSystem message (press Enter for default):\n"
        f"  [{default_system}]\n> "
    ).strip()
    system_content = system_input if system_input else default_system

    # Collect the human question
    question = input("\nYour question:\n> ").strip()
    if not question:
        print("No question provided. Exiting.")
        return

    # Build the message list — mirrors the professor's pattern exactly
    messages = [
        system_message(system_content),
        human_message(question),
    ]

    print(f"\n[SystemMessage] {messages[0]['content']}")
    print(f"[HumanMessage]  {messages[1]['content']}\n")

    response_text = invoke(messages)

    print("=" * 60)
    print("  AI RESPONSE")
    print("=" * 60)
    if response_text:
        print(f"\n{response_text}\n")
    else:
        print("No response received.")


if __name__ == "__main__":
    main()
