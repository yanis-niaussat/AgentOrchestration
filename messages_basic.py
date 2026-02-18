import os
import json
import requests
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# Mirrors the professor's single-turn HumanMessage pattern:
#
#   llm.invoke([HumanMessage(content="What is an embedding?")])
#
# Here the "LLM" is the n8n workflow (messages_basic workflow), and the
# HumanMessage is the JSON body we POST to its webhook.
# ---------------------------------------------------------------------------

WEBHOOK_PATH = "messages-basic"


def human_message(content: str) -> dict:
    """
    Build a HumanMessage-style dict — the equivalent of:
        HumanMessage(content="...")
    """
    return {"role": "human", "content": content.strip()}


def invoke(message: dict, timeout: int = 180) -> Optional[str]:
    """
    Send a single HumanMessage to the n8n workflow and return the AI reply.
    Equivalent to:  llm.invoke([HumanMessage(content="...")])
    """
    base_url = os.getenv("N8N_BASE_URL", "http://localhost:5678").rstrip("/")
    webhook_url = f"{base_url}/webhook/{WEBHOOK_PATH}"

    try:
        print("  Waiting for AI response …", end="", flush=True)
        resp = requests.post(webhook_url, json=message, timeout=timeout)
        print(" done.")
        resp.raise_for_status()

        # n8n (responseMode: lastNode) returns the agent output in the body
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
    print("  MESSAGES BASIC — Single-turn AI chat via n8n")
    print("=" * 60)

    question = input("\nAsk anything:\n> ").strip()
    if not question:
        print("No question provided. Exiting.")
        return

    # Build the HumanMessage and invoke the LLM (n8n workflow)
    msg = human_message(question)
    print(f"\n[HumanMessage] {msg['content']}\n")

    response_text = invoke(msg)

    print("=" * 60)
    print("  AI RESPONSE")
    print("=" * 60)
    if response_text:
        print(f"\n{response_text}\n")
    else:
        print("No response received.")


if __name__ == "__main__":
    main()
