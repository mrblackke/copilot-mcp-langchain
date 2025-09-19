import mcp.types as types
from langchain.prompts import PromptTemplate
from mcp_server.file_state_manager import prompts_manager
from mcp_server.llm import llm
import logging

logger = logging.getLogger('mcp_server.tools.lng_llm_prompt_template')


async def tool_info() -> dict:
    """Returns information about the lng_llm_prompt_template tool."""
    return {
        "description": """Unified prompt template management tool with file-based storage.

**Commands:**
- `save` - Save a prompt template to filesystem
- `use` - Use a saved prompt template with parameters  
- `list` - List all saved prompt templates

**Parameters for save:**
- `command` (string, required): "save"
- `template` (string, required): The prompt template with placeholders in {name} format
- `template_name` (string, optional): Template name (default: "default")

**Parameters for use:**
- `command` (string, required): "use"
- `template_name` (string, optional): Template name to use (default: "default")
- Any key-value pairs that match the placeholders in your template

**Parameters for list:**
- `command` (string, required): "list"

**Example Usage:**
1. Save: `{"command": "save", "template_name": "pirate", "template": "Tell me about {topic} in the style of {style}."}`
2. Use: `{"command": "use", "template_name": "pirate", "topic": "AI", "style": "a pirate"}`
3. List: `{"command": "list"}`

Templates are stored in `mcp_server/config/prompt/` directory as `.prompt` files.""",
        "schema": {
            "type": "object",
            "required": ["command"],
            "properties": {
                "command": {
                    "type": "string",
                    "enum": ["save", "use", "list"],
                    "description": "The operation to perform: save, use, or list templates"
                },
                "template_name": {
                    "type": "string",
                    "description": "Template name (optional, default: 'default')"
                },
                "template": {
                    "type": "string",
                    "description": "The prompt template to save (required for save command)"
                }
            },
            "additionalProperties": {
                "type": "string",
                "description": "Additional parameters for template placeholders (for use command)"
            }
        }
    }


async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    """Unified prompt template management tool."""
    
    command = parameters.get("command")
    if not command:
        return [types.TextContent(type="text", text="Error: 'command' parameter is required. Use 'save', 'use', or 'list'.")]
    
    if command == "save":
        return await _save_template(parameters)
    elif command == "use":
        return await _use_template(parameters)
    elif command == "list":
        return await _list_templates(parameters)
    else:
        return [types.TextContent(type="text", text=f"Error: Unknown command '{command}'. Use 'save', 'use', or 'list'.")]


async def _save_template(parameters: dict) -> list[types.Content]:
    """Save a prompt template to filesystem."""
    template_text = parameters.get("template")
    if not template_text:
        return [types.TextContent(type="text", text="Error: 'template' parameter is required for save command.")]
    
    template_name = parameters.get("template_name", "default")
    
    try:
        prompts_manager.set(template_name, template_text, extension=".prompt")
        return [types.TextContent(type="text", text=f"Prompt template '{template_name}' saved successfully to mcp_server/config/prompt/{template_name}.prompt")]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error saving prompt template: {str(e)}")]


async def _use_template(parameters: dict) -> list[types.Content]:
    """Use a saved prompt template with provided parameters."""
    template_name = parameters.get("template_name", "default")
    
    logger.info(f"Using template '{template_name}' with parameters: {parameters}")
    
    saved_template = prompts_manager.get(template_name, extension=".prompt")
    if saved_template is None:
        available_templates = prompts_manager.list_files(extension=".prompt")
        if available_templates:
            available_list = ", ".join(available_templates)
            return [types.TextContent(type="text", text=f"No prompt template named '{template_name}' found. Available templates: {available_list}")]
        else:
            return [types.TextContent(type="text", text=f"No prompt template named '{template_name}' found. No templates have been saved yet.")]
    
    logger.info(f"Loaded template content:\n--------------\n{saved_template}\n--------------")
    
    try:
        # Create a copy of parameters without the command and template_name
        template_params = {k: v for k, v in parameters.items() if k not in ["command", "template_name"]}
        
        logger.info(f"Template parameters after filtering: {template_params}")
        
        if not template_params:
            return [types.TextContent(type="text", text=f"Template '{template_name}' loaded: {saved_template}\n\nNo parameters provided. Add parameters that match the placeholders in your template.")]
        
        # Extract input variables from the parameters
        input_variables = list(template_params.keys())
        logger.info(f"Input variables: {input_variables}")
        
        # Create prompt template with the input variables
        prompt_template = PromptTemplate(
            input_variables=input_variables,
            template=saved_template
        )
        
        # Format the prompt with the provided parameters
        prompt = prompt_template.format(**template_params)
        logger.info(f"Formatted prompt:\n--------------\n{prompt}\n--------------")

        # Initialize LLM and get response
        logger.info("Calling LLM...")
        response = llm().invoke(prompt)
        logger.info(f"LLM response type: {type(response)}")
        logger.info(f"LLM response raw:\n--------------\n{response}\n--------------")

        # Check if the response has content and convert it to string
        if hasattr(response, "content"):
            response_text = response.content
            logger.info(f"Response content:\n--------------\n{response_text}\n--------------")
        else:
            response_text = str(response)
            logger.info(f"Response as string:\n--------------\n{response_text}\n--------------")

        return [types.TextContent(type="text", text=response_text)]
    except Exception as e:
        logger.error(f"Error in _use_template: {str(e)}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error using prompt template '{template_name}': {str(e)}")]


async def _list_templates(parameters: dict) -> list[types.Content]:
    """List all saved prompt templates."""
    try:
        available_templates = prompts_manager.list_files(extension=".prompt")
        
        if not available_templates:
            return [types.TextContent(type="text", text="No prompt templates found. Use the 'save' command to create templates.")]
        
        result = f"Available prompt templates ({len(available_templates)}):\n\n"
        
        for template_name in available_templates:
            template_content = prompts_manager.get(template_name, extension=".prompt")
            # Truncate long templates for display
            if len(template_content) > 100:
                template_preview = template_content[:100] + "..."
            else:
                template_preview = template_content
            
            result += f"**{template_name}**\n{template_preview}\n\n"
        
        return [types.TextContent(type="text", text=result)]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error listing templates: {str(e)}")]
