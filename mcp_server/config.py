import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "azure")
if LLM_PROVIDER not in ["openai", "azure"]:
    raise ValueError(f"LLM_PROVIDER must be 'openai' or 'azure', got {LLM_PROVIDER}")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY is None:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

AZURE_OPENAI_API_KEY=os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION=os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_ENDPOINT=os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_DEPLOYMENT=os.getenv("AZURE_OPENAI_API_DEPLOYMENT")
AZURE_OPENAI_API_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_API_EMBEDDING_DEPLOYMENT")
if AZURE_OPENAI_API_KEY is None or \
   AZURE_OPENAI_API_VERSION is None or \
   AZURE_OPENAI_ENDPOINT is None or \
   AZURE_OPENAI_API_DEPLOYMENT is None or \
    AZURE_OPENAI_API_EMBEDDING_DEPLOYMENT is None:
    raise ValueError("One or more Azure OpenAI environment variables not found in .env")