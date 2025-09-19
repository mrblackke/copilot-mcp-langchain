## Info
- These instructions demonstrate the Terminal Chat functionality - a command-line AI assistant that can answer questions and analyze command outputs.
- The demo shows installation, usage, and uninstallation of the copilot-cli terminal tools.
- **Important:** This solution works independently and doesn't require MCP to be enabled.

## How to ask for demo in chat
Use this case to make demo:
```
Show me demo from file:
Please demonstrate the copilot-cli terminal chat functionality.
```

## Demo Flow

### Step 1: Clean Previous Installation (if any)
Remove any existing 'ask' command installation to ensure clean setup:
```powershell
mcp_server/projects/copilot-cli/ask.ps1 uninstall
```

**Important:** After uninstallation, you MUST restart your PowerShell terminal for the changes to take effect.

**Ask the user to:**
1. Close current PowerShell window
2. Open a new PowerShell window
3. Return to continue the demo

### Step 2: Install Terminal Chat Command
Install the global 'ask' command for system-wide usage:
```powershell
mcp_server/projects/copilot-cli/ask.ps1 install
```

**Important:** After installation, you MUST restart your PowerShell terminal for the changes to take effect. 

**Ask the user to:**
1. Close current PowerShell window
2. Open a new PowerShell window
3. Return to continue the demo

### Step 3: Demo Usage - Simple Questions
After terminal restart, demonstrate asking AI direct questions:
```powershell
ask "What is the difference between Git and GitHub?"
ask "How do I check if Docker is running on Windows?"
ask "Explain what PowerShell profiles are"
```

### Step 4: Demo Usage - Command Analysis
Show how AI can analyze command outputs:
```powershell
ask "Get-Process | Select-Object -First 5" "Which processes are using the most memory?"
ask "dir" "How many files and folders are in this directory?"
ask "Get-Service | Where-Object {$_.Status -eq 'Running'} | Select-Object -First 3" "What are these services used for?"
```

### Step 5: Show Help
Display available options and examples:
```powershell
ask help
```

### Step 6: Uninstall (Optional)
Remove the global command if needed:
```powershell
ask uninstall
```

**After uninstallation:** Restart PowerShell terminal again for changes to take effect.

## Key Features Demonstrated

1. **Global Command Installation** - System-wide 'ask' command available anywhere
2. **Two Operation Modes:**
   - Simple questions: `ask "question"`  
   - Command analysis: `ask "command" "question about output"`
3. **Automatic System Context** - Includes OS, PowerShell version, current directory
4. **Colored Terminal Output** - User-friendly interface with color coding
5. **Help System** - Built-in help and usage examples

## Important Notes for Demo
- Virtual environment activation happens automatically
- System information is included with every request for better AI responses
- All scripts support Unicode/UTF-8 for international characters
- Cross-platform versions available (PowerShell, Bash, Batch)
