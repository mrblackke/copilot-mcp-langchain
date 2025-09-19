from color import header
header("Chain of Thought example", "yellow")

import sys
import os
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

from langchain_openai import AzureChatOpenAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

# Azure OpenAI setup
llm = AzureChatOpenAI(
    azure_deployment = os.getenv("AZURE_OPENAI_API_DEPLOYMENT"),
    api_version      = os.getenv("AZURE_OPENAI_API_VERSION"),
    api_key          = os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint   = os.getenv("AZURE_OPENAI_ENDPOINT"),
    max_tokens       = 2000,
    temperature      = 0,
    verbose          = False,
    seed             = 1234
)

# Complex problem solver using Chain of Thought methodology
def solve_complex_problem(problem: str):
    """Solves complex problems using structured Chain of Thought approach"""
    
    prompt = PromptTemplate(
        template="""Solve the following complex problem using structured Chain of Thought methodology.

Problem: {problem}

Solution methodology:

🔍 Step 1: Problem definition
- What exactly is the problem?
- Who/what is affected?
- How serious is the problem?

📊 Step 2: Information gathering
- What facts do we know?
- What needs to be investigated additionally?
- What resources are available?

💡 Step 3: Generating solution options
- What are the possible solutions?
- Pros and cons of each option
- What resources will be required?

⚖️ Step 4: Evaluating options
- Which option is most effective?
- What are the risks of each option?
- What is easiest to implement?

✅ Step 5: Final recommendation
- Best solution option
- Action plan
- Success criteria

Answer: [Detailed step-by-step solution]""",
        input_variables=["problem"]
    )
    
    chain = prompt | llm
    response = chain.invoke({"problem": problem})
    
    return response.content

complex_problem = """
A software startup has been growing rapidly but is facing multiple challenges:
1. Customer complaints about slow response times are increasing
2. Development team is overworked and experiencing burnout
3. Server costs are rising exponentially with user growth
4. Competition is launching similar features faster
5. Budget is limited and investors want to see profitability

The company needs a comprehensive strategy to address these issues while maintaining growth.
"""

header("Problem")
print(complex_problem.strip())

header("Analysis")
solution = solve_complex_problem(complex_problem)
print(solution)

header("Demonstration completed!")

print(f"🧠 Key benefits of Chain of Thought:")
print(f"✅ Structured approach to complex problems")
print(f"✅ Transparent reasoning process")
print(f"✅ Comprehensive analysis of all aspects")
print(f"✅ Balanced consideration of options")
print(f"✅ Clear action plan with success metrics")
