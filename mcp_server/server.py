# filepath: c:\Java\CopipotTraining\hello-langchain\mcp_server\server.py
import sys
import os
import logging
import traceback
import json

# Add the project root to the Python path to ensure imports work correctly
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Setup logging for server
from mcp_server.logging_config import setup_logging
logger = setup_logging("mcp_server", logging.DEBUG)

# # Classes for intercepting and logging MCP communication
class LoggingReadStream:
    """Wrapper for the read stream with logging of incoming messages"""
    
    def __init__(self, original_stream):
        self.original_stream = original_stream
    
    def __aiter__(self):
        return self
      
    async def __anext__(self):
        try:
            message = await self.original_stream.__anext__()
            # Log incoming message
            try:
                # Extract clean JSON-RPC from SessionMessage
                if hasattr(message, 'message') and hasattr(message.message, 'root'):
                    # This is a SessionMessage with JSONRPCMessage inside
                    json_rpc_message = message.message.root
                    if hasattr(json_rpc_message, 'model_dump'):
                        message_dict = json_rpc_message.model_dump()
                    elif hasattr(json_rpc_message, 'dict'):
                        message_dict = json_rpc_message.dict()
                    else:
                        message_dict = json_rpc_message
                elif hasattr(message, 'model_dump'):
                    message_dict = message.model_dump()
                elif hasattr(message, 'dict'):
                    message_dict = message.dict()
                else:
                    message_dict = message
                
                message_json = json.dumps(message_dict, ensure_ascii=False, separators=(',', ':'))
                logger.info(f"[<] {message_json}")
            except Exception as e:
                logger.error(f"Error logging incoming message: {e}")
                logger.info(f"[<] {str(message)}")
            
            return message
        except StopAsyncIteration:
            raise
        except Exception as e:
            logger.error(f"Error in read stream: {e}")
            raise
    
    async def __aenter__(self):
        if hasattr(self.original_stream, '__aenter__'):
            await self.original_stream.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self.original_stream, '__aexit__'):
            return await self.original_stream.__aexit__(exc_type, exc_val, exc_tb)
        return False
    
    def __getattr__(self, name):
        # Proxy all other attributes to the original stream
        return getattr(self.original_stream, name)

class LoggingWriteStream:
    """Wrapper for the write stream with logging of outgoing messages"""
    
    def __init__(self, original_stream):
        self.original_stream = original_stream
    
    async def send(self, message):
        # Log outgoing message
        try:
            # Extract clean JSON-RPC from SessionMessage
            if hasattr(message, 'message') and hasattr(message.message, 'root'):
                # This is a SessionMessage with JSONRPCMessage inside
                json_rpc_message = message.message.root
                if hasattr(json_rpc_message, 'model_dump'):
                    message_dict = json_rpc_message.model_dump()
                elif hasattr(json_rpc_message, 'dict'):
                    message_dict = json_rpc_message.dict()
                else:
                    message_dict = json_rpc_message
            elif hasattr(message, 'model_dump'):
                message_dict = message.model_dump()
            elif hasattr(message, 'dict'):
                message_dict = message.dict()
            else:
                message_dict = message
            
            message_json = json.dumps(message_dict, ensure_ascii=False, separators=(',', ':'))
            logger.info(f"[>] {message_json}")
        except Exception as e:
            logger.error(f"Error logging outgoing message: {e}")
            logger.info(f"[>] {str(message)}")
        
        # Send message through the original stream
        return await self.original_stream.send(message)
    
    async def __aenter__(self):
        if hasattr(self.original_stream, '__aenter__'):
            await self.original_stream.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self.original_stream, '__aexit__'):
            return await self.original_stream.__aexit__(exc_type, exc_val, exc_tb)
        return False
    
    def close(self):
        if hasattr(self.original_stream, 'close'):
            return self.original_stream.close()
    
    async def aclose(self):
        if hasattr(self.original_stream, 'aclose'):
            return await self.original_stream.aclose()
    
    def __getattr__(self, name):
        # Proxy all other attributes to the original stream
        return getattr(self.original_stream, name)

def wrap_streams(read_stream, write_stream):
    """Wraps streams for logging communication"""
    return LoggingReadStream(read_stream), LoggingWriteStream(write_stream)

logger.info(f"Python executable: {sys.executable}")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current directory: {os.getcwd()}")
logger.info(f"Project root in sys.path: {project_root}")

try:
    import anyio
    import click
    import mcp.types as types
    from mcp.server.lowlevel import Server
    from dotenv import load_dotenv
    import os.path
    import mcp_server.tools.tool_registry as tools
    from mcp_server.state_manager import state_manager
    logger.info("All modules imported successfully")
except Exception as e:
    logger.error(f"Error importing modules: {e}")
    logger.error(traceback.format_exc())
    raise

# Importing problematic libraries early to catch any issues before starting the server
try:
    logger.info("Attempting to handle problem imports for all enabled tools")
    from mcp_server.tools.tool_registry import handle_problem_imports
    handle_problem_imports()
    logger.info("Problem imports handled successfully")
except Exception as e:
    logger.error(f"Error during problem imports handling: {e}")
    logger.exception("Stack trace:")

# Initialize the shared state with default values if needed
# Example: state_manager.set("app_start_time", datetime.now().isoformat())

@click.command()
@click.option("--port", default=8000, help="Port to listen on for SSE")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type",
)
def main(port: int, transport: str) -> int:
    logger.info(f"Starting MCP server with transport: {transport}, port: {port}")
    app = Server("langchain-prompt-server")
    logger.info("Server instance created")

    @app.call_tool()
    async def process_tool(name: str, arguments: dict) -> list[types.Content]:
        logger.info(f"Calling tool: {name} with arguments: {arguments}")
        try:
            result = await tools.run_tool(name, arguments)
            logger.info(f"Tool {name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Error running tool {name}: {e}")
            logger.error(traceback.format_exc())
            raise
            
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        logger.info("Listing available tools")
        try:
            tool_info_list = await tools.tools_info()
            logger.info(f"Found {len(tool_info_list)} tools")
            return [
                types.Tool(
                    name=tool["name"],
                    description=tool["description"],
                    inputSchema=tool["schema"]
                ) for tool in tool_info_list
            ]
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            logger.error(traceback.format_exc())
            raise

    if transport == "sse":
        logger.info("Using SSE transport")
        try:
            from mcp.server.sse import SseServerTransport
            from starlette.applications import Starlette
            from starlette.responses import Response
            from starlette.routing import Mount, Route

            sse = SseServerTransport("/messages/")
            logger.info("SSE transport created")

            async def handle_sse(request):
                logger.info("SSE connection received")
                try:
                    async with sse.connect_sse(
                        request.scope, request.receive, request._send
                    ) as streams:
                        logger.info("SSE streams created, running app")
                        # Wrap streams for logging communication
                        read_stream, write_stream = wrap_streams(streams[0], streams[1])
                        logger.info("MCP communication logging started for SSE transport")
                        
                        logger.info("Running app with wrapped streams")
                        await app.run(
                            read_stream, write_stream, app.create_initialization_options()
                        )
                    logger.info("App run completed for SSE connection")
                    return Response()
                except Exception as e:
                    logger.error(f"Error in SSE handler: {e}")
                    logger.error(traceback.format_exc())
                    raise

            starlette_app = Starlette(
                debug=True,
                routes=[
                    Route("/sse", endpoint=handle_sse, methods=["GET"]),
                    Mount("/messages/", app=sse.handle_post_message),
                ],
            )
            logger.info("Starlette app created with routes")

            import uvicorn
            logger.info(f"Starting Uvicorn server on 127.0.0.1:{port}")
            uvicorn.run(starlette_app, host="127.0.0.1", port=port)
        except Exception as e:
            logger.error(f"Error in SSE setup: {e}")
            logger.error(traceback.format_exc())
            raise
    else:
        logger.info("Using stdio transport")
        try:
            from mcp.server.stdio import stdio_server

            async def arun():
                logger.info("Setting up stdio streams")
                try:
                    async with stdio_server() as streams:
                        logger.info("Stdio streams created, running app")
                        # Wrap streams for logging communication
                        read_stream, write_stream = wrap_streams(streams[0], streams[1])
                        logger.info("MCP communication logging started for stdio transport")
                        
                        logger.info("Running app with wrapped streams")
                        await app.run(
                            read_stream, write_stream, app.create_initialization_options()
                        )
                        logger.info("App run completed for stdio connection")
                except Exception as e:
                    logger.error(f"Error in stdio handler: {e}")
                    logger.error(traceback.format_exc())
                    raise

            logger.info("Starting anyio run")
            anyio.run(arun)
            logger.info("Anyio run completed")
        except Exception as e:
            logger.error(f"Error in stdio setup: {e}")
            logger.error(traceback.format_exc())
            raise

    return 0


if __name__ == "__main__":
    try:
        logger.info("Starting main function")
        main()
    except Exception as e:
        logger.error(f"Unhandled exception in main: {e}")
        logger.error(traceback.format_exc())
        raise
