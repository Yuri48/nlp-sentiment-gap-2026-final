"""
classify_llm.py — Run the frozen prompt (prompts/classify_v1.md) over the batch files with the
Anthropic Messages API and write one output file per batch.

    python src/classify_llm.py --model claude-haiku-5-5 [--limit 10] [--batches 1-50]

Requires ANTHROPIC_API_KEY.  Output: data/processed/llm/out/batch_####.json (the JSON array the
model returned) and data/processed/llm/raw/batch_####.txt (verbatim response + model id + usage).

Note on provenance: the production labels in this repository were generated with the SAME prompt
and model id by Claude Code sub-agents (see prompts/subagent_runner.md), because no API key was
available on the course machine.  This script reproduces the labels through the public API.
"""
import argparse, glob, json, os, re, sys, time, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LLM = os.path.join(ROOT, 'data', 'processed', 'llm')
PROMPT = open(os.path.join(ROOT, 'prompts', 'classify_v1.md'), encoding='utf-8').read().split('---', 1)[1].strip()


def build_prompt(items):
    return PROMPT.replace('{{ITEMS_JSON}}', json.dumps(items, ensure_ascii=False, indent=0))


def parse_json_array(text):
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text)
    start, end = text.find('['), text.rfind(']')
    return json.loads(text[start:end + 1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', default='claude-haiku-5-5')
    ap.add_argument('--limit', type=int, default=None)
    ap.add_argument('--batches', default=None, help='e.g. 1-50')
    args = ap.parse_args()
    import anthropic
    client = anthropic.Anthropic()
    os.makedirs(os.path.join(LLM, 'out'), exist_ok=True); os.makedirs(os.path.join(LLM, 'raw'), exist_ok=True)
    files = sorted(glob.glob(os.path.join(LLM, 'in', 'batch_*.json')))
    if args.batches:
        lo, hi = [int(x) for x in args.batches.split('-')]
        files = [f for f in files if lo <= int(re.search(r'(\d+)', os.path.basename(f)).group(1)) <= hi]
    done = 0
    for fn in files:
        out_fn = fn.replace('/in/', '/out/')
        if os.path.exists(out_fn):
            continue
        items = json.load(open(fn, encoding='utf-8'))
        for attempt in range(4):
            try:
                resp = client.messages.create(model=args.model, max_tokens=8000, temperature=0,
                                              messages=[{'role': 'user', 'content': build_prompt(items)}])
                text = resp.content[0].text
                arr = parse_json_array(text)
                assert len(arr) == len(items), f'{len(arr)} != {len(items)}'
                break
            except Exception as e:
                print(f'{os.path.basename(fn)} attempt {attempt}: {e}', flush=True); time.sleep(5 * (attempt + 1))
        else:
            continue
        json.dump(arr, open(out_fn, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        with open(fn.replace('/in/', '/raw/').replace('.json', '.txt'), 'w', encoding='utf-8') as f:
            f.write(f'model={resp.model} time={dt.datetime.now().isoformat()} usage={resp.usage}\n\n{text}')
        done += 1
        print(f'{os.path.basename(fn)}: {len(arr)} labels', flush=True)
        if args.limit and done >= args.limit:
            break


if __name__ == '__main__':
    main()
