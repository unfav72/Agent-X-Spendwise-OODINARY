"""
Spendwise AI - Entry Point & CLI Judging Contract
Mandatory contract:
  python main.py "your question"            human-readable run
  python main.py --json "your question"     machine output: ONE JSON line on stdout (Judges' harness)
  python main.py --dry-run "anything"       offline evaluation without API keys
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from agent.core import AgentExecutor
from agent.llm import LLM, DryRunLLM
from tools import build_tools

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_agent(query: str, dry_run: bool = False, verbose: bool = False):
    llm = DryRunLLM() if dry_run else LLM()
    return AgentExecutor(llm, build_tools()).run(query, verbose=verbose)

def main():
    ap = argparse.ArgumentParser(description="Spendwise AI - Autonomous Financial Auditor")
    ap.add_argument("query", nargs="?", default=None, help="Financial investigation question")
    ap.add_argument("--json", action="store_true", help="Print machine-readable JSON on stdout for judging harness")
    ap.add_argument("--dry-run", action="store_true", help="Run with autonomous deterministic LLM without API keys")
    ap.add_argument("--ui", "--serve", dest="serve_ui", action="store_true", help="Start the Spendwise AI web dashboard server")
    args = ap.parse_args()

    if args.serve_ui or (args.query is None and not args.json):
        import subprocess
        port = int(os.environ.get("PORT", 8501))
        print(f"Launching Spendwise AI Streamlit Dashboard on port {port}...", file=sys.stderr)
        subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py", "--server.port", str(port)])
        return

    # Determine if dry run mode should be active
    is_dry = args.dry_run or bool(os.environ.get("AGENTX_DRY_RUN"))
    if not is_dry and not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY")):
        # If no keys configured in environment, gracefully fall back to autonomous DryRun mode
        is_dry = True

    try:
        answer, trace = run_agent(args.query, dry_run=is_dry, verbose=not args.json)
    except Exception as e:
        answer, trace = f"Agent error: {type(e).__name__}: {e}", []
        print(f"Error during agent run: {e}", file=sys.stderr)

    if args.json:
        # Output exactly ONE valid JSON line on stdout, no extra characters or markdown
        sys.stdout.write(json.dumps({"answer": answer, "trace": trace}) + "\n")
        sys.stdout.flush()
    else:
        print(f"\n==========================================")
        print(f"SPENDWISE AI AUDIT REPORT")
        print(f"==========================================")
        print(f"QUESTION: {args.query}")
        print(f"\nAUDIT FINDINGS:\n{answer}\n")
        print(f"Tools Executed: {len(trace)}")
        for i, step in enumerate(trace, 1):
            print(f"  [{i}] Tool: {step.get('tool')} | Args: {step.get('args')}")
        print(f"==========================================\n")

if __name__ == "__main__":
    main()
