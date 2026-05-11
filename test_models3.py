#!/usr/bin/env python3
"""Quick test – verify NVIDIA NIM API key + a few models."""

import os
from openai import OpenAI

# Load .env file
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ[k.strip()] = v.strip().strip("'\"")

API_KEY  = os.environ.get("NVIDIA_API_KEY", "")
BASE_URL = "https://integrate.api.nvidia.com/v1"

MODELS_TO_TEST = [
    "meta/llama-3.1-8b-instruct",
    "mistralai/mistral-7b-instruct-v0.3",
    "microsoft/phi-3.5-mini-instruct",
]

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

for model in MODELS_TO_TEST:
    print(f"Testing: {model} ... ", end="", flush=True)
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Reply with just 'OK'."}],
            max_tokens=10,
        )
        reply = resp.choices[0].message.content.strip()
        print(f"✔  → {reply}")
    except Exception as e:
        print(f"✗  → {e}")
