#!/usr/bin/env bash
# run_all.sh — reproduce the full analytical pipeline (after the raw collectors have run).
# Usage: bash run_all.sh            (uses the project virtual environment in .venv)
#        bash run_all.sh collect    (also re-runs the collectors; slow: hours, network-bound)
set -euo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python
if [ "${1:-}" = "collect" ]; then
  $PY src/collect_fred_alfred.py            # FRED controls + ALFRED vintages
  $PY src/collect_michigan.py RB            # Michigan Surveys of Consumers tables
  $PY src/collect_gkg.py                    # GDELT GKG headline slices (resumable)
  $PY src/collect_bluesky.py                # Bluesky posts (resumable)
fi
$PY src/build_macro_panel.py                # macro_monthly.csv, realtime_panel.csv, data_notes.md
$PY src/econ_baseline.py                    # economic-only model, gap, prediction intervals, fig1-3
$PY src/prepare_corpus.py                   # news_items / social_items parquet, corpus_summary.md
$PY src/make_llm_batches.py                 # stratified LLM sample -> data/processed/llm/in/
# LLM labels: either  $PY src/classify_llm.py  (needs ANTHROPIC_API_KEY)  or the sub-agent runner (prompts/subagent_runner.md)
$PY src/merge_llm_outputs.py                # labels_llm.parquet + validation report
$PY src/classify_baselines.py ${BASELINE_MODE:-all}   # VADER, GDELT tone, FinBERT, Twitter-RoBERTa, TF-IDF+LR  (fast = skip transformers)
$PY src/build_media_indices.py              # media_monthly.csv, claims_checked.csv
$PY src/models.py                           # three models, OOS tests, asymmetry, lead-lag, partisan; fig4-8
$PY src/perturbation_test.py eval           # name-swap / source-label robustness (after its batches are labelled)
$PY src/make_labeling_sample.py             # 320-item human labeling workbook
$PY src/eval_labels.py                      # agreement + AI performance (needs filled workbook)
$PY src/build_dashboard.py                  # dashboard/index.html
$PY src/md_to_docx.py report/report.md report/Report.docx   # Word report
$PY src/md_to_pdf.py report/report.md report/Report.pdf     # PDF report (headless Chrome)
$PY src/build_slides.py presentation/slides.md presentation/Presentation.pptx
echo "pipeline complete"
