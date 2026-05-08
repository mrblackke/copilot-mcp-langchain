from langchain_openai import OpenAI, OpenAIEmbeddings, AzureOpenAIEmbeddings
from langchain_openai import AzureChatOpenAI
from mcp_server.config import LLM_PROVIDER, OPENAI_API_KEY, AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_DEPLOYMENT, AZURE_OPENAI_API_EMBEDDING_DEPLOYMENT
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger('mcp_server.llm')

def llm(callbacks=None, verbose=False, **kwargs):
    if LLM_PROVIDER == "openai":
        logger.info("Using OpenAI LLM.")
        return OpenAI(
            openai_api_key=OPENAI_API_KEY,
            callbacks=callbacks,
            verbose=verbose,
            **kwargs
        )
    else:
        logger.info(f"Using Azure OpenAI LLM: {AZURE_OPENAI_API_DEPLOYMENT} at {AZURE_OPENAI_ENDPOINT} with API version {AZURE_OPENAI_API_VERSION}.")
        return AzureChatOpenAI(
            azure_deployment=AZURE_OPENAI_API_DEPLOYMENT,
            model=AZURE_OPENAI_API_DEPLOYMENT,
            api_version=AZURE_OPENAI_API_VERSION,
            api_key=AZURE_OPENAI_API_KEY,
            max_tokens=1000,
            temperature=0,
            callbacks=callbacks,
            verbose=verbose,
            seed=1234,
            **kwargs
        )

def embeddings(callbacks=None, **kwargs):
    if LLM_PROVIDER == "azure":
        logger.info("Using Azure OpenAI Embeddings.")
        
        # For Azure, we need to use the Azure OpenAI format
        return AzureOpenAIEmbeddings(
            model=AZURE_OPENAI_API_EMBEDDING_DEPLOYMENT,
            deployment=AZURE_OPENAI_API_EMBEDDING_DEPLOYMENT,
            api_version=AZURE_OPENAI_API_VERSION,
            api_key=AZURE_OPENAI_API_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
    else:
        logger.info("Using OpenAI Embeddings.")
        return OpenAIEmbeddings(
            api_key=OPENAI_API_KEY,
            **kwargs
        )