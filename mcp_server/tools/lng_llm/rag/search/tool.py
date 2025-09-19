import json
import mcp.types as types
from mcp_server.state_manager import state_manager
from mcp_server.file_state_manager import prompts_manager
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from mcp_server.llm import llm

async def tool_info() -> dict:
    """Returns information about the lng_rag_search tool."""
    return {
        "description": """Searches the RAG (Retrieval Augmented Generation) vector database with a query and returns relevant results.

**Parameters:**
- `query` (string, required): The search query to find relevant documents in the vector database
- `k` (number, optional): The number of most relevant documents to retrieve (default: 3)
- `threshold` (number, optional): Relevance threshold for filtering results. Documents with similarity score above this threshold will be filtered out. Lower values mean stricter filtering (default: 0.5)
- `max_chunks` (number, optional): Maximum number of chunks to include in the context for LLM response. If not specified, uses all documents that pass the threshold filter (default: uses all relevant documents)
- `prompt_template` (string, required): Name of the prompt template to use with the retrieved documents
  The template should contain placeholders for `{context}` and `{query}` to format the response.
  Use lng_llm_prompt_template tool first to create templates.

**Example Usage:**
- First, create a prompt template: lng_llm_prompt_template with command="save"
- Then search for documents related to a specific topic
- Specify which template to use: prompt_template="scientific" or prompt_template="default_rag"
- Optionally adjust threshold: threshold=0.3 for stricter filtering, threshold=0.7 for more lenient filtering
- Optionally limit chunks: max_chunks=5 to limit context size for better LLM performance
- The tool will retrieve relevant documents and generate a response using the specified template
- Templates must contain {context} and {query} placeholders for proper RAG functionality

This tool works together with lng_rag_add_data and lng_llm_prompt_template to provide a complete RAG workflow.""",
        "schema": {
            "type": "object",
            "required": ["query", "prompt_template"],
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant documents in the vector database",
                },
                "k": {
                    "type": "number",
                    "description": "The number of most relevant documents to retrieve (default: 3)",
                },
                "threshold": {
                    "type": "number",
                    "description": "Relevance threshold for filtering results. Documents with similarity score above this threshold will be filtered out (default: 0.5)",
                },
                "max_chunks": {
                    "type": "number",
                    "description": "Maximum number of chunks to include in the context for LLM response (default: uses all relevant documents)",
                },
                "prompt_template": {
                    "type": "string",
                    "description": "Name of the prompt template to use with the retrieved documents (required)",
                }
            },
        }
    }

async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    """Searches the RAG vector database with a query."""
    query = parameters.get("query", None)
    if not query:
        error_output = {
            "error": "missing_parameter",
            "message": "'query' parameter is required",
            "required_parameter": "query"
        }
        return [types.TextContent(type="text", text=json.dumps(error_output, ensure_ascii=False, indent=2))]
    
    k = parameters.get("k", 3)
    threshold = parameters.get("threshold", 0.5)
    max_chunks = parameters.get("max_chunks", None)  # If None, use all relevant documents
    prompt_template_name = parameters.get("prompt_template")
    
    if not prompt_template_name:
        error_output = {
            "error": "missing_parameter",
            "message": "'prompt_template' parameter is required",
            "required_parameter": "prompt_template",
            "suggestion": "Use lng_llm_prompt_template tool first to create a template, then specify its name here"
        }
        return [types.TextContent(type="text", text=json.dumps(error_output, ensure_ascii=False, indent=2))]
    
    try:
        # Get vector store from state
        vector_store = state_manager.get("vector_store")
        
        if vector_store is None:
            error_output = {
                "error": "no_vector_database",
                "message": "No vector database found",
                "suggestion": "Please add documents first using lng_llm_rag_add_data"
            }
            return [types.TextContent(type="text", text=json.dumps(error_output, ensure_ascii=False, indent=2))]
        
        # Initialize embeddings
        embeddings = OpenAIEmbeddings()
        
        # Perform similarity search
        results = vector_store.similarity_search_with_score(query, k=k)
        
        if not results:
            no_results_output = {
                "message": "No relevant documents found for your query",
                "query": query,
                "search_parameters": {
                    "k": k,
                    "threshold": threshold,
                    "max_chunks": max_chunks
                },
                "retrieved_documents": [],
                "response": None
            }
            return [types.TextContent(type="text", text=json.dumps(no_results_output, ensure_ascii=False, indent=2))]
        
        # Filter results by threshold and format
        all_retrieved_docs = []
        relevant_docs = []
        
        for doc, score in results:
            doc_info = {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "relevance_score": float(score),
                "similarity": 1 - float(score),  # Convert to similarity (higher is better)
                "passed_threshold": float(score) < threshold
            }
            all_retrieved_docs.append(doc_info)
            
            # Include in context only if passes threshold
            if float(score) < threshold:
                relevant_docs.append(doc_info)
        
        # Apply max_chunks limit if specified
        context_docs = relevant_docs
        if max_chunks is not None and len(relevant_docs) > max_chunks:
            context_docs = relevant_docs[:max_chunks]
        
        # Check if we have any documents for context after filtering
        if not context_docs:
            filtered_results_output = {
                "message": "No documents passed the relevance threshold",
                "query": query,
                "search_parameters": {
                    "k": k,
                    "threshold": threshold,
                    "max_chunks": max_chunks
                },
                "documents_retrieved": len(all_retrieved_docs),
                "documents_after_threshold": len(relevant_docs),
                "documents_used_for_context": len(context_docs),
                "retrieved_documents": all_retrieved_docs,
                "response": None,
                "suggestion": "Try increasing the threshold value (e.g., 0.7 or 0.8) for more lenient filtering"
            }
            return [types.TextContent(type="text", text=json.dumps(filtered_results_output, ensure_ascii=False, indent=2))]
        
        # Get saved prompt template by name
        saved_template = prompts_manager.get(prompt_template_name, extension=".prompt")
        
        if saved_template is None:
            # If specified template is not found, return error with available templates
            available_templates = prompts_manager.list_files(extension=".prompt")
            error_output = {
                "error": "template_not_found",
                "message": f"Prompt template '{prompt_template_name}' not found",
                "requested_template": prompt_template_name,
                "available_templates": available_templates if available_templates else [],
                "suggestion": "Use lng_llm_prompt_template to create new templates"
            }
            return [types.TextContent(type="text", text=json.dumps(error_output, ensure_ascii=False, indent=2))]
            
        # Create a context from documents that will be used for LLM response
        context = "\n\n".join([f"Document {i+1}:\n{doc['content']}" for i, doc in enumerate(context_docs)])
        
        # Create prompt template with the input variables
        prompt_template = PromptTemplate(
            input_variables=["context", "query"],
            template=saved_template
        )
        
        # Format the prompt with the provided parameters
        prompt = prompt_template.format(context=context, query=query)
        
        model = llm()

        # Get response from LLM
        response = model.invoke(prompt)
        
        # Check if the response has content and convert it to string
        if hasattr(response, "content"):
            response_text = response.content
        else:
            response_text = str(response)
        
        # Add retrieved documents and LLM response to output
        output = {
            "response": response_text,
            "search_parameters": {
                "k": k,
                "threshold": threshold,
                "max_chunks": max_chunks
            },
            "documents_retrieved": len(all_retrieved_docs),
            "documents_after_threshold": len(relevant_docs),
            "documents_used_for_context": len(context_docs),
            "retrieved_documents": all_retrieved_docs
        }
        
        return [types.TextContent(type="text", text=json.dumps(output, ensure_ascii=False, indent=2))]
            
    except Exception as e:
        error_output = {
            "error": "exception",
            "message": f"Error searching vector database: {str(e)}",
            "exception_type": type(e).__name__,
            "query": query
        }
        return [types.TextContent(type="text", text=json.dumps(error_output, ensure_ascii=False, indent=2))]
