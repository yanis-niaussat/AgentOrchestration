import os
import json
import requests
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# Mirrors the professor's multi-turn conversation pattern:
#
#   conversation = [
#       HumanMessage(content="What is RAG?"),
#       AIMessage(content="RAG combines retrieval with generation."),
#       HumanMessage(content="Why is it useful?")
#   ]
#   response = llm.invoke(conversation)
#
# The full message list is POSTed to n8n as a JSON array.
# A Code node in the workflow formats the history, then the AI Agent replies.
# ---------------------------------------------------------------------------

WEBHOOK_PATH = "conversation"


def human_message(content: str) -> dict:
    """Equivalent of HumanMessage(content="...")."""
    return {"role": "human", "content": content.strip()}


def ai_message(content: str) -> dict:
    """Equivalent of AIMessage(content="...")."""
    return {"role": "ai", "content": content.strip()}


def invoke(conversation: list, timeout: int = 180) -> Optional[str]:
    """
    Send the full conversation list to n8n and return the AI reply.
    Equivalent to:  llm.invoke([HumanMessage(...), AIMessage(...), HumanMessage(...)])
    """
    base_url = os.getenv("N8N_BASE_URL", "http://localhost:5678").rstrip("/")
    webhook_url = f"{base_url}/webhook/{WEBHOOK_PATH}"

    try:
        print("  Waiting for AI response …", end="", flush=True)
        # Wrap in an object so n8n can access it as $json.body.messages
        resp = requests.post(webhook_url, json={"messages": conversation}, timeout=timeout)
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


def print_conversation(conversation: list):
    """Pretty-print the conversation history."""
    label = {"human": "Human", "ai": "AI"}
    for msg in conversation:
        role = label.get(msg["role"], msg["role"].capitalize())
        print(f"  [{role}] {msg['content']}")


# ---------------------------------------------------------------------------
# Main — interactive multi-turn session
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  CONVERSATION — Multi-turn AI chat via n8n")
    print("  Type 'quit' to exit, 'reset' to start a new conversation.")
    print("=" * 60)

    conversation = []

    while True:
        user_input = input("\nYou: ").strip()

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break
        if user_input.lower() == "reset":
            conversation = []
            print("  [Conversation reset]")
            continue

        # Append the new HumanMessage — mirrors: HumanMessage(content="...")
        conversation.append(human_message(user_input))

        # Invoke — mirrors: llm.invoke(conversation)
        response_text = invoke(conversation)

        if response_text:
            # Append the AIMessage to keep history growing
            # mirrors: AIMessage(content=response.content)
            conversation.append(ai_message(response_text))
            print(f"\nAI: {response_text}")
        else:
            # Remove the last human message so the turn can be retried
            conversation.pop()
            print("  No response received. Please try again.")


if __name__ == "__main__":
    main()
