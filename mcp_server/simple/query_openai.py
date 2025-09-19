from color import header
header("Query on OpenAI example", "yellow")

import sys
import os
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

from langchain_openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

llm = OpenAI(openai_api_key=os.getenv("OPENAI_API_KEY"))

header("Query")
query = "Tell me about artificial intelligence in the style of a pirate."
print(query)

response = llm.invoke(query)
header("Response")
print(response)

header("Demonstration completed!")