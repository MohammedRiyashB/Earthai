import json
import httpx
from .config import MODE, BASE_URL, API_KEY, MODEL, TEMPERATURE, MAX_TOKENS

SYSTEM = "You are EARTH AI, a helpful, honest and capable assistant. Answer clearly. Admit uncertainty. Use Markdown when useful."

async def generate(messages):
    if MODE == "mock":
        for part in ("EARTH AI backend is connected. ", "This is development simulator output, not a real model. ", "Configure MODEL_BASE_URL and MODEL_NAME to connect your own inference engine."):
            yield part
        return
    if not BASE_URL:
        raise RuntimeError("Model endpoint is missing. Configure MODEL_BASE_URL in backend/.env.")
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    payload = {"model": MODEL, "messages": [{"role":"system","content":SYSTEM}, *messages], "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS, "stream": True}
    async with httpx.AsyncClient(timeout=httpx.Timeout(120, connect=20)) as client:
        async with client.stream("POST", BASE_URL + "/chat/completions", headers=headers, json=payload) as r:
            if r.status_code >= 400:
                detail = (await r.aread()).decode(errors="replace")[:700]
                raise RuntimeError(f"Model endpoint HTTP {r.status_code}: {detail}")
            async for line in r.aiter_lines():
                if not line.startswith("data:"):
                    continue
                raw = line[5:].strip()
                if raw == "[DONE]":
                    break
                try:
                    obj = json.loads(raw)
                    token = obj["choices"][0].get("delta", {}).get("content", "")
                    if isinstance(token, str) and token:
                        yield token
                except (ValueError, KeyError, IndexError, TypeError):
                    continue
