import os, json, gradio as gr
from validator import validate, repair
from theory_map import SYMBOLIC_LOGIC_MD

def get_client():
    try:
        from openai import OpenAI
    except Exception as e:
        raise RuntimeError(f"OpenAI SDK not installed: {e}")
    key = os.environ.get("OPENAI_API_KEY","").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY not found. Add it in Settings → Variables and secrets → Secrets, then Restart Space.")
    org = os.environ.get("OPENAI_ORG_ID","").strip()
    if org:
        return OpenAI(api_key=key, organization=org)
    return OpenAI(api_key=key)

MODEL_NAME = os.environ.get("MODEL_NAME","gpt-4o-mini")

with open("oracle_prompt.txt","r",encoding="utf-8") as f:
    ORACLE_PROMPT = f.read()

def call_model(q: str, extra_system: str | None = None):
    client = get_client()
    JSON_ONLY_NUDGE = (
        "Return json only. Output a single JSON object with the required keys; "
        "do not include markdown fences or any extra commentary."
    )
    messages = [
        {"role": "system", "content": ORACLE_PROMPT},
        {"role": "system", "content": JSON_ONLY_NUDGE},
        {"role": "system", "content": "When you cite, quote verbatim from the CITABLE THEORY if possible."}
    ]
    if extra_system:
        messages.append({"role": "system", "content": extra_system})
    messages.append({"role": "user", "content": q})

    resp = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0,
        response_format={"type": "json_object"},
        messages=messages
    )
    return json.loads(resp.choices[0].message.content)

def oracle_ask(q: str):
    if not q.strip():
        return "Ask something.", "[]", "[]", "[]"
    try:
        draft = call_model(q)
    except Exception as e:
        return f"API error: {e}", "[]", "[]", "[]"

    draft = repair(draft)

    if not draft.get("claims"):
        draft = call_model(q, extra_system="Add at least one informative relation and cite relevant axioms (e.g., D1, T4). Return json only.")

    violations = validate(draft)

    if violations:
        hint = (
            "Revise to satisfy all constraints. Include at least ONE informative relation in `claims` "
            "(Applies/Owns/HasCoords/CausallyPrecedes/ArisesFrom/LT). Add citations referencing the theory."
        )
        try:
            draft = call_model(q, extra_system="Violations: " + "; ".join(violations) + " | " + hint)
        except Exception as e:
            return f"API error (revise): {e}", "[]", "[]", "[]"

        draft = repair(draft)
        violations = validate(draft)

    if violations:
        return "Oracle remains silent (inconsistent).", json.dumps(draft, indent=2), json.dumps(violations, indent=2), "[]"

    answer = draft.get("answer","").strip()
    claims = json.dumps(draft.get("claims",[]), indent=2)
    citations = json.dumps(draft.get("citations",[]), indent=2)
    return answer, claims, "[]", citations

with gr.Blocks(title="Oracle of Delphi (Ω) — Cited") as demo:
    gr.Markdown("# Oracle of Delphi (Ω) — Cited Reasoning")
    q = gr.Textbox(label="Your question", lines=2)
    b = gr.Button("Ask")
    a = gr.Textbox(label="Answer", lines=6)
    c = gr.Code(label="Claims (JSON)")
    v = gr.Code(label="Violations")
    z = gr.Code(label="Citations (Axioms/Theorems)")
    b.click(oracle_ask, inputs=[q], outputs=[a,c,v,z])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT","7860")))
