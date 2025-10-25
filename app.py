import os, json, gradio as gr
from validator import validate, repair
from theory_map import BUNDLED_THEORY

def get_client():
    try:
        from openai import OpenAI
    except Exception as e:
        raise RuntimeError(f"OpenAI SDK not installed: {e}")
    key = os.environ.get("OPENAI_API_KEY","").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY not found. Add it in Settings → Secrets, then Restart.")
    org = os.environ.get("OPENAI_ORG_ID","").strip()
    return OpenAI(api_key=key, organization=org) if org else OpenAI(api_key=key)

MODEL_NAME = os.environ.get("MODEL_NAME","gpt-4o-mini")

with open("oracle_prompt.txt","r",encoding="utf-8") as f:
    BASE_PROMPT = f.read()

THEORY_TEXT = BUNDLED_THEORY

def make_prompt():
    return BASE_PROMPT.replace("{{CITABLE_THEORY}}", THEORY_TEXT)

def call_model(q: str, extra_system: str | None = None):
    client = get_client()
    JSON_ONLY_NUDGE = ("Return json only. Output a single JSON object with the required keys; "
                       "do not include markdown fences or commentary. The word 'json' appears here.")
    messages = [
        {"role":"system","content":make_prompt()},
        {"role":"system","content":JSON_ONLY_NUDGE},
        {"role":"system","content":"When you cite, quote verbatim from the CITABLE ACTIVE THEORY if possible."}
    ]
    if extra_system:
        messages.append({"role":"system","content":extra_system})
    messages.append({"role":"user","content":q})

    resp = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0,
        response_format={"type":"json_object"},
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
        try:
            draft = call_model(q, extra_system="Add at least one informative relation and cite relevant axioms (ND*, Schema_*, etc.).")
        except Exception as e:
            return f"API error (retry): {e}", "[]", "[]", "[]"
        draft = repair(draft)

    violations = validate(draft)
    if violations:
        try:
            draft = call_model(q, extra_system="Violations: " + "; ".join(violations) + " | Revise to satisfy all constraints.")
        except Exception as e:
            return f"API error (revise): {e}", "[]", "[]", "[]"
        draft = repair(draft)
        violations = validate(draft)

    if violations:
        return "Oracle remains silent (inconsistent).", json.dumps(draft, indent=2, ensure_ascii=False), json.dumps(violations, indent=2, ensure_ascii=False), "[]"

    answer = (draft.get("answer","") or "").strip()
    claims = json.dumps(draft.get("claims",[]), indent=2, ensure_ascii=False)
    citations = json.dumps(draft.get("citations",[]), indent=2, ensure_ascii=False)
    return answer, claims, "[]", citations

def load_theory(file_obj):
    global THEORY_TEXT
    try:
        THEORY_TEXT = file_obj.decode("utf-8")
        return "Loaded new theory.", THEORY_TEXT[:1200] + ("..." if len(THEORY_TEXT)>1200 else "")
    except Exception as e:
        return f"Failed to load: {e}", ""

with gr.Blocks(title="Oracle of Delphi (Ω) — Nondual Core Edition") as demo:
    gr.Markdown("# Oracle of Delphi (Ω) — Nondual Core Edition\nActive Theory is the Nondual Core symbolic extraction (ND*, Schema_*). Upload to hot-swap.")
    with gr.Row():
        q = gr.Textbox(label="Your question", lines=2)
    ask = gr.Button("Ask")
    a = gr.Textbox(label="Answer", lines=8)
    c = gr.Code(label="Claims (JSON)")
    v = gr.Code(label="Violations")
    z = gr.Code(label="Citations (Axioms/Theorems)")
    ask.click(oracle_ask, inputs=[q], outputs=[a,c,v,z])

    with gr.Accordion("Theory Loader", open=False):
        up = gr.File(label="Upload .thy / .md (text)", file_types=[".thy",".md",".txt"])
        load_btn = gr.Button("Load as active theory")
        status = gr.Textbox(label="Load status")
        preview = gr.Code(label="Active theory preview (head)")
        load_btn.click(load_theory, inputs=[up], outputs=[status, preview])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT","7860")))
