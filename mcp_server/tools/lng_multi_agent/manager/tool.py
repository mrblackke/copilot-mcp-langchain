import mcp.types as types
import json
import logging
import os
import asyncio
import uuid
import sys
import warnings
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from langchain.agents import initialize_agent, AgentType
from langchain.callbacks.base import BaseCallbackHandler
from langchain.tools import BaseTool, tool
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field
from mcp_server.llm import llm
from importlib import import_module
from mcp_server.pipeline.expressions import evaluate_expression
from mcp_server.file_state_manager import prompts_manager
from mcp_server.logging_config import setup_logging

# Setup unified logging to mcp_server.log for all multi-agent output
logger = setup_logging("mcp_server", logging.DEBUG)

# Suppress specific LangChain warnings to prevent stderr pollution
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain.*")
warnings.filterwarnings("ignore", message=".*migration guide.*")
warnings.filterwarnings("ignore", message=".*LangChainDeprecationWarning.*")

# Redirect warnings to our logger instead of stderr
class LoggerWriter:
    """Custom writer to redirect stderr to our logger"""
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.buffer = ""
    
    def write(self, message):
        if message and message.strip():
            self.buffer += message
            if message.endswith('\n'):
                self.logger.log(self.level, f"[STDERR] {self.buffer.strip()}")
                self.buffer = ""
    
    def flush(self):
        if self.buffer:
            self.logger.log(self.level, f"[STDERR] {self.buffer.strip()}")
            self.buffer = ""

# Redirect stderr to our unified logger
original_stderr = sys.stderr
sys.stderr = LoggerWriter(logger, logging.WARNING)

# Redirect warnings to logger
def warning_handler(message, category, filename, lineno, file=None, line=None):
    logger.warning(f"[LANGCHAIN_WARNING] {category.__name__}: {message} (in {filename}:{lineno})")

warnings.showwarning = warning_handler

class AgentCallbackHandler(BaseCallbackHandler):
    """Callback handler to log agent's intermediate thoughts and reasoning"""
    
    def __init__(self, conversation_logger):
        self.conversation_logger = conversation_logger
        self.step_count = 0
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        """Called when LLM starts generating response"""
        self.conversation_logger.log_agent_response(f"[THINKING] LLM started processing...")
    
    def on_llm_end(self, response, **kwargs):
        """Called when LLM finishes generating response"""
        if hasattr(response, 'generations') and response.generations:
            for generation in response.generations:
                for gen in generation:
                    if hasattr(gen, 'text'):
                        self.conversation_logger.log_agent_response(f"[REASONING] {gen.text}")
    
    def on_agent_action(self, action, **kwargs):
        """Called when agent decides to take an action"""
        self.step_count += 1
        self.conversation_logger.log_agent_response(
            f"[STEP {self.step_count}] Action: {action.tool}, Input: {action.tool_input}"
        )
    
    def on_agent_finish(self, finish, **kwargs):
        """Called when agent finishes"""
        self.conversation_logger.log_agent_response(f"[FINISHED] {finish.return_values.get('output', 'No output')}")

class ConversationLogger:
    """Conversation logging for each sub-agent in a separate file"""
    
    def __init__(self, agent_id: str, agent_name: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.log_dir = Path("mcp_server/logs/multi_agent")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file name based on agent ID and name
        safe_name = "".join(c for c in agent_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_')
        self.log_file = self.log_dir / f"{safe_name}_{agent_id[:8]}.log"
        
        # Configure logger for this agent
        self.logger = logging.getLogger(f'agent_{agent_id}')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplication
        self.logger.handlers.clear()
        
        # Create file handler
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
        
        # Prevent propagation to parent logger
        self.logger.propagate = False
        
        # Write initial entry
        self.logger.info(f"=== Started conversation with agent {agent_name} (ID: {agent_id}) ===")
    
    def log_user_question(self, question: str):
        """Log user question"""
        self.logger.info(f"USER: {question}")
    
    def log_agent_response(self, response: str):
        """Log agent response"""
        self.logger.info(f"AGENT: {response}")
    
    def log_tool_usage(self, tool_name: str, parameters: dict, result: str, log_params: bool = None):
        """Log tool usage - automatically determine if should log params based on result content"""
        # Auto-detect if this is the first call (with "Executing...") or second call (with actual result)
        is_start = result == "Executing..."
        
        # Log parameters only at start, not on result logging
        if log_params is None:
            should_log_params = is_start
        else:
            should_log_params = log_params
            
        if should_log_params:
            self.logger.info(f"TOOL_PARAMS: {json.dumps(parameters, ensure_ascii=False, indent=2)}")
        self.logger.info(f"TOOL_RESULT: {result[:500]}{'...' if len(result) > 500 else ''}")
    
    def log_session_start(self, session_id: str, question: str):
        """Log session start with unique ID"""
        self.logger.info(f"=== SESSION_START {session_id} ===")
        self.logger.info(f"USER: {question}")
        
        # Get current line number by counting lines in log file
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                start_line = len(lines) - 1  # Line number where session started (0-indexed)
                
                # Also log to main mcp_server.log with file reference
                logger.info(f"🚀 SESSION_START [{self.agent_name}] {session_id} - Details: {self.log_file}:{start_line + 1}")
                
                return start_line
        except:
            return 0
    
    def log_session_end(self, session_id: str, summary: str):
        """Log session end with unique ID"""
        self.logger.info(f"AGENT_SUMMARY: {summary}")
        self.logger.info(f"=== SESSION_END {session_id} ===")
        
        # Get current line number by counting lines in log file
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                end_line = len(lines) - 1  # Line number where session ended (0-indexed)
                
                # Find the start line for this session by searching backwards
                start_line = 0
                for i in range(len(lines) - 1, -1, -1):
                    if f"SESSION_START {session_id}" in lines[i]:
                        start_line = i
                        break
                
                # Also log to main mcp_server.log with file reference and line range
                logger.info(f"🏁 SESSION_END [{self.agent_name}] {session_id} - Full dialog: {self.log_file}:{start_line + 1}-{end_line + 1}")
                
                return end_line
        except:
            return 0
    
    def log_error(self, error_msg: str):
        """Log error"""
        self.logger.error(f"ERROR: {error_msg}")
    


class DirectToolWrapper(BaseTool):
    """LangChain tool that directly calls MCP tool functions"""
    
    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")  
    tool_module_path: str = Field(description="Path to tool module")
    tool_function_name: str = Field(description="Tool function name", default="run_tool")
    conversation_logger: Optional[Any] = Field(default=None, description="Conversation logger instance")
    
    def __init__(self, name: str, description: str, tool_module_path: str, conversation_logger=None, **kwargs):
        super().__init__(
            name=name,
            description=description,
            tool_module_path=tool_module_path,
            conversation_logger=conversation_logger,
            **kwargs
        )
    
    def _run(self, **kwargs) -> str:
        """Synchronous tool execution"""
        try:
            # Log tool usage - log parameters only at start
            if self.conversation_logger:
                self.conversation_logger.log_tool_usage(self.name, kwargs, "Executing...")
            
            # Import tool module
            tool_module = import_module(self.tool_module_path)
            
            # Get the tool function
            if hasattr(tool_module, self.tool_function_name):
                tool_function = getattr(tool_module, self.tool_function_name)
                
                # Call the function directly                
                if asyncio.iscoroutinefunction(tool_function):
                    # If async function, run in event loop
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # If loop is already running, create task
                            import concurrent.futures
                            import threading
                            
                            def run_in_new_loop():
                                new_loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(new_loop)
                                try:
                                    return new_loop.run_until_complete(tool_function(self.name, kwargs))
                                finally:
                                    new_loop.close()
                            
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(run_in_new_loop)
                                result = future.result()
                        else:
                            result = loop.run_until_complete(tool_function(self.name, kwargs))
                    except RuntimeError:
                        # No event loop, create new one
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            result = loop.run_until_complete(tool_function(self.name, kwargs))
                        finally:
                            loop.close()
                else:
                    # Synchronous function
                    result = tool_function(self.name, kwargs)
                
                # Extract text from result
                result_text = ""
                if isinstance(result, list) and len(result) > 0:
                    if hasattr(result[0], 'text'):
                        result_text = result[0].text
                    else:
                        result_text = str(result[0])
                else:
                    result_text = str(result)
                
                # Log result
                if self.conversation_logger:
                    self.conversation_logger.log_tool_usage(self.name, kwargs, result_text)
                
                return result_text
                    
            else:
                error_msg = f"Error: Tool function {self.tool_function_name} not found in module {self.tool_module_path}"
                if self.conversation_logger:
                    self.conversation_logger.log_error(error_msg)
                return error_msg
                
        except Exception as e:
            error_msg = f"Error executing {self.name}: {str(e)}"
            
            # Add helpful hint about getting tool information
            if "parameter" in str(e).lower() or "argument" in str(e).lower() or "missing" in str(e).lower():
                error_msg += f"\n\nHint: Use `lng_get_tools_info(tools=\"{self.name}\")` to see required parameters and usage examples."
            
            if self.conversation_logger:
                self.conversation_logger.log_error(error_msg)
            return error_msg
    
    async def _arun(self, **kwargs) -> str:
        """Asynchronous tool execution"""
        try:
            # Log tool usage - log parameters only at start
            if self.conversation_logger:
                self.conversation_logger.log_tool_usage(self.name, kwargs, "Executing...")
            
            # Import tool module
            tool_module = import_module(self.tool_module_path)
            
            # Get the tool function
            if hasattr(tool_module, self.tool_function_name):
                tool_function = getattr(tool_module, self.tool_function_name)
                
                # Call the function
                if asyncio.iscoroutinefunction(tool_function):
                    result = await tool_function(self.name, kwargs)
                else:
                    result = tool_function(self.name, kwargs)
                
                # Extract text from result
                result_text = ""
                if isinstance(result, list) and len(result) > 0:
                    if hasattr(result[0], 'text'):
                        result_text = result[0].text
                    else:
                        result_text = str(result[0])
                else:
                    result_text = str(result)
                
                # Log result
                if self.conversation_logger:
                    self.conversation_logger.log_tool_usage(self.name, kwargs, result_text)
                
                return result_text
                    
            else:
                error_msg = f"Error: Tool function {self.tool_function_name} not found in module {self.tool_module_path}"
                if self.conversation_logger:
                    self.conversation_logger.log_error(error_msg)
                return error_msg
                
        except Exception as e:
            error_msg = f"Error executing {self.name}: {str(e)}"
            
            # Add helpful hint about getting tool information
            if "parameter" in str(e).lower() or "argument" in str(e).lower() or "missing" in str(e).lower():
                error_msg += f"\n\nHint: Use `lng_get_tools_info(tools=\"{self.name}\")` to see required parameters and usage examples."
            
            if self.conversation_logger:
                self.conversation_logger.log_error(error_msg)
            return error_msg

@dataclass
class SubAgentConfig:
    """Configuration for a sub-agent"""
    agent_id: str
    name: str
    module_path: str
    available_tools: List[str]
    description: str
    system_prompt_template: str
    max_iterations: int
    max_execution_time: int
    created_at: datetime
    last_active: datetime
    config_path: str
    
    def to_dict(self):
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "module_path": self.module_path,
            "available_tools": self.available_tools,
            "description": self.description,
            "system_prompt_template": self.system_prompt_template,
            "max_iterations": self.max_iterations,
            "max_execution_time": self.max_execution_time,
            "created_at": self.created_at.isoformat()
            # last_active исключено - оно хранится только в памяти
        }
    
    @classmethod
    def from_dict(cls, data, config_path: str = ""):
        return cls(
            agent_id=data["agent_id"],
            name=data["name"],
            module_path=data["module_path"],
            available_tools=data["available_tools"],
            description=data["description"],
            system_prompt_template=data.get("system_prompt_template", "multi_agent_default"),
            max_iterations=data.get("max_iterations", 20),
            max_execution_time=data.get("max_execution_time", 120),
            created_at=datetime.fromisoformat(data["created_at"]),
            # last_active берем из файла, если есть, иначе используем created_at
            last_active=datetime.fromisoformat(data.get("last_active", data["created_at"])),
            config_path=config_path
        )

class SubAgentMemory:
    """Memory management for sub-agents using LangChain"""
    def __init__(self, agent_id: str, max_token_limit: int = 2000):
        self.agent_id = agent_id
        self.llm = llm()
        # Use simpler window memory to avoid deprecation warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            warnings.filterwarnings("ignore", message=".*migration guide.*")
            self.memory = ConversationBufferWindowMemory(
                k=10,  # Keep last 10 interactions
                return_messages=True
            )
        
    def add_interaction(self, question: str, answer: str):
        """Add a question-answer pair to memory"""
        self.memory.save_context(
            {"input": question},
            {"output": answer}
        )
    
    def get_memory_summary(self) -> str:
        """Get memory summary for context"""
        try:
            # Get conversation buffer and convert to simple string
            if hasattr(self.memory, 'chat_memory') and self.memory.chat_memory.messages:
                messages = []
                for msg in self.memory.chat_memory.messages[-5:]:  # Last 5 messages
                    if hasattr(msg, 'content'):
                        content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                        msg_type = type(msg).__name__.replace('Message', '')
                        messages.append(f"{msg_type}: {content}")
                return " | ".join(messages) if messages else "No conversation history"
            else:
                return "No conversation history"
        except Exception as e:
            return f"Error getting memory summary: {str(e)}"
    
    def get_conversation_history(self) -> List[BaseMessage]:
        """Get conversation history"""
        return self.memory.chat_memory.messages
    
    def clear_memory(self):
        """Clear memory"""
        self.memory.clear()

class SubAgent:
    """A sub-agent that monitors a specific module using direct tool access"""
    def __init__(self, config: SubAgentConfig):
        self.config = config
        self.memory = SubAgentMemory(config.agent_id)
        self.conversation_logger = ConversationLogger(config.agent_id, config.name)
        self.tools = []
        self.agent = None
        
        # Create callback handler for detailed logging
        self.callback_handler = AgentCallbackHandler(self.conversation_logger)
        
        # Create LLM instance WITHOUT callbacks to avoid verbose output
        self.llm = llm(verbose=False)
        
        # Initialize tools directly
        self._initialize_tools()
        
        # Create LangChain agent
        self._initialize_agent()
    
    def _initialize_tools(self):
        """Initialize tools using DirectToolWrapper"""
        self.tools = []
        try:
            from mcp_server.tools.tool_registry import tool_definitions
            
            # Always add lng_get_tools_info automatically (hardcoded)
            help_tool_info = None
            for tool in tool_definitions:
                if tool["name"] == "lng_get_tools_info":
                    help_tool_info = tool
                    break
            
            if help_tool_info:
                help_wrapper = DirectToolWrapper(
                    name=help_tool_info['name'],
                    description=f"Get help information about available tools",
                    tool_module_path=help_tool_info['module_path'],
                    conversation_logger=self.conversation_logger
                )
                self.tools.append(help_wrapper)
                logger.info(f"Agent {self.config.agent_id}: Automatically added lng_get_tools_info")
            
            # Add configured tools
            for tool_name in self.config.available_tools:
                try:
                    # Find tool in registry
                    tool_info = None
                    for tool in tool_definitions:
                        if tool["name"] == tool_name:
                            tool_info = tool
                            break
                    
                    if tool_info:
                        # Create DirectToolWrapper for each tool with logger
                        wrapper = DirectToolWrapper(
                            name=tool_info['name'],
                            description=f"Tool {tool_name} for agent {self.config.name}",
                            tool_module_path=tool_info['module_path'],
                            conversation_logger=self.conversation_logger
                        )
                        self.tools.append(wrapper)
                        logger.info(f"Agent {self.config.agent_id}: Added tool {tool_name}")
                    else:
                        logger.warning(f"Agent {self.config.agent_id}: Tool {tool_name} not found in registry")
                        
                except Exception as e:
                    logger.error(f"Agent {self.config.agent_id}: Error loading tool {tool_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Agent {self.config.agent_id}: Error importing tool_registry: {e}")
    
    def _initialize_agent(self):
        """Initialize LangChain agent with more aggressive limits"""
        try:
            if self.tools:
                # Use AgentExecutor directly for better control
                from langchain.agents import AgentExecutor
                from langchain.agents.structured_chat.base import StructuredChatAgent
                
                # Create agent with strict prompt - NO VERBOSE
                agent = StructuredChatAgent.from_llm_and_tools(
                    llm=self.llm,
                    tools=self.tools,
                    verbose=False,  # ОТКЛЮЧАЕМ verbose вывод
                    handle_parsing_errors=True
                )
                
                # Create executor without callbacks to prevent MCP pollution
                self.agent = AgentExecutor(
                    agent=agent,
                    tools=self.tools,
                    memory=self.memory.memory,
                    # callbacks=[self.callback_handler],  # УБИРАЕМ callbacks
                    max_iterations=self.config.max_iterations,
                    max_execution_time=self.config.max_execution_time,
                    handle_parsing_errors=True,
                    early_stopping_method="force",  # Force stop if needed
                    return_intermediate_steps=False,  # Don't return extra info
                    trim_intermediate_steps=0,  # Don't keep intermediate steps
                    verbose=False  # ОТКЛЮЧАЕМ verbose вывод полностью
                )
                logger.info(f"Agent {self.config.agent_id}: Initialized AgentExecutor with strict limits: max_iterations={self.config.max_iterations}, max_execution_time={self.config.max_execution_time}")
            else:
                logger.warning(f"Agent {self.config.agent_id}: No tools available")
                self.agent = None
        except Exception as e:
            logger.error(f"Agent {self.config.agent_id}: Error initializing agent: {e}")
            logger.exception("Full error details:")
            self.agent = None

    def _create_analysis_block(self, session_id: str, start_line: int, end_line: int, status: str, **extra_fields) -> dict:
        """Create standardized analysis block with consistent structure"""
        analysis = {
            "session_id": session_id,
            "log_file": str(self.conversation_logger.log_file),
            "log_start_line": start_line - 1,  # Adjust to point to conversation start
            "log_end_line": end_line + 1,      # Adjust to point to session end
            "status": status,
            "agent_id": self.config.agent_id,
            "agent_name": self.config.name,
            "config_path": self.config.config_path
        }
        
        # Add any extra fields
        analysis.update(extra_fields)
        return analysis

    async def process_query(self, question: str) -> dict:
        """Process a query and return a structured response with session tracking"""
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        try:
            # Log session start and get line number
            start_line = self.conversation_logger.log_session_start(session_id, question)
            
            if not self.agent:
                error_msg = f"Agent {self.config.name} failed to initialize properly."
                self.conversation_logger.log_error(error_msg)
                end_line = self.conversation_logger.log_session_end(session_id, error_msg)
                
                return {
                    "response": error_msg,
                    "analysis": self._create_analysis_block(session_id, start_line, end_line, "error")
                }
            
            # Load system prompt template from file
            base_prompt_template = prompts_manager.get(self.config.system_prompt_template, extension=".prompt")
            if base_prompt_template is None:
                logger.warning(f"System prompt template '{self.config.system_prompt_template}' not found, using fallback")
                # Fallback to basic template
                base_prompt_template = """You are a specialized agent responsible for module: {! config.module_path !}

Your role is to analyze and understand code in your assigned module and answer questions about it.

Module Description: {! config.description !}
Available Tools: {! config.available_tools_list !}

Use lng_get_tools_info for help with tools when needed."""

            # Create context for template evaluation
            all_available_tools = ['lng_get_tools_info'] + self.config.available_tools
            template_context = {
                "config": {
                    "module_path": self.config.module_path,
                    "description": self.config.description,
                    "available_tools_list": ', '.join(all_available_tools)
                },
                "base_dir": os.path.dirname(os.path.abspath(__file__))
            }
            
            try:
                # Use expression evaluator to process template
                system_context = evaluate_expression(base_prompt_template, template_context)
            except Exception as e:
                logger.warning(f"Template evaluation failed, using fallback: {e}")
                # Fallback to simple, direct prompt to reduce iterations
                all_tools_fallback = ['lng_get_tools_info'] + self.config.available_tools
                system_context = f"""Answer questions about module: {self.config.module_path}

Description: {self.config.description}
Tools: {', '.join(all_tools_fallback)}

IMPORTANT: Keep responses short and direct. Use tools only when necessary."""
            
            # Combine system context with the question
            full_input = f"{system_context}\n\nQuestion: {question}"
            
            # Process with agent - add aggressive timeout wrapper
            execution_start = datetime.now()
            try:
                # Reduce timeout buffer to make it more aggressive
                timeout_seconds = self.config.max_execution_time
                logger.info(f"Agent {self.config.agent_id}: Starting execution with {timeout_seconds}s timeout")
                
                if hasattr(self.agent, 'ainvoke'):
                    # Use async version with timeout
                    result = await asyncio.wait_for(
                        self.agent.ainvoke({"input": full_input}), 
                        timeout=timeout_seconds
                    )
                else:
                    # Fallback to sync version with timeout
                    result = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, 
                            lambda: self.agent.invoke({"input": full_input})
                        ), 
                        timeout=timeout_seconds
                    )
                
                execution_time = (datetime.now() - execution_start).total_seconds()
                logger.info(f"Agent {self.config.agent_id}: Execution completed in {execution_time:.2f}s")
                
            except asyncio.TimeoutError:
                execution_time = (datetime.now() - execution_start).total_seconds()
                # Handle timeout with detailed info
                timeout_msg = f"TIMEOUT: Agent execution exceeded {self.config.max_execution_time}s (actual: {execution_time:.2f}s)"
                
                logger.warning(f"Agent {self.config.agent_id}: {timeout_msg}")
                self.conversation_logger.log_error(timeout_msg)
                end_line = self.conversation_logger.log_session_end(session_id, timeout_msg)
                
                return {
                    "response": "Agent stopped due to time limit.",
                    "analysis": self._create_analysis_block(
                        session_id, start_line, end_line, "timeout",
                        max_execution_time=self.config.max_execution_time,
                        actual_execution_time=execution_time,
                        max_iterations=self.config.max_iterations,
                        error="Time limit exceeded"
                    )
                }
            
            # Extract the response
            response = result.get("output", "No response generated")
            logger.debug(f"Agent {self.config.agent_id}: Extracted response from result")
            
            # Check if agent stopped due to iteration limit (LangChain doesn't throw exception for this)
            if "stopped due to iteration limit" in response.lower() or "iteration limit" in response.lower():
                limit_msg = f"EXECUTION LIMIT REACHED: Agent exceeded {self.config.max_iterations} iterations limit."
                
                logger.warning(f"Agent {self.config.agent_id}: Iteration limit reached")
                # Don't log error here to avoid duplication - limit_msg will be logged in session_end
                end_line = self.conversation_logger.log_session_end(session_id, limit_msg)
                
                return {
                    "response": limit_msg,
                    "analysis": self._create_analysis_block(
                        session_id, start_line, end_line, "limit_exceeded",
                        max_execution_time=self.config.max_execution_time,
                        max_iterations=self.config.max_iterations,
                        error="Iteration limit exceeded"
                    )
                }
            
            # Create summary (this is already a summary since we ask agent to summarize)
            summary = self._create_summary(question, response)
            logger.debug(f"Agent {self.config.agent_id}: Created summary")
            
            # Log session end and get line number
            end_line = self.conversation_logger.log_session_end(session_id, summary)
            logger.debug(f"Agent {self.config.agent_id}: Logged session end at line {end_line}")
            
            # Store in memory
            self.memory.add_interaction(question, summary)
            logger.debug(f"Agent {self.config.agent_id}: Stored interaction in memory")
            
            # Update last active time
            self.config.last_active = datetime.now()
            logger.debug(f"Agent {self.config.agent_id}: Updated last active time")
            
            logger.debug(f"Agent {self.config.agent_id}: About to return result")
            return {
                "response": summary,
                "analysis": self._create_analysis_block(session_id, start_line, end_line, "success")
            }
            
        except Exception as e:
            # Check if it's a limit-related error
            error_str = str(e).lower()
            is_limit_error = any(keyword in error_str for keyword in [
                'iteration', 'timeout', 'time limit', 'max_iterations', 'max_execution_time', 'limit', 'exceeded'
            ])
            
            if is_limit_error:
                limit_msg = f"EXECUTION LIMIT REACHED: Agent exceeded configured limits.\n\n"
                limit_msg += f"Current limits: {self.config.max_iterations} iterations, {self.config.max_execution_time} seconds\n"
                limit_msg += f"To increase limits, update the agent config file with higher max_iterations or max_execution_time values."
                
                logger.warning(f"Agent {self.config.agent_id}: Execution limit reached - {str(e)}")
                # Don't log error here to avoid duplication - limit_msg will be logged in session_end
                end_line = self.conversation_logger.log_session_end(session_id, limit_msg)
                
                return {
                    "response": limit_msg,
                    "analysis": self._create_analysis_block(
                        session_id, start_line, end_line, "limit_exceeded",
                        max_execution_time=self.config.max_execution_time,
                        max_iterations=self.config.max_iterations,
                        error=str(e)
                    )
                }
            else:
                # Handle other errors
                error_msg = f"Error processing query: {str(e)}"
                
                # Check for specific parsing errors and add helpful information
                if "output parsing error" in str(e).lower() or "could not parse llm output" in str(e).lower():
                    error_msg += "\n\nPARSING ERROR: The AI agent had trouble formatting its response. This is usually resolved automatically with handle_parsing_errors=True."
                    logger.warning(f"Agent {self.config.agent_id}: Output parsing error detected - {str(e)[:200]}...")
                else:
                    logger.error(f"Agent {self.config.agent_id}: {error_msg}")
                    
                self.conversation_logger.log_error(error_msg)
                end_line = self.conversation_logger.log_session_end(session_id, error_msg)
                
                return {
                    "response": error_msg,
                    "analysis": self._create_analysis_block(
                        session_id, start_line, end_line, "error",
                        error=str(e)
                    )
                }
    
    def _create_summary(self, question: str, response: str) -> str:
        """Create a summary of the interaction"""
        # For now, we'll return the response as-is since we ask the agent to provide summaries
        # In the future, we might want to add additional summarization
        return response
    
    def get_status(self) -> dict:
        """Get agent status"""
        # Start with all config fields
        status = {}
        
        # Add all fields from config
        for field_name in dir(self.config):
            if not field_name.startswith('_'):  # Skip private fields
                field_value = getattr(self.config, field_name)
                # Convert datetime to string
                if hasattr(field_value, 'isoformat'):
                    status[field_name] = field_value.isoformat()
                # Skip methods/functions
                elif not callable(field_value):
                    status[field_name] = field_value
        
        # Add additional computed fields
        status["memory_summary"] = self.memory.get_memory_summary()
        status["tools_count"] = len(self.tools)
        
        return status
    
    def __del__(self):
        """Destructor to log session end when agent is destroyed"""
        try:
            if hasattr(self, 'conversation_logger'):
                self.conversation_logger.log_session_end("destructor", "Agent destroyed")
        except Exception:
            # Ignore errors in destructor
            pass

class MultiAgentManager:
    """Manager for multiple sub-agents"""
    def __init__(self):
        self.agents: Dict[str, SubAgent] = {}
        self.config_dir = Path("mcp_server/config/multi_agent")
        self._load_configs()
    
    def _name_to_filename(self, name: str) -> str:
        """Convert agent name to filename (using hyphens instead of spaces)"""
        # Replace spaces with hyphens, convert to lowercase, remove special chars
        filename = name.lower().replace(' ', '-')
        # Keep only alphanumeric characters and hyphens
        filename = ''.join(c for c in filename if c.isalnum() or c == '-')
        # Remove multiple consecutive hyphens
        filename = '-'.join(filter(None, filename.split('-')))
        return f"{filename}.json"
    
    def _load_configs(self):
        """Load agent configurations from individual files"""
        if not self.config_dir.exists():
            logger.info("Multi-agent config directory does not exist yet")
            return
            
        for json_file in self.config_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    agent_data = json.load(f)
                
                config = SubAgentConfig.from_dict(agent_data, str(json_file))
                agent = SubAgent(config)
                self.agents[config.agent_id] = agent
                logger.info(f"Loaded agent {config.name} from {json_file.name}")
                
            except Exception as e:
                logger.error(f"Error loading agent from {json_file}: {e}")
        
        logger.info(f"Loaded {len(self.agents)} sub-agents total")
    
    def _create_manager_analysis_block(self, agent_id: str, status: str, **extra_fields) -> dict:
        """Create standardized analysis block for manager-level operations"""
        analysis = {
            "status": status,
            "agent_id": agent_id,
        }
        
        # Add agent info if available
        if agent_id in self.agents:
            analysis["agent_name"] = self.agents[agent_id].config.name
            analysis["config_path"] = self.agents[agent_id].config.config_path
        else:
            analysis["agent_name"] = "Unknown"
            analysis["config_path"] = ""
        
        # Add any extra fields
        analysis.update(extra_fields)
        return analysis

    def _save_agent_config(self, config: SubAgentConfig):
        """Save individual agent configuration to file (synchronous version)"""
        try:
            logger.debug(f"Saving config for agent {config.name}")
            # Ensure directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Config directory ensured: {self.config_dir}")
            
            filename = self._name_to_filename(config.name)
            file_path = self.config_dir / filename
            logger.debug(f"Config file path: {file_path}")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
            logger.debug(f"Config written to file for agent {config.name}")
                
            logger.info(f"Saved agent {config.name} to {filename}")
                
        except Exception as e:
            logger.error(f"Error saving agent config for {config.name}: {e}")

    def _remove_agent_config(self, config: SubAgentConfig):
        """Remove individual agent configuration file"""
        try:
            filename = self._name_to_filename(config.name)
            file_path = self.config_dir / filename
            
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Removed agent config file {filename}")
                
        except Exception as e:
            logger.error(f"Error removing agent config file for {config.name}: {e}")
    
    def create_agent(self, name: str, module_path: str, available_tools: List[str], description: str = "", system_prompt_template: str = "multi_agent_default", max_iterations: int = 20, max_execution_time: int = 120) -> str:
        """Create a new sub-agent"""
        agent_id = str(uuid.uuid4())
        
        # Generate config file path
        filename = self._name_to_filename(name)
        config_path = str(self.config_dir / filename)
        
        config = SubAgentConfig(
            agent_id=agent_id,
            name=name,
            module_path=module_path,
            available_tools=available_tools,
            description=description,
            system_prompt_template=system_prompt_template,
            max_iterations=max_iterations,
            max_execution_time=max_execution_time,
            created_at=datetime.now(),
            last_active=datetime.now(),
            config_path=config_path
        )
        
        agent = SubAgent(config)
        self.agents[agent_id] = agent
        
        # Save individual agent config
        self._save_agent_config(config)
        
        logger.info(f"Created sub-agent {name} with ID {agent_id} for module {module_path}")
        return agent_id
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove a sub-agent"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent_name = agent.config.name
            
            # Log session end before removing agent
            agent.conversation_logger.log_session_end("remove_agent", f"Agent {agent_name} removed from manager")
            
            # Remove config file
            self._remove_agent_config(agent.config)
            
            # Remove from memory
            del self.agents[agent_id]
            
            logger.info(f"Removed sub-agent {agent_name} with ID {agent_id}")
            return True
        return False
    
    async def query_agent(self, agent_id: str, question: str) -> dict:
        """Send a query to a specific sub-agent"""
        logger.debug(f"MultiAgentManager.query_agent: Starting query for agent {agent_id}")
        
        if agent_id not in self.agents:
            logger.debug(f"MultiAgentManager.query_agent: Agent {agent_id} not found")
            return {
                "response": f"Agent with ID {agent_id} not found",
                "analysis": self._create_manager_analysis_block(agent_id, "error", error="Agent not found")
            }

        try:
            logger.debug(f"MultiAgentManager.query_agent: About to call process_query for agent {agent_id}")
            result = await self.agents[agent_id].process_query(question)
            logger.debug(f"MultiAgentManager.query_agent: process_query completed, result type: {type(result)}")
            logger.debug(f"MultiAgentManager.query_agent: result keys: {list(result.keys()) if isinstance(result, dict) else 'not dict'}")
            
            # Update last active time in memory only (no file save)
            logger.debug(f"MultiAgentManager.query_agent: Updating last_active time in memory")
            self.agents[agent_id].config.last_active = datetime.now()
            logger.debug(f"MultiAgentManager.query_agent: last_active updated in memory only")
            
            logger.debug(f"MultiAgentManager.query_agent: About to return result")
            return result
            
        except Exception as e:
            logger.error(f"Multi-agent manager: query_agent error: {e}")
            return {
                "response": f"QUERY ERROR: {str(e)}",
                "analysis": self._create_manager_analysis_block(
                    agent_id, "error",
                    error=str(e)
                )
            }
    
    def list_agents(self) -> List[dict]:
        """List all sub-agents"""
        result = []
        for agent in self.agents.values():
            try:
                status = agent.get_status()
                result.append(status)
            except Exception as e:
                logger.error(f"Error getting status for agent {agent.config.agent_id}: {e}")
                # Add all config fields even if status fails
                fallback_status = {"error": str(e)}
                
                # Add all fields from config
                for field_name in dir(agent.config):
                    if not field_name.startswith('_'):  # Skip private fields
                        try:
                            field_value = getattr(agent.config, field_name)
                            # Convert datetime to string
                            if hasattr(field_value, 'isoformat'):
                                fallback_status[field_name] = field_value.isoformat()
                            # Skip methods/functions
                            elif not callable(field_value):
                                fallback_status[field_name] = field_value
                        except Exception:
                            pass  # Skip fields that can't be accessed
                
                # Add additional computed fields
                fallback_status["memory_summary"] = "Error getting memory summary"
                fallback_status["tools_count"] = len(agent.tools) if hasattr(agent, 'tools') else 0
                
                result.append(fallback_status)
        return result
    
    def get_agent_by_module(self, module_path: str) -> Optional[str]:
        """Find agent responsible for a specific module"""
        for agent_id, agent in self.agents.items():
            if agent.config.module_path == module_path:
                return agent_id
        return None
    
    def __del__(self):
        """Restore stderr on cleanup"""
        try:
            if 'original_stderr' in globals():
                sys.stderr = original_stderr
                logger.info("Restored original stderr")
        except Exception as e:
            pass  # Ignore errors in destructor

# Global manager instance
manager = MultiAgentManager()

async def tool_info() -> dict:
    """Returns information about the lng_multi_agent_manager tool."""
    return {
        "description": """Multi-Agent Manager for delegating tasks to specialized sub-agents.

This tool manages a system of sub-agents, each responsible for monitoring and analyzing specific modules or directories in a codebase.

**Parameters for different operations:**

**create_agent** - Create a new sub-agent:
- `operation` (string, required): "create_agent"
- `name` (string, required): Human-readable name for the agent (can contain spaces)
- `module_path` (string, required): Path to the module this agent will monitor
- `available_tools` (array, required): List of tool names from tool_registry this agent can use
- `description` (string, optional): Description of the agent's purpose

**Important**: Agent configuration files will be created using lowercase with hyphens (-) instead of spaces in filenames:
- "Frontend Agent" → `frontend-agent.json`
- "API Manager" → `api-manager.json`
- "Database Handler" → `database-handler.json`

**query_agent** - Send query to a sub-agent:
- `operation` (string, required): "query_agent"  
- `agent_id` (string, required): ID of the agent to query
- `question` (string, required): Question to ask the agent

**list_agents** - List all sub-agents:
- `operation` (string, required): "list_agents"

**remove_agent** - Remove a sub-agent:
- `operation` (string, required): "remove_agent"
- `agent_id` (string, required): ID of the agent to remove

**find_agent** - Find agent by module path:
- `operation` (string, required): "find_agent"
- `module_path` (string, required): Module path to search for

**Example Usage:**
- Create agent: `{"operation": "create_agent", "name": "Frontend Agent", "module_path": "/src/components", "available_tools": ["lng_file_read", "lng_file_list"], "description": "Handles React components"}`
- Query agent: `{"operation": "query_agent", "agent_id": "agent-uuid", "question": "What files are in this module?"}`""",
        
        "schema": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The operation to perform",
                    "enum": ["create_agent", "query_agent", "list_agents", "remove_agent", "find_agent"]
                },
                "name": {
                    "type": "string",
                    "description": "Name for the agent (for create_agent). Can contain spaces - the filename will automatically use hyphens instead."
                },
                "module_path": {
                    "type": "string", 
                    "description": "Path to the module (for create_agent and find_agent)"
                },
                "available_tools": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of tool names from tool_registry (for create_agent)"
                },
                "description": {
                    "type": "string",
                    "description": "Description of the agent (for create_agent)"
                },
                "agent_id": {
                    "type": "string",
                    "description": "Agent ID (for query_agent, remove_agent)"
                },
                "question": {
                    "type": "string",
                    "description": "Question to ask the agent (for query_agent)"
                }
            },
            "required": ["operation"]
        }
    }

async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    """Runs the multi-agent manager tool."""
    logger.debug(f"MCP Tool: run_tool called with operation: {parameters.get('operation', 'UNKNOWN')}")
    try:
        operation = parameters.get("operation", "")
        logger.debug(f"MCP Tool: Processing operation: {operation}")
        
        if not operation:
            return [types.TextContent(type="text", text=json.dumps({"error": "operation parameter is required"}, ensure_ascii=False))]
        
        if operation == "create_agent":
            agent_name = parameters.get("name", "")
            module_path = parameters.get("module_path", "")
            available_tools = parameters.get("available_tools", [])
            description = parameters.get("description", "")
            system_prompt_template = parameters.get("system_prompt_template", "multi_agent_default")
            max_iterations = parameters.get("max_iterations", 20)
            max_execution_time = parameters.get("max_execution_time", 120)
            
            if not agent_name or not module_path or not available_tools:
                return [types.TextContent(type="text", text=json.dumps({
                    "error": "name, module_path, and available_tools are required for create_agent operation"
                }, ensure_ascii=False))]
            
            agent_id = manager.create_agent(agent_name, module_path, available_tools, description, system_prompt_template, max_iterations, max_execution_time)
            
            result = {
                "operation": "create_agent",
                "success": True,
                "agent_id": agent_id,
                "name": agent_name,
                "module_path": module_path,
                "available_tools": available_tools,
                "description": description,
                "system_prompt_template": system_prompt_template,
                "max_iterations": max_iterations,
                "max_execution_time": max_execution_time
            }
            
        elif operation == "query_agent":
            agent_id = parameters.get("agent_id", "")
            question = parameters.get("question", "")
            
            if not agent_id or not question:
                return [types.TextContent(type="text", text=json.dumps({
                    "error": "agent_id and question are required for query_agent operation"
                }, ensure_ascii=False))]
            
            logger.debug(f"MCP Tool: About to call manager.query_agent({agent_id}, '{question[:50]}...')")
            response_data = await manager.query_agent(agent_id, question)
            logger.debug(f"MCP Tool: query_agent returned, response_data type: {type(response_data)}")
            logger.debug(f"MCP Tool: response_data content: {str(response_data)[:200]}...")
            logger.debug(f"MCP Tool: query_agent completed for {agent_id}")
            
            # Extract response text and analysis from structured response
            if isinstance(response_data, dict) and "response" in response_data:
                logger.debug(f"Multi-agent manager: processing structured response")
                response_text = response_data["response"]
                analysis = response_data.get("analysis", {})
                
                # Check if response indicates an error
                is_error = analysis.get("status") in ["error", "timeout", "limit_exceeded"]
                
                # Create minimal result - different for success vs error
                if is_error:
                    result = {
                        "operation": "query_agent", 
                        "success": False,
                        "agent_id": agent_id,
                        "message": analysis.get("message", "Query processing failed"),
                        "status": analysis.get("status", "error"),
                        "error": "Agent execution failed",
                        "error_type": analysis.get("status", "unknown_error"),
                        "analysis": analysis
                    }
                    if "error" in analysis:
                        result["error_details"] = analysis["error"]
                else:
                    # Success response with analysis block
                    result = {
                        "operation": "query_agent",
                        "success": True,
                        "agent_id": agent_id,
                        "message": "Query completed successfully",
                        "response": response_text,
                        "analysis": analysis
                    }
            else:
                # Fallback for old format (string response)
                response_text = str(response_data)
                is_error = any(error_indicator in response_text for error_indicator in [
                    "Error processing query", "EXECUTION LIMIT REACHED", "failed to initialize"
                ])
                
                result = {
                    "operation": "query_agent",
                    "success": not is_error,
                    "agent_id": agent_id,
                    "question": question,
                    "response": response_text
                }
                
                # Add error fields if it's an error
                if is_error:
                    result["error"] = "Agent execution failed due to limits or other error"
                    result["error_type"] = "execution_limit" if "LIMIT REACHED" in response_text else "agent_error"
            
        elif operation == "list_agents":
            agents = manager.list_agents()
            
            result = {
                "operation": "list_agents",
                "success": True,
                "agents": agents
            }
            
        elif operation == "remove_agent":
            agent_id = parameters.get("agent_id", "")
            
            if not agent_id:
                return [types.TextContent(type="text", text=json.dumps({
                    "error": "agent_id is required for remove_agent operation"
                }, ensure_ascii=False))]
            
            success = manager.remove_agent(agent_id)
            
            result = {
                "operation": "remove_agent",
                "success": success,
                "agent_id": agent_id
            }
            
        elif operation == "find_agent":
            module_path = parameters.get("module_path", "")
            
            if not module_path:
                return [types.TextContent(type="text", text=json.dumps({
                    "error": "module_path is required for find_agent operation"
                }, ensure_ascii=False))]
            
            agent_id = manager.get_agent_by_module(module_path)
            
            result = {
                "operation": "find_agent",
                "success": True,
                "module_path": module_path,
                "agent_id": agent_id
            }
            
        else:
            return [types.TextContent(type="text", text=json.dumps({
                "error": f"Unknown operation: {operation}"
            }, ensure_ascii=False))]
        
        logger.debug(f"MCP Tool: About to return result for operation: {operation}")
        logger.debug(f"MCP Tool: Result keys: {list(result.keys()) if isinstance(result, dict) else 'not dict'}")
        return [types.TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
    except Exception as e:
        logger.error(f"Error in multi-agent manager: {e}")
        logger.debug(f"Multi-agent manager: returning error response")
        return [types.TextContent(type="text", text=json.dumps({"error": str(e)}, ensure_ascii=False))]


