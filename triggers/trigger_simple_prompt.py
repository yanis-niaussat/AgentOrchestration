import os
import sys
from dotenv import load_dotenv

# Adding root to path to allow importing from triggers package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from triggers.workflow_client import WorkflowClient

# Load environment variables
load_dotenv()

def trigger_simple_prompt():
    """Triggers the 'Simple Prompt' n8n workflow via GET."""
    # 1. Construct the Webhook URL
    base_url = os.getenv("N8N_BASE_URL", "http://localhost:5678/api/v1")
    webhook_url = f"{base_url.replace('/api/v1', '')}/webhook/simple-prompt"
    verify_ssl = os.getenv("N8N_SSL_VERIFY", "true").lower() == "true"
    
    # 2. Use the n8n WorkflowClient
    client = WorkflowClient(webhook_url, verify_ssl=verify_ssl)
    
    print(f"🚀 Triggering 'Simple Prompt' via GET...")
    
    try:
        # 3. Trigger workflow via GET
        result = client.get()
        
        print("\n--- Response ---")
        if isinstance(result, list) and len(result) > 0:
            print(result[0].get("output") or result[0].get("text") or result[0])
        elif isinstance(result, dict):
            print(result.get("output") or result.get("text") or result)
        else:
            print(result)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    trigger_simple_prompt()
