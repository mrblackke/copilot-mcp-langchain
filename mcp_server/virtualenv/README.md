# Virtual Environment Activation Scripts

This directory contains cross-platform scripts for activating the project's virtual environment and PowerShell profile auto-replacement tools.

## Files

### Virtual Environment Activation

#### Windows
- `activate_venv.ps1` - PowerShell script for virtual environment activation
- `activate_venv.bat` - Command Prompt script for virtual environment activation

#### Linux/macOS
- `activate_venv.sh` - Bash script for virtual environment activation
- `activate_venv.zsh` - Zsh script for virtual environment activation

### PowerShell Auto-Replace Profile Tools

#### Profile Management
- `profile_autoreplace_install.ps1` - Install auto-fix for encoding bug in PowerShell profile
- `profile_autoreplace_uninstall.ps1` - Remove auto-fix function from PowerShell profile  
- `profile_autoreplace_test.ps1` - Test if auto-fix function works correctly

#### What it fixes
The auto-replace profile fixes an encoding bug where commands get corrupted with a leading Cyrillic "с" character:
- `сpython` → `python` ✅
- `сls` → `ls` ✅  
- `сgit` → `git` ✅
- `сnpm` → `npm` ✅

## Usage

### Virtual Environment Manual Activation

**Windows PowerShell:**
```powershell
& mcp_server\virtualenv\activate_venv.ps1
```

**Windows CMD:**
```cmd
mcp_server\virtualenv\activate_venv.bat
```

**Linux/macOS Bash:**
```bash
source mcp_server/virtualenv/activate_venv.sh
```

**Linux/macOS Zsh:**
```zsh
source mcp_server/virtualenv/activate_venv.zsh
```

### PowerShell Auto-Replace Profile

**Install auto-fix:**
```powershell
& mcp_server\virtualenv\profile_autoreplace_install.ps1
```

**Test auto-fix:**
```powershell
& mcp_server\virtualenv\profile_autoreplace_test.ps1
```

**Uninstall auto-fix:**
```powershell
& mcp_server\virtualenv\profile_autoreplace_uninstall.ps1
```

**Manual activation after install:**
```powershell
. $PROFILE
```

### Automatic Activation

The VS Code workspace is configured to automatically activate the virtual environment when opening new terminals. This is done through terminal profiles defined in `.vscode/settings.json`:

- **Windows**: Uses PowerShell with automatic activation
- **Linux**: Uses bash with automatic activation  
- **macOS**: Uses zsh with automatic activation

## Requirements

### Virtual Environment
- Virtual environment must be located at project root: `.virtualenv/`
- VS Code workspace settings must be properly configured
- Execution policies must allow script execution (Windows only)

### PowerShell Auto-Replace
- PowerShell 5.1 or later
- ExecutionPolicy allowing script execution
- Works with both Windows PowerShell and PowerShell Core

## Virtual Environment Structure

```
project-root/
├── .virtualenv/
│   ├── Scripts/          # Windows
│   │   ├── Activate.ps1
│   │   ├── activate.bat
│   │   └── python.exe
│   └── bin/              # Linux/macOS
│       ├── activate
│       └── python
└── mcp_server/
    └── virtualenv/       # This directory
        ├── activate_venv.ps1
        ├── activate_venv.bat
        ├── activate_venv.sh
        ├── activate_venv.zsh
        ├── profile_autoreplace_install.ps1
        ├── profile_autoreplace_uninstall.ps1
        ├── profile_autoreplace_test.ps1
        └── README.md
```

## Troubleshooting

### Virtual Environment Issues
- Ensure `.virtualenv` directory exists in project root
- Check that Python is installed in the virtual environment
- Verify VS Code settings.json is properly configured

### PowerShell Auto-Replace Issues
- Run `Get-ExecutionPolicy` to check if scripts can execute
- Use `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` if needed
- Test with `profile_autoreplace_test.ps1` to verify functionality
- Check profile location with `$PROFILE` variable

### Encoding Bug Examples
If you see these errors, the auto-replace profile will fix them:
```
сpython : The term 'сpython' is not recognized...
сls : The term 'сls' is not recognized...
сgit : The term 'сgit' is not recognized...
```

After installing the auto-replace profile, these commands will be automatically corrected.
