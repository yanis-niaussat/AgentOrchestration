import os
import sys
import json
from dotenv import load_dotenv

# Adding root to path to allow importing from triggers package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from triggers.workflow_client import WorkflowClient

# Load environment variables
load_dotenv()

def trigger_chat_prompt(query: str = "Explain prompt engineering."):
    """
    Triggers the 'Chat Prompt' n8n workflow.
    Logic: Structured prompt with System (Assistant) and Human messages.
    """
    # 1. Construct the Webhook URL
    base_url = os.getenv("N8N_BASE_URL", "http://localhost:5678/api/v1")
    webhook_url = f"{base_url.replace('/api/v1', '')}/webhook/chat-prompt"
    verify_ssl = os.getenv("N8N_SSL_VERIFY", "true").lower() == "true"
    
    # 2. Use the n8n WorkflowClient
    client = WorkflowClient(webhook_url, verify_ssl=verify_ssl)
    
    print(f"🚀 Triggering 'Chat Prompt' via n8n...")
    print(f"Query: {query}\n")
    
    try:
        # 3. POST the query to n8n
        result = client.post(data={"query": query})
        
        # 4. Display the response
        print("--- Assistant Response ---")
        if isinstance(result, list) and len(result) > 0:
            output = result[0].get("output") or result[0].get("text") or result[0]
            print(output)
        elif isinstance(result, dict):
            output = result.get("output") or result.get("text") or result
            print(output)
        else:
            print(result)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Use CLI arg for query if provided
    user_query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Explain prompt engineering."
    trigger_chat_prompt(user_query)
