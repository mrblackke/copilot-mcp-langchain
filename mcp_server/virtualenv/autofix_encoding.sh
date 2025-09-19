#!/bin/bash
# Bash Auto-Fix for Encoding Bug
# Handles various encoding issues that can occur in different environments

# Function to fix common encoding issues in command names
autofix_command() {
    local cmd="$1"
    shift
    local args="$@"
    
    # Check for Cyrillic 'с' (U+0441) at the beginning
    if [[ "$cmd" =~ ^с(.+) ]]; then
        local fixed_cmd="${cmd#с}"
        echo -e "\033[33m🔧 Auto-fixing encoding bug: '$cmd' → '$fixed_cmd'\033[0m" >&2
        
        # Check if fixed command exists
        if command -v "$fixed_cmd" >/dev/null 2>&1; then
            echo -e "\033[32m✅ Fixed successfully\033[0m" >&2
            "$fixed_cmd" "$@"
            return $?
        else
            echo -e "\033[31m❌ Command '$fixed_cmd' not found\033[0m" >&2
            return 127
        fi
    fi
    
    # If no fix needed, run original command
    "$cmd" "$@"
}

# Override command_not_found_handle for bash
command_not_found_handle() {
    local cmd="$1"
    shift
    
    # Try autofix first
    if autofix_command "$cmd" "$@"; then
        return $?
    fi
    
    # If autofix fails, show standard error
    echo "bash: $cmd: command not found" >&2
    return 127
}

echo -e "\033[36m🛡️ Bash encoding auto-fix loaded\033[0m"
