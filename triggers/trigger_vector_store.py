import os
import sys
from dotenv import load_dotenv

# Adding root to path to allow importing from triggers package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from triggers.workflow_client import WorkflowClient

load_dotenv()

def trigger_vector_store(texts: list = None):
    """
    Triggers the 'Vector Store' n8n workflow.
    """
    if texts is None:
        texts = ["LLMs generate text.", "Vector DBs store embeddings."]
        
    base_url = os.getenv("N8N_BASE_URL", "http://localhost:5678/api/v1")
    webhook_url = f"{base_url.replace('/api/v1', '')}/webhook/vector-store"
    verify_ssl = os.getenv("N8N_SSL_VERIFY", "true").lower() == "true"
    
    client = WorkflowClient(webhook_url, verify_ssl=verify_ssl)
    
    print(f"Goal: Store embeddings locally for {len(texts)} documents.")
    
    try:
        result = client.post(data={"texts": texts})
        
        print("Response from n8n vector store:", result)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Can take a single text from CLI, or default list
    if len(sys.argv) > 1:
        user_texts = [" ".join(sys.argv[1:])]
    else:
        user_texts = None
    trigger_vector_store(user_texts)
