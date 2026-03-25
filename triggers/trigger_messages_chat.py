import os
import sys
import json
from dotenv import load_dotenv

# Adding root to path to allow importing from triggers package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from triggers.workflow_client import WorkflowClient

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# Mirrors the professor's role-based message pattern:
# ---------------------------------------------------------------------------

WEBHOOK_PATH = "messages-chat"

def system_message(content: str) -> dict:
    """Equivalent of SystemMessage(content="...")."""
    return {"role": "system", "content": content.strip()}

def human_message(content: str) -> dict:
    """Equivalent of HumanMessage(content="...")."""
    return {"role": "human", "content": content.strip()}

def invoke(messages: list) -> str:
    """
    Send a list of role-based messages to the n8n workflow and return the reply.
    """
    base_url = os.getenv("N8N_BASE_URL", "http://localhost:5678/api/v1")
    webhook_url = f"{base_url.replace('/api/v1', '')}/webhook/{WEBHOOK_PATH}"
    verify_ssl = os.getenv("N8N_SSL_VERIFY", "true").lower() == "true"
    
    client = WorkflowClient(webhook_url, verify_ssl=verify_ssl)

    # Build payload from the message list (last system + last human wins)
    payload = {}
    for msg in messages:
        payload[msg["role"]] = msg["content"]

    try:
        print("  Waiting for AI response …", end="", flush=True)
        resp = client.post(data=payload)
        print(" done.")

        try:
            body = resp
            if isinstance(body, list) and body:
                body = body[0]
            for key in ("output", "text", "message", "response", "content"):
                if isinstance(body, dict) and key in body:
                    return str(body[key])
            return json.dumps(body)
        except Exception:
            return str(resp)

    except Exception as exc:
        print(f"\n  [error] {exc}")
        return None

def main():
    print("=" * 60)
    print("  MESSAGES CHAT — Role-based AI interaction via n8n")
    print("=" * 60)

    # Collect the system persona
    default_system = "You explain concepts briefly and clearly."
    try:
        system_input = input(
            f"\nSystem message (press Enter for default):\n"
            f"  [{default_system}]\n> "
        ).strip()
    except EOFError:
        return
        
    system_content = system_input if system_input else default_system

    # Collect the human question
    try:
        question = input("\nYour question:\n> ").strip()
    except EOFError:
        return
        
    if not question:
        print("No question provided. Exiting.")
        return

    # Build the message list
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
