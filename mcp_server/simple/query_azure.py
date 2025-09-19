from color import header
header("Query on Azure example", "yellow")

import sys
import os
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

from langchain_openai import OpenAI
from langchain_openai import AzureChatOpenAI 
from dotenv import load_dotenv

load_dotenv()

llm = AzureChatOpenAI(
    azure_deployment = os.getenv("AZURE_OPENAI_API_DEPLOYMENT"),
    api_version      = os.getenv("AZURE_OPENAI_API_VERSION"),
    api_key          = os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint   = os.getenv("AZURE_OPENAI_ENDPOINT"),
    max_tokens       = 1000,
    temperature      = 0,
    verbose          = False,
    seed             = 1234
)

header("Query")
query = "Tell me about artificial intelligence in the style of a pirate."
print(query)

response = llm.invoke(query)
header("Response")
print(response)

header("Demonstration completed!")