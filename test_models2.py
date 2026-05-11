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

test_ids = [
    "glm-4.5", "glm-4.5-air", "glm-4.6", "glm-4.7", "glm-4.7-flash",
    "glm-5", "glm-5.1", "glm-5-turbo", "glm-5-code"
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
