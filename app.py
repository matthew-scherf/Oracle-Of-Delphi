import os, json, gradio as gr
from dotenv import load_dotenv
from validator import validate

load_dotenv()
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception:
    client = None

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
with open("oracle_prompt.txt","r",encoding="utf-8") as f:
    ORACLE_PROMPT = f.read()

def call_model(q: str):
    # Extra system nudge so JSON mode passes API validation
    JSON_ONLY_NUDGE = (
        "Return json only. Output a single JSON object with the required keys; "
        "do not include markdown fences or any extra commentary."
    )

    r = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": ORACLE_PROMPT},
            {"role": "system", "content": JSON_ONLY_NUDGE},  # ensures 'json' appears in messages
            {"role": "user", "content": q}
        ]
    )
    return json.loads(r.choices[0].message.content)


from validator import validate, repair

from validator import validate, repair

def oracle_ask(q: str):
    if not q.strip():
        return "Ask something.", "[]", "[]"

    try:
        draft = call_model(q)
    except Exception as e:
        return f"API error: {e}", "[]", "[]"

    # Normalize/auto-complete before validating
    draft = repair(draft)
    violations = validate(draft)

    if violations:
        return (
            "Oracle remains silent (inconsistent).",
            json.dumps(draft, indent=2),
            json.dumps(violations, indent=2),
        )

    # Merge layers for display
    ultimate = draft.get("answer_ultimate", "") or draft.get("answer", "")
    conventional = draft.get("answer_conventional", "")
    guidance = draft.get("guidance_steps", [])

    combined = ultimate
    if conventional:
        combined += ("\n\n" + conventional)

    return combined.strip(), json.dumps(draft.get("claims", []), indent=2), json.dumps(guidance, indent=2)



with gr.Blocks(title="Oracle of Delphi (Ω)") as demo:
    gr.Markdown("# Oracle of Delphi (Ω)")
    q = gr.Textbox(label="Your question")
    b = gr.Button("Ask")
    a = gr.Textbox(label="Answer")
    c = gr.Code(label="Claims (JSON)")
    v = gr.Code(label="Violations")
    b.click(oracle_ask, [q], [a,c,v])

if __name__=="__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT",7860)))
