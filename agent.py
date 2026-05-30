import argparse
import json
import os
import sys
import time
import shlex
from datetime import datetime
from pathlib import Path
try:
    from google import genai
    from dotenv import load_dotenv
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

# Constants
HISTORY_FILE = Path(__file__).parent / "history.json"
ENV_FILE = Path(__file__).parent / ".env"

def get_default_model():
    if HAS_DEPS:
        load_dotenv(ENV_FILE)
    return os.getenv("DEFAULT_MODEL", "gemini-2.0-flash")

class HistoryManager:
    """Manages the persistence of command history in a JSON file."""
    def __init__(self, file_path: Path):
        self.file_path = file_path
        if not self.file_path.exists():
            self.save_history([])

    def load_history(self):
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def save_history(self, history):
        with open(self.file_path, "w") as f:
            json.dump(history, f, indent=4)

    def clear_history(self):
        self.save_history([])

    def add_entry(self, command: str, args: list, status: str = "success"):
        history = self.load_history()
        entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "arguments": args,
            "status": status
        }
        history.append(entry)
        self.save_history(history)

class GeminiClient:
    """Handles interaction with the new Google Gemini SDK (google-genai)."""
    def __init__(self, api_key: str, model_name: str):
        if not HAS_DEPS:
            raise ImportError("Dependencies 'google-genai' and 'python-dotenv' are not installed.")
        if not api_key:
            raise ValueError("API Key is missing. Please set GEMINI_API_KEY in .env or environment.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def query(self, prompt: str, retries: int = 3) -> str:
        for attempt in range(retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    if attempt < retries - 1:
                        wait_time = (attempt + 1) * 2
                        print(f"Quota exceeded. Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        return f"Error: Quota exhausted for model '{self.model_name}'. Please wait a moment or try a different model using the --model flag.\nDetails: {err_msg}"
                return f"Error: {err_msg}"
        return "Error: Maximum retries reached."

    def list_models(self) -> list:
        try:
            models = self.client.models.list()
            return [m.name for m in models]
        except Exception as e:
            return [f"Error listing models: {str(e)}"]

def create_parser():
    parser = argparse.ArgumentParser(description="Gemini CLI Agent", prog="agent")
    current_default = get_default_model()
    parser.add_argument("--model", type=str, default=current_default, help=f"Gemini model to use (default: {current_default})")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Summarize command
    summarize_parser = subparsers.add_parser("summarize", help="Summarize a file's content")
    summarize_parser.add_argument("file", type=str, help="Path to the file to summarize")

    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate content based on a prompt")
    generate_parser.add_argument("prompt", type=str, help="The generation prompt")
    generate_parser.add_argument("--output", "-o", type=str, help="Path to save the generated content")

    # Ask command
    ask_parser = subparsers.add_parser("ask", help="Ask a general question")
    ask_parser.add_argument("question", type=str, help="The question to ask")

    # History command
    history_parser = subparsers.add_parser("history", help="Show or reset command history")
    history_subparsers = history_parser.add_subparsers(dest="history_command", help="History subcommands")
    history_subparsers.add_parser("list", help="List command history (default)")
    history_subparsers.add_parser("reset", help="Clear all command history")

    # Models command
    subparsers.add_parser("models", help="List available Gemini models")

    # Config command
    config_parser = subparsers.add_parser("config", help="Manage agent configuration")
    config_subparsers = config_parser.add_subparsers(dest="config_command", help="Config subcommands")
    set_parser = config_subparsers.add_parser("set", help="Set a configuration value")
    set_parser.add_argument("key", choices=["model"], help="The configuration key to set")
    set_parser.add_argument("value", type=str, help="The value to set")
    
    # Exit command (for REPL)
    subparsers.add_parser("exit", help="Exit the interactive agent")

    return parser

def execute_command(args, api_key, history_mgr):
    if not args.command:
        return True

    if args.command == "exit":
        return False

    try:
        client = None
        if args.command in ["summarize", "generate", "ask", "models"]:
            client = GeminiClient(api_key, model_name=args.model)

        if args.command == "summarize":
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"Error: File '{args.file}' not found.")
                history_mgr.add_entry("summarize", [args.file], "failed")
                return True
            
            content = file_path.read_text()
            prompt = f"Please provide a concise summary of the following content:\n\n{content}"
            result = client.query(prompt)
            print("\n--- Summary ---\n")
            print(result)
            history_mgr.add_entry("summarize", [args.file], "success")

        elif args.command == "generate":
            result = client.query(args.prompt)
            if args.output:
                Path(args.output).write_text(result)
                print(f"Content saved to {args.output}")
            else:
                print("\n--- Generated Content ---\n")
                print(result)
            history_mgr.add_entry("generate", [args.prompt, args.output], "success")

        elif args.command == "ask":
            question = args.question
            context = ""
            referenced_paths = []
            
            words = question.split()
            for word in words:
                if word.startswith("@") and len(word) > 1:
                    path_str = word[1:]
                    p = Path(path_str)
                    if not p.exists():
                        continue
                        
                    referenced_paths.append(path_str)
                    
                    if p.is_file():
                        try:
                            context += f"\n--- Content of {path_str} ---\n{p.read_text()}\n"
                        except Exception as e:
                            print(f"Warning: Could not read file {path_str}: {e}")
                    
                    elif p.is_dir():
                        ignore_dirs = {".git", "venv", "__pycache__", "node_modules"}
                        count = 0
                        for f in p.rglob("*"):
                            if f.is_file() and not any(part in ignore_dirs for part in f.parts):
                                try:
                                    content = f.read_text()
                                    context += f"\n--- Content of {f} ---\n{content}\n"
                                    count += 1
                                    if count >= 30:
                                        context += f"\n... (Limit reached for {path_str}) ...\n"
                                        break
                                except (UnicodeDecodeError, Exception):
                                    continue
                        print(f"Added context from {count} files in @{path_str}")
            
            final_prompt = question
            if context:
                final_prompt = f"Context from files and directories:{context}\n\nQuestion: {question}"
            
            result = client.query(final_prompt)
            print("\n--- Answer ---\n")
            print(result)
            history_mgr.add_entry("ask", [question] + referenced_paths, "success")

        elif args.command == "history":
            if args.history_command == "reset":
                history_mgr.clear_history()
                print("History has been reset.")
            else:
                # Default to listing history
                history = history_mgr.load_history()
                if not history:
                    print("No history found.")
                else:
                    print(f"{'Timestamp':<25} | {'Command':<10} | {'Status':<8} | {'Arguments'}")
                    print("-" * 80)
                    for entry in history:
                        ts = entry['timestamp'][:19].replace('T', ' ')
                        cmd = entry['command']
                        status = entry['status']
                        args_str = ", ".join([str(a) for a in entry['arguments'] if a is not None])
                        print(f"{ts:<25} | {cmd:<10} | {status:<8} | {args_str}")

        elif args.command == "models":
            models = client.list_models()
            print("\n--- Available Gemini Models ---\n")
            for m in models:
                clean_name = m.replace("models/", "")
                print(f"- {clean_name}")
            history_mgr.add_entry("models", [], "success")

        elif args.command == "config":
            if args.config_command == "set":
                if args.key == "model":
                    lines = []
                    if ENV_FILE.exists():
                        lines = ENV_FILE.read_text().splitlines()
                    
                    found = False
                    new_lines = []
                    for line in lines:
                        if line.startswith("DEFAULT_MODEL="):
                            new_lines.append(f"DEFAULT_MODEL={args.value}")
                            found = True
                        else:
                            new_lines.append(line)
                    
                    if not found:
                        new_lines.append(f"DEFAULT_MODEL={args.value}")
                    
                    ENV_FILE.write_text("\n".join(new_lines) + "\n")
                    print(f"Default model updated to: {args.value}")
                    history_mgr.add_entry("config set model", [args.value], "success")

    except Exception as e:
        print(f"Critical Error: {str(e)}")
        if args.command:
            history_mgr.add_entry(args.command, [], "error")
    
    return True

def main():
    if HAS_DEPS:
        load_dotenv(ENV_FILE)
    
    api_key = os.getenv("GEMINI_API_KEY")
    history_mgr = HistoryManager(HISTORY_FILE)
    parser = create_parser()

    # One-shot mode
    if len(sys.argv) > 1:
        args = parser.parse_args()
        execute_command(args, api_key, history_mgr)
        return

    # Stdin / Interactive mode
    is_tty = sys.stdin.isatty()
    if is_tty:
        print("Gemini CLI Agent - Interactive Mode (type 'exit' to quit)")
    
    while True:
        try:
            if is_tty:
                line = input("agent> ")
            else:
                line = sys.stdin.readline()
                if not line:
                    break
            
            line = line.strip()
            if not line:
                continue
            
            # shlex.split handles quotes correctly
            cmd_args = shlex.split(line)
            
            # argparse might call sys.exit() on error or --help, we need to catch it
            try:
                args = parser.parse_args(cmd_args)
                if not execute_command(args, api_key, history_mgr):
                    break
            except SystemExit:
                # argparse already printed the error/help
                continue
                
        except (EOFError, KeyboardInterrupt):
            if is_tty:
                print("\nExiting...")
            break
        except Exception as e:
            print(f"Error processing input: {e}")

if __name__ == "__main__":
    main()
