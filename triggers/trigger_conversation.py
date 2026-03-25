import os
import sys
import json
import uuid
from dotenv import load_dotenv

# Adding root to path to allow importing from triggers package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from triggers.workflow_client import WorkflowClient

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# Mirrors the professor's multi-turn conversation pattern:
# ---------------------------------------------------------------------------

WEBHOOK_PATH = "conversation"

def human_message(content: str) -> dict:
    """Equivalent of HumanMessage(content="...")."""
    return {"role": "human", "content": content.strip()}

def ai_message(content: str) -> dict:
    """Equivalent of AIMessage(content="...")."""
    return {"role": "ai", "content": content.strip()}

def invoke(conversation: list, session_id: str) -> str:
    """
    Send the full conversation list and a unique session ID to n8n and return the AI reply.
    """
    base_url = os.getenv("N8N_BASE_URL", "http://localhost:5678/api/v1")
    webhook_url = f"{base_url.replace('/api/v1', '')}/webhook/{WEBHOOK_PATH}"
    verify_ssl = os.getenv("N8N_SSL_VERIFY", "true").lower() == "true"
    
    client = WorkflowClient(webhook_url, verify_ssl=verify_ssl)

    try:
        print("  Waiting for AI response …", end="", flush=True)
        resp = client.post(data={"messages": conversation, "sessionId": session_id})
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

def print_conversation(conversation: list):
    """Pretty-print the conversation history."""
    label = {"human": "Human", "ai": "AI"}
    for msg in conversation:
        role = label.get(msg["role"], msg["role"].capitalize())
        print(f"  [{role}] {msg['content']}")

def main():
    print("=" * 60)
    print("  CONVERSATION — Multi-turn AI chat via n8n")
    print("  Type 'quit' to exit, 'reset' to start a new conversation.")
    print("=" * 60)

    conversation = []
    # Generate a unique session ID for the conversation thread
    session_id = uuid.uuid4().hex

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except EOFError:
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break
        if user_input.lower() == "reset":
            conversation = []
            session_id = uuid.uuid4().hex # New session ID for new conversation
            print(f"  [Conversation reset - New Session ID: {session_id}]")
            continue

        conversation.append(human_message(user_input))

        response_text = invoke(conversation, session_id)

        if response_text:
            conversation.append(ai_message(response_text))
            print(f"\nAI: {response_text}")
        else:
            conversation.pop()
            print("  No response received. Please try again.")

if __name__ == "__main__":
    main()
