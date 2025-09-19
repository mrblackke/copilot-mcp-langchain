# Terminal Chat Scripts

This folder contains scripts for terminal chat with LLM that use MCP (Model Context Protocol) server to process commands and questions.

## Scripts

### 1. `ask.ps1` - PowerShell Script (Windows)
Script for Windows PowerShell with colored output support and automatic virtual environment activation.

**Installation:** For convenient system-wide usage, install the global alias:
```powershell
.\ask.ps1 install # Creates and loads 'ask' command automatically
# ⚠️ Important: Restart PowerShell terminal for permanent effect!
```

**Usage:**
```powershell
ask "What is Python?" # Simple question mode
ask "dir" "How many files are in the directory?" # Command analysis mode
ask "Get-Process" "Which processes use the most memory?"
ask help # Show detailed help and examples
```

**Uninstall:** To remove the global alias:
```powershell
ask uninstall # Removes 'ask' command from system
```

### 2. `ask` - Bash Script (Linux/macOS/Git Bash)
Script for Unix-like systems and Git Bash on Windows with colored output support and automatic virtual environment activation.

**Installation:** For convenient system-wide usage, install the global alias:
```bash
bash ask install # Creates 'ask' command automatically
# ⚠️ Important: Restart terminal or run: source ~/.bash_profile
```

**Usage:**
```bash
ask "How does Git work?" # Simple question mode
ask "ls -la" "How many files are in the directory?" # Command analysis mode
ask "ps aux" "Which processes use the most CPU?" 
ask help # Show detailed help and examples
```

**Uninstall:** To remove the global alias:
```bash
ask uninstall # Removes 'ask' command from system
```

### 3. `ask.bat` - Batch Script (Windows Command Prompt)
Pure batch script for Windows Command Prompt without PowerShell dependencies.

**Usage:**
```cmd
ask.bat "Explain Windows commands"
ask.bat "dir" "How many files are in the directory?"
ask.bat "tasklist" "Which programs are running?"
```

## Features

### Automatic System Context
All scripts automatically include system information with every request to provide better context for LLM responses:
- Operating system and version
- Shell/terminal type and version  
- System architecture
- Current working directory

This helps the LLM provide more relevant and platform-specific answers.

### Two Operation Modes:

1. **Simple Question** - ask LLM directly:
   - Only one parameter is passed (the question)
   - LLM answers the question without executing commands

2. **Command Analysis** - execute command and analyze the result:
   - Two parameters are passed: command and question
   - Command is executed, result is passed to LLM along with the question
   - LLM analyzes command output and answers the question

### Automatic Virtual Environment Activation

All scripts automatically:
- Check if virtual environment is already activated
- If not, activate `.virtualenv` from parent directory
- Display activation status messages
- Continue working or exit with error