import os
import sys
from dotenv import load_dotenv

# Adding root to path to allow importing from triggers package if run from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from triggers.workflow_client import WorkflowClient

# Load environment variables
load_dotenv()

def trigger_dynamic_prompt(topic: str = "vector databases"):
    """
    Triggers the 'Dynamic Prompt' n8n workflow.
    Logic: Formats a template locally and sends the raw prompt to n8n.
    """
    # 1. Construct the Webhook URL
    base_url = os.getenv("N8N_BASE_URL", "http://localhost:5678/api/v1")
    webhook_url = f"{base_url.replace('/api/v1', '')}/webhook/dynamic-prompt"
    verify_ssl = os.getenv("N8N_SSL_VERIFY", "true").lower() == "true"
    
    # 2. Use the n8n WorkflowClient
    client = WorkflowClient(webhook_url, verify_ssl=verify_ssl)
    
    # 3. Format prompt locally (Introducing variables)
    template = "Explain {topic} in simple terms."
    formatted_prompt = template.format(topic=topic)
    
    print(f"🚀 Triggering 'Dynamic Prompt' via n8n...")
    print(f"Topic: {topic}")
    print(f"Formatted Prompt: {formatted_prompt}\n")
    
    try:
        # 4. POST the prompt to n8n (no system_message)
        result = client.post(data={"prompt": formatted_prompt})
        
        # 5. Display the response
        print("--- Response ---")
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
    # Use CLI arg for topic if provided
    input_topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "vector databases"
    trigger_dynamic_prompt(input_topic)
