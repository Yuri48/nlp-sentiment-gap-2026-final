# How the production LLM labels were generated (sub-agent runner)

No Anthropic API key was available on the course machine, so the frozen prompt
`prompts/classify_v1.md` was executed by Claude Code sub-agents inside the authoring session.
The procedure is mechanical and fully specified so that it can be audited or re-run with
`src/classify_llm.py` (API backend, same prompt, same model id).

1. `src/make_llm_batches.py` writes `data/processed/llm/in/batch_####.json` (≤ 40 items each)
   and `manifest.csv` (item → batch, kind, month). Seed 20261014.
2. For each group of batches, a sub-agent (model `claude-haiku-5-5`, temperature not
   controllable in this mode) receives the instruction below, reads the prompt file and the batch
   file, and writes `data/processed/llm/out/batch_####.json` containing only the JSON array.
3. `src/merge_llm_outputs.py` validates every record against the scheme (allowed values, one
   record per input id, non-empty topics when relevant) and rejects invalid ones; rejected
   batches are re-run.
4. The verbatim instruction given to each sub-agent:

```
You are a research coder. Read /…/prompts/classify_v1.md. For each batch file listed below, read
the JSON array of items in it, apply the coding scheme in the prompt to EVERY item exactly as the
prompt specifies, and write the resulting JSON array (one object per input item, same order,
exactly the keys listed in the prompt) to the corresponding output path. Do not skip items, do
not add commentary, do not change ids. Write valid JSON only.
Batches: data/processed/llm/in/batch_0001.json -> data/processed/llm/out/batch_0001.json, …
```

5. Model/version record: `claude-haiku-5-5` via Claude Code 2.1.152 sub-agents, October 2026.
   Perturbation (name-swap / source-label) tests use the same runner on the files produced by
   `src/perturbation_test.py`.
