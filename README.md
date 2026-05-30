# Gemini CLI Agent

A standalone Python-based CLI agent that interacts with the Google Gemini API to perform various tasks.

## Features
- **Summarize**: Get a concise summary of any text file.
- **Generate**: Create content based on prompts and optionally save to a file.
- **Ask**: Quick Q&A interface for general knowledge. Supports **@context** (files or directories).
- **History**: Maintains a persistent record of all commands executed.
- **Config**: Set and persist a default model.

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Key and Defaults**:
   Create a `.env` file in the `agent/` directory:
   ```env
   GEMINI_API_KEY=your_api_key_here
   DEFAULT_MODEL=gemini-2.5-flash
   ```

## Usage

### Interaction Modes

- **One-shot Command**:
  ```bash
  python3 agent.py ask "Hello"
  ```

- **Interactive Mode (REPL)**:
  Run without arguments to enter a persistent session.
  ```bash
  python3 agent.py
  agent> ask "How are you?"
  agent> exit
  ```

- **Piped Commands (Stdin)**:
  ```bash
  echo "models" | python3 agent.py
  cat commands.txt | python3 agent.py
  ```

### Commands

- **Ask about a file or directory**:
  ```bash
  # Analyze a specific file
  python3 agent.py ask "Explain the logic in @agent.py"

  # Analyze an entire directory
  python3 agent.py ask "Summarize the project structure in @src/"
  ```

- **Summarize a file**:
  ```bash
  python3 agent.py summarize <path_to_file>
  ```

- **Generate content**:
  ```bash
  python3 agent.py generate "Write a short poem about coding" --output poem.txt
  ```

- **Ask a question**:
  ```bash
  python3 agent.py ask "What is the distance to the moon?"
  ```

- **View history**:
  ```bash
  python3 agent.py history
  ```

- **List available models**:
  ```bash
  python3 agent.py models
  ```

- **Configure default model**:
  ```bash
  python3 agent.py config set model gemini-1.5-flash
  ```

## Global Options

- **--model**: Override the default model for a single command.
  ```bash
  python3 agent.py --model gemini-1.5-pro ask "Complex question..."
  ```
