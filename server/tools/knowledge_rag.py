import os
import chromadb
from chromadb.utils import embedding_functions
from server.utils.logger import get_logger

logger = get_logger(__name__)

# Use a lightweight embedding model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHROMA_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chroma_db")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)

def initialize_knowledge_base():
    """Reads txt files from data/ and loads them into Chroma."""
    try:
        collection = client.get_or_create_collection(
            name="travel_knowledge",
            embedding_function=sentence_transformer_ef
        )
        
        # If collection already has items, we assume it's initialized (for simplicity)
        if collection.count() > 0:
            logger.info("Knowledge Base already initialized.")
            return

        logger.info("Initializing Knowledge Base (RAG) from data/ ...")
        if not os.path.exists(DATA_DIR):
            logger.warning("Knowledge base data directory not found: %s", DATA_DIR)
            return
            
        docs = []
        ids = []
        
        for filename in os.listdir(DATA_DIR):
            if filename.endswith(".txt"):
                filepath = os.path.join(DATA_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Simple chunking by paragraph
                paragraphs = content.split('\n\n')
                for i, para in enumerate(paragraphs):
                    para = para.strip()
                    if len(para) > 20:
                        docs.append(para)
                        ids.append(f"{filename}_{i}")
                        
        if docs:
            collection.add(
                documents=docs,
                ids=ids
            )
            logger.info("Added %s chunks to Knowledge Base.", len(docs))
        else:
            logger.warning("No knowledge documents were found to index.")
            
    except Exception as e:
        logger.error("Error initializing RAG: %s", e)

# Call it once when module is loaded
initialize_knowledge_base()

def query_knowledge(query: str, n_results: int = 2) -> dict:
    """Retrieve relevant context for a travel query."""
    try:
        collection = client.get_collection(
            name="travel_knowledge",
            embedding_function=sentence_transformer_ef
        )
        
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if results and results['documents'] and len(results['documents'][0]) > 0:
            return {
                "success": True,
                "context": "\n".join(results['documents'][0])
            }
            
        return {
            "success": False,
            "error": "No relevant information found."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
