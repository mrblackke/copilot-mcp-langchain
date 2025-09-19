#!/bin/zsh
# Auto-activate virtual environment for this project
cd "$(dirname "$0")/../.."
if [ -f "./.virtualenv/bin/activate" ]; then
    source "./.virtualenv/bin/activate"
    echo -e "\033[32mVirtual environment activated!\033[0m"
    exec zsh
else
    echo -e "\033[33mVirtual environment not found at ./.virtualenv\033[0m"
    exec zsh
fi
