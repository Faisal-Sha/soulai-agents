"""Isolate which outbound call fails on this machine."""
import sys
import traceback
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv()

print("Python:", sys.executable)
print("-" * 60)

# --- Test 1: Supabase ---
print("\n[1] Testing Supabase get_chat_history RPC...")
try:
    from app.db.supabase import supabase

    test_user = str(uuid.uuid4())
    test_thread = str(uuid.uuid4())
    resp = supabase.rpc(
        "get_chat_history",
        {"p_thread_id": test_thread, "p_user_id": test_user},
    ).execute()
    print("  OK - returned", len(resp.data or []), "messages")
except Exception:
    print("  FAILED:")
    traceback.print_exc()

# --- Test 2: OpenAI embeddings ---
print("\n[2] Testing OpenAI embeddings...")
try:
    from app.services.embeddings import embed_query

    vec = embed_query("hello")
    print("  OK - vector length", len(vec))
except Exception:
    print("  FAILED:")
    traceback.print_exc()

# --- Test 3: OpenAI chat ---
print("\n[3] Testing OpenAI chat completion...")
try:
    from app.services.llm import llm

    resp = llm.invoke("Say hi in one word")
    print("  OK -", resp.content[:80])
except Exception:
    print("  FAILED:")
    traceback.print_exc()

print("\n" + "-" * 60)
print("Done.")
