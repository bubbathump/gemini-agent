# Gemini/OpenAI CLI Agent

A standalone Python-based CLI agent that interacts with Google Gemini or OpenAI to perform various tasks.

## Features
- **Multi-Provider**: Switch between Google Gemini and OpenAI.
- **Summarize**: Get a concise summary of any text file.
- **Generate**: Create content based on prompts and optionally save to a file.
- **Ask**: Quick Q&A interface for general knowledge. Supports **@context** (files or directories).
- **History**: Maintains a persistent record of all commands executed.
- **Config**: Set and persist default models and providers.

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Keys and Defaults**:
   Create a `.env` file in the `agent/` directory:
   ```env
   PROVIDER=gemini
   GEMINI_API_KEY=your_gemini_key
   OPENAI_API_KEY=your_openai_key
   DEFAULT_MODEL=gemini-2.0-flash
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
  agent> config set provider openai
  agent> ask "How are you?"
  agent> exit
  ```

### Commands

- **Switch Provider**:
  ```bash
  python3 agent.py config set provider openai
  python3 agent.py config set provider gemini
  ```

- **List available models**:
  ```bash
  # Lists models for the active provider
  python3 agent.py models
  ```

- **Ask about a file or directory**:
  ```bash
  # Works with both Gemini and OpenAI
  python3 agent.py ask "Explain the logic in @agent.py"
  ```

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
  # or explicitly
  python3 agent.py history list
  ```

- **Reset history**:
  ```bash
  python3 agent.py history reset
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
