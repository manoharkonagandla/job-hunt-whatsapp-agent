"""
The actual agent: prompt + tools + memory.

Flow for every incoming WhatsApp message:
  1. Pull recent conversation history for this phone number (memory)
  2. Send it + the new message to Claude, with a small toolset it can call
  3. Run whichever tool Claude decides on (log a new application, update a
     status, or look applications up)
  4. Feed the tool result back so Claude can write the reply in plain English
  5. Save both sides of the exchange to memory
"""
import os
import json
from datetime import datetime
import anthropic

from . import db

MODEL = "claude-sonnet-4-6"
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """You are Manohar's personal job-hunt assistant on WhatsApp.

He forwards you messages like "applied to Swiggy for SDE role" or "Jumbo
called me for an interview" or "got rejected by Razorpay". Your job:

1. Log new applications and status changes using the tools you have.
2. If he asks a question ("what have I applied to this month?", "what's
   still pending?"), look it up and answer in a short, casual WhatsApp
   style — not a formal report. Use bullet points sparingly, prefer plain
   sentences.
3. If a message is unrelated to job hunting, just reply naturally and
   briefly — don't force it into a tool call.

Company and role names should be title-cased and cleaned up (e.g. "swiggy"
-> "Swiggy"). If no role is mentioned, leave it blank. Default status for a
new application is "applied". Valid statuses: applied, interviewing,
offer, rejected, withdrawn.

Keep replies under 3 sentences unless he's asked for a list.
"""

TOOLS = [
    {
        "name": "log_application",
        "description": "Record a new job application.",
        "input_schema": {
            "type": "object",
            "properties": {
                "company": {"type": "string"},
                "role": {"type": "string"},
                "status": {"type": "string", "enum": ["applied", "interviewing", "offer", "rejected", "withdrawn"]},
            },
            "required": ["company"],
        },
    },
    {
        "name": "update_status",
        "description": "Update the status of an application already on file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "company": {"type": "string"},
                "status": {"type": "string", "enum": ["applied", "interviewing", "offer", "rejected", "withdrawn"]},
            },
            "required": ["company", "status"],
        },
    },
    {
        "name": "list_applications",
        "description": "Look up applications on file, optionally limited to the last N days.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Only include applications from the last N days. Omit for all-time."},
            },
        },
    },
]


def _run_tool(user_phone: str, name: str, args: dict) -> str:
    if name == "log_application":
        db.add_application(user_phone, args["company"].strip().title(),
                            args.get("role"), args.get("status", "applied"))
        return f"Logged: {args['company'].title()} ({args.get('status', 'applied')})"

    if name == "update_status":
        ok = db.update_status(user_phone, args["company"], args["status"])
        return "Updated." if ok else f"Couldn't find an application matching '{args['company']}'."

    if name == "list_applications":
        rows = db.list_applications(user_phone, args.get("days"))
        if not rows:
            return "No applications on file for that period."
        lines = [f"- {r['company']} ({r['role'] or 'role n/a'}): {r['status']}, applied {r['applied_on'][:10]}"
                 for r in rows]
        return "\n".join(lines)

    return "Unknown tool."


def handle_message(user_phone: str, text: str) -> str:
    db.add_message(user_phone, "user", text)
    history = db.recent_messages(user_phone, limit=10)

    messages = [{"role": "user" if m["role"] == "user" else "assistant", "content": m["content"]}
                for m in history]

    # Agent loop: let Claude call tools until it's ready to just reply in text.
    for _ in range(4):
        response = client.messages.create(
            model=MODEL,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            reply = "".join(block.text for block in response.content if block.type == "text").strip()
            db.add_message(user_phone, "agent", reply)
            return reply

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = _run_tool(user_phone, block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })
        messages.append({"role": "user", "content": tool_results})

    fallback = "Sorry, got a bit stuck on that one — try rephrasing?"
    db.add_message(user_phone, "agent", fallback)
    return fallback
