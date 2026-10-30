"""
Spendwise AI - The Autonomous Agent ReAct Loop
Thought -> Action -> Observation -> Decision -> Evidence Verification -> Final Answer.
"""

import json
import re
import os
import sys

import config
from agent.prompt_builder import build_system_prompt
from database.repository import Repository
from services.transaction_service import TransactionService

def parse_json(text):
    """Pulls the first valid JSON object out of an LLM reply, handling markdown fences and surrounding commentary."""
    if not text:
        return None
    text = re.sub(r"```(?:json)?", "", text)
    start = text.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    break
        start = text.find("{", start + 1)
    return None

class AgentExecutor:
    def __init__(self, llm, tools, role=None, max_iterations=None):
        self.llm, self.tools = llm, tools
        self.max_iterations = max_iterations or config.MAX_ITERATIONS
        self.system = build_system_prompt(tools, **({"role": role} if role else {}))

    def run(self, query, verbose=False):
        messages = [{"role": "user", "content": query}]
        trace, seen, nudged = [], {}, False

        for step in range(self.max_iterations):
            force_final = any(n >= config.MAX_SAME_TOOL_CALLS for n in seen.values())
            if force_final:
                messages.append({"role": "user", "content": "You repeated a tool. Give your final_answer now."})

            reply = self.llm.generate(self.system, messages)
            data = parse_json(reply)

            if data is None or not (data.get("action") or "final_answer" in data):
                messages += [
                    {"role": "assistant", "content": reply or "(empty)"},
                    {"role": "user", "content": "Invalid format. Reply with ONE JSON object with an \"action\" or a \"final_answer\"."}
                ]
                continue

            thought = str(data.get("thought", ""))

            # Guarantee grounding: an agent must execute at least one real tool before giving a final answer
            if "final_answer" in data and not trace and not nudged:
                nudged = True
                messages += [
                    {"role": "assistant", "content": json.dumps(data)},
                    {"role": "user", "content": "Do not answer from memory. Call a financial tool (such as spending_analytics, anomaly_detector, or transaction_search) first."}
                ]
                continue

            if "final_answer" in data:
                if verbose:
                    print(f"[Thought] {thought}\n[Final Answer] {data['final_answer']}", file=sys.stderr)
                return str(data["final_answer"]), trace

            name = data.get("action")
            args = data.get("args") or {}
            key = (name, json.dumps(args, sort_keys=True, default=str))
            seen[key] = seen.get(key, 0) + 1

            observation = self._call_tool(name, args)
            obs_preview = observation[:2000]
            trace.append({
                "thought": thought,
                "tool": name,
                "args": args,
                "observation": obs_preview
            })

            if verbose:
                print(f"[Thought] {thought}\n[Action] {name}({args})\n[Observation] {obs_preview[:300]}...\n", file=sys.stderr)

            messages += [
                {"role": "assistant", "content": json.dumps(data)},
                {"role": "user", "content": f"OBSERVATION: {observation}"}
            ]

        return self._wrap_up(messages), trace

    def _call_tool(self, name, args):
        tool = self.tools.get(name)
        if tool is None:
            return f"ERROR: unknown tool '{name}'. Available: {', '.join(self.tools)}"
        try:
            res = tool.execute(**args)
            if isinstance(res, (dict, list)):
                return json.dumps(res, default=str)
            return str(res)
        except Exception as e:
            # Tool exceptions become observations so the autonomous agent can recover
            return f"ERROR: {type(e).__name__}: {e}"

    def _wrap_up(self, messages):
        """Step limit reached: synthesize final answer from collected observations."""
        messages.append({"role": "user", "content": "Step limit reached. Synthesize an evidence-backed final_answer JSON from the observations."})
        data = parse_json(self.llm.generate(self.system, messages)) or {}
        return str(data.get("final_answer") or "Investigation completed within bounded step limit.")

