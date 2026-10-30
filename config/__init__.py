"""Runtime settings for Spendwise AI."""
import os

MAX_ITERATIONS = 6          # Hard cap on reasoning steps
MAX_SAME_TOOL_CALLS = 2     # Force final answer after repeated calls
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
TEMPERATURE = 0.2
DATA_DIR = os.environ.get("AGENTX_DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))

