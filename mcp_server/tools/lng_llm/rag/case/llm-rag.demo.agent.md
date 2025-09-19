## Info
- This case demonstrates complete RAG workflow: adding documents to vector database and performing intelligent search with LLM-powered answers

## How to ask for demo in chat  
Use this case to make demo:
```
Show me demo from file:
Create RAG system with animal knowledge base and ask questions about cats, dogs, and programming.
```

## 🤖 AI Instructions
1. **Create Prompt Template**: Use `lng_llm_prompt_template` to save RAG response template
2. **Add Animal Knowledge**: Use `lng_llm_rag_add_data` to populate vector database with animal facts
3. **Add Programming Knowledge**: Add Python programming information to the same database
4. **Search and Answer**: Use `lng_llm_rag_search` to ask questions and get LLM responses with context

**Key Features**: Vector search, context retrieval, LLM-powered answers, multi-domain knowledge

## Important
- Creates FAISS vector database in memory using embeddings
- Supports 9 different text splitter types
- Default splitter: RecursiveCharacterTextSplitter (1000 chunk_size, 200 overlap)
- Each call adds documents to existing vector store or creates new one

## Scenario
Create knowledge base with animal facts and programming info, then ask questions and get intelligent answers using vector search + LLM processing.

## Step 1: Create Prompt Template
```json
{
  "command": "save",
  "template_name": "rag_demo", 
  "template": "Based on the following context, provide a helpful and accurate answer to the question.\n\nContext:\n{context}\n\nQuestion: {query}\n\nAnswer:"
}
```

## Step 2: Add Animal Knowledge
```json
{
  "input_text": "A cat is a domestic animal of the feline family. Cats love to sleep and play. They are independent creatures that can live both indoors and outdoors. Cats are excellent hunters and have great night vision.",
  "metadata": {
    "source": "animal_facts",
    "category": "cats"
  }
}
```

## Step 3: Add More Animal Facts
```json
{
  "input_text": "A dog is a human's best friend. Dogs are loyal, protective, and social animals. They guard the house and love to walk with their owners. Dogs come in many breeds with different sizes and temperaments.",
  "metadata": {
    "source": "animal_facts",
    "category": "dogs"
  }
}
```

## Step 4: Add Programming Knowledge
```json
{
  "input_text": "Python is a popular programming language known for its simplicity and readability. It's excellent for beginners and widely used in data science, web development, and automation. Python uses indentation for code structure and has extensive library support.",
  "metadata": {
    "source": "programming_facts", 
    "category": "python"
  }
}
```

## Step 5: Search About Animals
```json
{
  "query": "What do you know about cats and dogs as pets?",
  "prompt_template": "rag_demo",
  "k": 3
}
```

## Step 6: Search About Programming
```json
{
  "query": "Tell me about Python programming language",
  "prompt_template": "rag_demo",
  "k": 2
}
```