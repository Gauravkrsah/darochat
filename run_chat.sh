#!/bin/bash
# Launcher for NVIDIA NIM Terminal Chatbot

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create venv if it doesn't exist
if [ ! -d "$DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$DIR/venv"
fi

# Install / upgrade openai package (OpenAI SDK works with NVIDIA NIM)
"$DIR/venv/bin/pip" install --quiet --upgrade openai

# Run the chatbot
"$DIR/venv/bin/python3" "$DIR/nvidia_chat.py"
