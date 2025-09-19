"""
FAISS warmup module for RAG system.
Provides background warmup functionality to optimize first-time FAISS creation.
"""

import threading
import time
import gc
import logging
from mcp_server.llm import embeddings

# Setup logger
logger = logging.getLogger('mcp_server.tools.lng_llm.rag.add_data.warmup')

# Global variables for warmup
_warmup_completed = False
_warmup_thread = None
FAISS = None


def faiss_warmup_worker():
    """Background thread worker for FAISS warmup using manual index creation."""
    global _warmup_completed
    
    try:
        logger.info("Starting FAISS warmup thread - bypassing LangChain wrapper...")
        
        # Step 1: Warm up Azure OpenAI embeddings
        logger.debug("Warming up Azure OpenAI embeddings...")
        start_time = time.time()
        embedding_instance = embeddings()
        test_embedding = embedding_instance.embed_query("FAISS warmup test")
        logger.debug(f"Azure OpenAI ready in {time.time() - start_time:.2f}s, dim={len(test_embedding)}")
        
        # Step 2: Create raw FAISS index (bypass LangChain wrapper deadlock)
        logger.debug("Creating raw FAISS index to avoid LangChain deadlock...")
        start_time = time.time()
        
        import faiss
        import numpy as np
        
        # Manual FAISS index creation
        dimension = len(test_embedding)
        index = faiss.IndexFlatL2(dimension)
        embeddings_array = np.array([test_embedding], dtype=np.float32)
        index.add(embeddings_array)
        
        logger.debug(f"Raw FAISS index ready in {time.time() - start_time:.2f}s")
        
        # Step 3: Clean up and mark complete
        del index, embeddings_array, embedding_instance
        gc.collect()
        
        _warmup_completed = True
        logger.info("FAISS warmup completed! System ready for fast operations.")
        
    except Exception as e:
        logger.error(f"FAISS warmup failed: {e}", exc_info=True)
        _warmup_completed = False


def initialize_warmup():
    """Initialize FAISS import and start background warmup thread."""
    global FAISS, _warmup_thread
    
    # Import FAISS
    from langchain_community.vectorstores import FAISS
    
    # Start background warmup
    if _warmup_thread is None:
        logger.info("Starting FAISS warmup thread...")
        _warmup_thread = threading.Thread(target=faiss_warmup_worker, daemon=True)
        _warmup_thread.start()


def get_vector_store_creation_strategy(documents, embeddings_func):
    """
    Determine the best strategy for FAISS vector store creation based on warmup status.
    Returns tuple: (vector_store, operation_description)
    """
    global _warmup_completed
    
    # Check if warmup completed for fast FAISS creation
    if _warmup_completed:
        logger.info("Using pre-warmed FAISS for fast vector store creation")
        start_time = time.time()
        vector_store = FAISS.from_documents(documents, embeddings_func)
        creation_time = time.time() - start_time
        logger.info(f"FAISS created in {creation_time:.2f}s (warmup worked!)")
        operation = f"created_new_fast_{creation_time:.2f}s"
    else:
        logger.info("FAISS warmup not ready, waiting briefly...")
        # Wait up to 5 seconds for warmup to complete
        wait_time = 0
        while wait_time < 5 and not _warmup_completed:
            time.sleep(0.5)
            wait_time += 0.5
        
        start_time = time.time()
        if _warmup_completed:
            logger.info("FAISS warmup completed during wait")
            vector_store = FAISS.from_documents(documents, embeddings_func)
            creation_time = time.time() - start_time
            operation = f"created_new_after_wait_{creation_time:.2f}s"
        else:
            logger.warning("FAISS warmup still not ready, proceeding anyway")
            vector_store = FAISS.from_documents(documents, embeddings_func)
            creation_time = time.time() - start_time
            operation = f"created_new_cold_{creation_time:.2f}s"
            
        logger.info(f"FAISS created in {creation_time:.2f}s")
    
    return vector_store, operation


def get_warmup_status():
    """Get current warmup status for reporting."""
    return "completed" if _warmup_completed else "in_progress"


def get_faiss_module():
    """Get the FAISS module reference."""
    return FAISS
