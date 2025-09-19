## Info
- These instructions are necessary to demonstrate the ability build a complex chain in which, when the hotkey is pressed, the contents of the Windows clipboard will be sent to LLM with the corresponding prompt for translation, and then the result will be pasted back into the clipboard

## How to ask for demo in chat
Use this case to make demo:
```
Show me demo from file:
I need a hotkey that I can press to translate the text in the clipboard into English.
```

## Important
- Use MCP (do not use terminal). 
- Don't do any checks, just initialize the solution - I need minimum MCP calls.
- Remove existing pipeline on this hotkey if any.

## Critical fix
- Use `lng_llm_prompt_template` tool, not `lng_llm_agent_demo`.
- Use `{! clipboard_text.content !}` not `{! clipboard_text.unicode_text !}` (new expression syntax)

## Scenario
Create `Ctrl+Shift+Insert` hotkey that:
- Takes text from clipboard.
- Translates to `English B2 level` via prompt.
- Puts result back to clipboard.
