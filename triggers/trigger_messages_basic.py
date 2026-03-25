import os
import sys
import json
from dotenv import load_dotenv

# Adding root to path to allow importing from triggers package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from triggers.workflow_client import WorkflowClient

# Load environment variables
load_dotenv()

WEBHOOK_PATH = "messages-basic"

def human_message(content: str) -> dict:
    """Build a HumanMessage-style dict"""
    return {"role": "human", "content": content.strip()}

def invoke(message: dict) -> str:
    """
    Send a single HumanMessage to the n8n workflow and return the AI reply.
    """
    base_url = os.getenv("N8N_BASE_URL", "http://localhost:5678/api/v1")
    webhook_url = f"{base_url.replace('/api/v1', '')}/webhook/{WEBHOOK_PATH}"
    verify_ssl = os.getenv("N8N_SSL_VERIFY", "true").lower() == "true"
    
    client = WorkflowClient(webhook_url, verify_ssl=verify_ssl)

    try:
        print("  Waiting for AI response …", end="", flush=True)
        resp = client.post(data=message)
        print(" done.")

        # n8n (responseMode: lastNode) returns the agent output in the body
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
    print("  MESSAGES BASIC — Single-turn AI chat via n8n")
    print("=" * 60)

    try:
        question = input("\nAsk anything:\n> ").strip()
    except EOFError:
        return
        
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
