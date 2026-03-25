import os
import sys
from dotenv import load_dotenv

# Adding root to path to allow importing from triggers package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from triggers.workflow_client import WorkflowClient

load_dotenv()

def trigger_embeddings(query: str = "What is a vector database?"):
    """
    Triggers the 'Embeddings' n8n workflow.
    """
    base_url = os.getenv("N8N_BASE_URL", "http://localhost:5678/api/v1")
    webhook_url = f"{base_url.replace('/api/v1', '')}/webhook/embeddings"
    verify_ssl = os.getenv("N8N_SSL_VERIFY", "true").lower() == "true"
    
    client = WorkflowClient(webhook_url, verify_ssl=verify_ssl)
    
    print(f"Goal: Generate embeddings for: '{query}'")
    
    try:
        result = client.post(data={"text": query})
        
        # Extract the vector depending on response format
        vector = []
        if isinstance(result, list) and len(result) > 0:
            vector = result[0].get("vector", [])
        elif isinstance(result, dict):
            vector = result.get("vector", [])
        else:
            print(f"Unexpected response format: {result}")
            
        print(f"Generated vector length: {len(vector)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    user_query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is a vector database?"
    trigger_embeddings(user_query)
