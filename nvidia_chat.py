#!/usr/bin/env python3
"""
NVIDIA NIM Terminal Chatbot
Uses the OpenAI-compatible NVIDIA NIM API (https://integrate.api.nvidia.com/v1)
Supports streaming, multi-turn conversation, and model switching.
"""

import os
import sys
import time
import threading

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Load .env file manually if python-dotenv is not installed
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ[k.strip()] = v.strip().strip("'\"")

API_KEY  = os.environ.get("NVIDIA_API_KEY", "")
BASE_URL = "https://integrate.api.nvidia.com/v1"

# Models confirmed available on integrate.api.nvidia.com/v1
# Speed: ⚡ = fast response, 🔥 = recommended, 🐢 = large/slower
MODELS = [
    # ── ⚡ Fast & Recommended ───────────────────────────────────────────────
    ("meta/llama-3.1-8b-instruct",             "⚡ Llama-3.1 8B       — Meta, ultra-fast"),
    ("openai/gpt-oss-20b",                     "⚡ GPT-OSS 20B        — OpenAI OSS, fast"),
    ("google/gemma-3-12b-it",                  "⚡ Gemma-3 12B        — Google, compact"),
    ("microsoft/phi-4-mini-instruct",          "⚡ Phi-4 Mini         — Microsoft, compact"),
    ("deepseek-ai/deepseek-v4-flash",          "⚡ DeepSeek-V4 Flash  — DeepSeek, fast"),
    ("stepfun-ai/step-3.5-flash",              "⚡ Step-3.5 Flash     — StepFun AI"),
    # ── 🔥 Balanced (good quality + decent speed) ──────────────────────────
    ("meta/llama-4-maverick-17b-128e-instruct","🔥 Llama-4 Maverick   — Meta, 128-expert MoE     ⭐"),
    ("meta/llama-3.3-70b-instruct",            "🔥 Llama-3.3 70B     — Meta, all-rounder"),
    ("meta/llama-3.1-70b-instruct",            "🔥 Llama-3.1 70B     — Meta, balanced"),
    ("google/gemma-4-31b-it",                  "🔥 Gemma-4 31B       — Google, latest"),
    ("google/gemma-3-27b-it",                  "🔥 Gemma-3 27B       — Google"),
    ("mistralai/mistral-small-4-119b-2603",    "🔥 Mistral-Small-4   — Mistral, efficient"),
    ("mistralai/mistral-nemotron",             "🔥 Mistral-Nemotron  — Mistral × NVIDIA"),
    ("nvidia/llama-3.3-nemotron-super-49b-v1.5","🔥 Nemotron-Super 49B — NVIDIA, reasoning"),
    ("nvidia/llama-3.1-nemotron-70b-instruct", "🔥 Nemotron-70B      — NVIDIA, RLHF-tuned"),
    ("openai/gpt-oss-120b",                    "🔥 GPT-OSS 120B     — OpenAI open-source"),
    ("qwen/qwen2.5-coder-32b-instruct",        "🔥 Qwen-2.5 Coder   — Alibaba, coding"),
    # ── 🐢 Large / Slower (highest quality) ────────────────────────────────
    ("deepseek-ai/deepseek-v4-pro",            "🐢 DeepSeek-V4 Pro   — DeepSeek, flagship"),
    ("mistralai/mistral-large-3-675b-instruct-2512", "🐢 Mistral-Large 675B — Mistral, biggest"),
    ("mistralai/mistral-medium-3.5-128b",      "🐢 Mistral-Medium 3.5 — Mistral"),
    ("mistralai/mixtral-8x22b-instruct-v0.1",  "🐢 Mixtral 8×22B     — Mistral, MoE"),
    ("qwen/qwen3.5-397b-a17b",                 "🐢 Qwen-3.5 397B    — Alibaba, massive"),
    ("qwen/qwen3-coder-480b-a35b-instruct",    "🐢 Qwen-3 Coder 480B — Alibaba, coding"),
    ("nvidia/llama-3.1-nemotron-ultra-253b-v1","🐢 Nemotron-Ultra 253B — NVIDIA, top-tier"),
    ("nvidia/nemotron-3-super-120b-a12b",      "🐢 Nemotron-3 Super  — NVIDIA, MoE"),
    ("moonshotai/kimi-k2-instruct",            "🐢 Kimi-K2           — Moonshot AI"),
    ("moonshotai/kimi-k2-thinking",            "🐢 Kimi-K2 Thinking  — Moonshot, reasoning"),
    # ── GLM (also available here!) ──────────────────────────────────────────
    ("z-ai/glm-5.1",                           "🔥 GLM-5.1           — Z.ai / ZhipuAI"),
    ("z-ai/glm5",                              "🔥 GLM-5             — Z.ai / ZhipuAI"),
    ("z-ai/glm4.7",                            "⚡ GLM-4.7           — Z.ai / ZhipuAI"),
]

SYSTEM_PROMPT = "You are a helpful, harmless, and honest AI assistant."

# ---------------------------------------------------------------------------
# ANSI colours (disable when not a TTY)
# ---------------------------------------------------------------------------
USE_COLOR = sys.stdout.isatty()

def c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text

BOLD    = lambda t: c("1",  t)
DIM     = lambda t: c("2",  t)
CYAN    = lambda t: c("96", t)
GREEN   = lambda t: c("92", t)
YELLOW  = lambda t: c("93", t)
RED     = lambda t: c("91", t)
MAGENTA = lambda t: c("95", t)
BLUE    = lambda t: c("94", t)

# ---------------------------------------------------------------------------
# Spinner (shows while waiting for first token)
# ---------------------------------------------------------------------------
class Spinner:
    """Animated spinner that runs in a background thread."""
    FRAMES = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]

    def __init__(self, message="  Thinking"):
        self._msg = message
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def _spin(self):
        i = 0
        while not self._stop.is_set():
            frame = self.FRAMES[i % len(self.FRAMES)]
            if USE_COLOR:
                print(f"\r  {DIM(frame + ' ' + self._msg + '...')}", end="", flush=True)
            self._stop.wait(0.08)
            i += 1

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join()
        # Clear the spinner line
        if USE_COLOR:
            print("\r\033[K", end="", flush=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def banner():
    print()
    print(BOLD(CYAN("╔══════════════════════════════════════════════════════╗")))
    print(BOLD(CYAN("║        NVIDIA NIM Terminal Chatbot  🚀               ║")))
    print(BOLD(CYAN("║    Powered by NVIDIA NIM  (integrate.api.nvidia.com) ║")))
    print(BOLD(CYAN("╚══════════════════════════════════════════════════════╝")))
    print()

def print_model_menu():
    print(BOLD(YELLOW("  Available Models")))
    print(DIM("  ─" * 34))
    for i, (_, label) in enumerate(MODELS, start=1):
        print(f"  {BOLD(GREEN(str(i).rjust(2)))}. {label}")
    print(DIM("  ─" * 34))
    print()

def select_model() -> tuple[str, str]:
    print_model_menu()
    while True:
        try:
            raw = input(BOLD("  Select model [1–{}]: ".format(len(MODELS)))).strip()
            idx = int(raw)
            if 1 <= idx <= len(MODELS):
                model_id, label = MODELS[idx - 1]
                print()
                print(GREEN(f"  ✔  Selected: {label}"))
                print()
                return model_id, label
            else:
                print(RED(f"  ✗  Enter a number between 1 and {len(MODELS)}."))
        except ValueError:
            print(RED("  ✗  Invalid input — enter a number."))
        except (EOFError, KeyboardInterrupt):
            print()
            print(DIM("  Aborted. Goodbye! 👋"))
            sys.exit(0)

def chat_loop(client, model_id: str, model_label: str):
    """Main multi-turn conversation loop with streaming responses."""
    conversation: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    print(BOLD(BLUE("  ┌─── Chat started ───────────────────────────────────────")))
    print(BOLD(BLUE(f"  │  Model   : {model_label}")))
    print(BOLD(BLUE("  │  Input   : type your message and press Enter")))
    print(BOLD(BLUE("  │  Commands: /exit · /clear · /model · /help")))
    print(BOLD(BLUE("  └───────────────────────────────────────────────────────")))
    print()

    while True:
        # ── User input ──────────────────────────────────────────────────────
        try:
            user_input = input(BOLD(CYAN("  You › "))).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            print(DIM("  Session ended. Goodbye! 👋"))
            break

        if not user_input:
            continue

        # ── Slash commands ───────────────────────────────────────────────────
        if user_input.lower() in ("/exit", "/quit", "/bye"):
            print(DIM("  Goodbye! 👋"))
            break

        if user_input.lower() == "/clear":
            conversation = [{"role": "system", "content": SYSTEM_PROMPT}]
            print(YELLOW("  ✔  Conversation history cleared."))
            print()
            continue

        if user_input.lower() == "/model":
            print()
            model_id, model_label = select_model()
            conversation = [{"role": "system", "content": SYSTEM_PROMPT}]
            print(YELLOW("  ✔  Switched model — history cleared."))
            print()
            continue

        if user_input.lower() == "/help":
            print(DIM("  Commands:"))
            print(DIM("    /exit · /quit · /bye — End session"))
            print(DIM("    /clear               — Clear conversation history"))
            print(DIM("    /model               — Switch to a different model"))
            print(DIM("    /help                — Show this help"))
            print()
            continue

        # ── Append user message ─────────────────────────────────────────────
        conversation.append({"role": "user", "content": user_input})

        # ── Stream response ─────────────────────────────────────────────────
        spinner = Spinner("Waiting for response")
        spinner.start()
        got_first_token = False

        full_reply = ""
        try:
            stream = client.chat.completions.create(
                model=model_id,
                messages=conversation,
                stream=True,
                max_tokens=4096,
                temperature=0.7,
            )
            for chunk in stream:
                # Some models send chunks with empty choices (e.g. usage info)
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    if not got_first_token:
                        spinner.stop()
                        got_first_token = True
                        print()
                        print(BOLD(MAGENTA("  NIM › ")), end="", flush=True)
                    token = delta.content
                    print(token, end="", flush=True)
                    full_reply += token
        except KeyboardInterrupt:
            spinner.stop()
            print()
            print(YELLOW("\n  ⚠  Response interrupted."))
            # Keep whatever was received so far
        except Exception as exc:
            spinner.stop()
            print()
            print(RED(f"\n  ✗  API error: {exc}"))
            conversation.pop()   # keep history consistent
            print()
            continue
        finally:
            spinner.stop()

        print("\n")
        if full_reply:
            conversation.append({"role": "assistant", "content": full_reply})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    banner()

    try:
        from openai import OpenAI
    except ImportError:
        print(RED("  ✗  'openai' package not found."))
        print(YELLOW("     Install it with:"))
        print(YELLOW("       pip install openai"))
        sys.exit(1)

    client = OpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
        timeout=60,           # don't hang forever
    )

    model_id, model_label = select_model()
    chat_loop(client, model_id, model_label)


if __name__ == "__main__":
    main()
