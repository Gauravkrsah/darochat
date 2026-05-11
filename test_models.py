from zhipuai import ZhipuAI

import os

# Load .env file
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ[k.strip()] = v.strip().strip("'\"")

client = ZhipuAI(api_key=os.environ.get("ZHIPUAI_API_KEY", ""))

# Test a variety of known model IDs
test_ids = [
    "glm-4-flash",
    "glm-4-flash-250414",
    "glm-4-air",
    "glm-4-air-0111",
    "glm-4",
    "glm-4-plus",
    "glm-4-long",
    "chatglm_turbo",
    "glm-z1-flash",
    "glm-z1-air",
    "glm-z1",
    "glm-z1-air-250414",
    "glm-4-flashx",
]

for mid in test_ids:
    try:
        resp = client.chat.completions.create(
            model=mid,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=5,
            stream=False,
        )
        print(f"✔  {mid}")
    except Exception as e:
        print(f"✗  {mid}: {str(e)[:80]}")
