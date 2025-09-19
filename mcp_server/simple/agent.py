from color import header 
header("Agent example", "yellow")

import sys
import os
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

from langchain_openai import AzureChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.tools import tool
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import hashlib
import re

load_dotenv()

# Azure OpenAI setup
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

# Tool 1: Accurate character count (including spaces and special characters)
@tool
def count_characters(text: str) -> str:
    """Accurately counts the number of characters in text, including spaces and special characters."""
    count = len(text)
    return f"Exact character count in text: {count}"

# Tool 2: MD5 hash generation
@tool  
def generate_md5_hash(text: str) -> str:
    """Generates MD5 hash for text. LLM cannot accurately compute hash."""
    md5_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
    return f"MD5 hash of text: {md5_hash}"

# Tool 3: Precise regex search and count
@tool
def regex_count(text: str, pattern: str) -> str:
    """Finds and accurately counts occurrences of regular expression in text."""
    try:
        matches = re.findall(pattern, text)
        count = len(matches)
        return f"Found {count} occurrences of pattern '{pattern}' in text. Matches found: {matches[:10]}{'...' if len(matches) > 10 else ''}"
    except re.error as e:
        return f"Regular expression error: {e}"

# Create list of tools
tools = [count_characters, generate_md5_hash, regex_count]

# Create prompt for agent
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an assistant who can work with text using precise tools.
    
You have 3 tools available:
1. count_characters - for accurate character counting in text
2. generate_md5_hash - for generating MD5 hash of text  
3. regex_count - for searching and counting regular expressions in text

Always use these tools for precise calculations, don't try to guess!"""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

# Create agent
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Test text with complex content for comprehensive analysis
test_text = """Hello! This comprehensive text contains various elements for analysis:
Numbers: 42, 123, 789, 2024
Email addresses: john.doe@company.com, support@example.org, info@test.co.uk
URLs: https://www.example.com, http://api.service.net/v1/data
Phone numbers: +1-555-123-4567, (555) 987-6543
Special characters: !@#$%^&*()_+-=[]{}|;:,.<>?
Mixed content: API_KEY_123, user_id_456, session_token_abc789
Dates: 2024-01-15, 12/25/2023, Jan 1st 2024"""

header("Complex test text for analysis")
print(test_text)

prompt = f"""Analyze this text using all available tools:
    
Text: '{test_text}'
    
Tasks:
    1. Count the total characters in the text
    2. Generate MD5 hash of the text
    3. Count email addresses in the text (pattern: [a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{{2,6}})
    4. Count URLs in the text (pattern: https?://[^\\s]+)
    5. Count phone numbers in the text (pattern: \\+?\\d[\\d\\s-]{{7,15}})

    Please use the tools to get exact results."""

header("Prompt sent to agent")
print(prompt)

header("Analysis demonstration")

result = agent_executor.invoke({
    "input": prompt
})

header("Analysis results")

print(result['output'])

header("Demonstration completed!")

print(f"🤖 Agent capabilities demonstrated:")
print(f"✅ Precise character counting (spaces, unicode, special chars)")
print(f"✅ Cryptographic hash generation (MD5)")
print(f"✅ Complex regex pattern matching and counting")
print(f"✅ Multi-step analysis coordination")
print(f"✅ Tool combination for comprehensive results")
