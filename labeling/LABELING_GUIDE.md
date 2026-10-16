# Human labeling guide — economic narrative coding (scheme v1.0)

This guide accompanies `labeling/human_label_sample.xlsx`, a stratified sample of **320 items**
(news headlines and social posts) drawn from the project corpus. Two annotators code the sample
**independently**, without discussing items, using only the text, the source and the date shown.
The sheet hides every machine label. Expected effort: 2–3 hours per annotator.

## 1. Who should annotate

Two people with basic economic literacy (they know what inflation, unemployment and the Fed
are). Annotators must **not** have seen the AI labels and must not consult each other until
adjudication. Record each annotator's initials in the sheet header.

## 2. What you see

Each row shows: `item_id`, `kind` (news / social), `source` (news domain, or "bluesky"), `date`,
and `text`. Do not open the URL. Code the text as a reader of that single line would.

## 3. What you code (one column per field — see `prompts/coding_scheme.md` for full definitions)

1. **relevant** (0/1). Is this about US economic conditions or their causes? If 0, leave the
   remaining columns blank.
2. **tone** (−1 / 0 / +1). Direction of the economic message for a typical US household.
3. **emotional** (0 / 1 / 2). Intensity of the wording, independent of tone.
4. **topics**. One or more codes separated by `;` from:
   `jobs_loss; jobs_gain; prices_up; prices_down; growth; recession; rates; housing; wages_income; tariffs_trade; markets; gov_policy; other_econ`.
5. **frame_level_rate** (level / rate / both / na). Only for price items.
6. **frame_scope** (national / household / both / na).
7. **frame_time** (current / forecast / both / na).
8. **numeric_claim** (0/1) and, if 1, **claims** written as `indicator=value@period`, e.g.
   `unemployment_rate=4.3@2026-08`; separate several claims with `;`.
9. **attribution_actor** and **attribution_valence** (see scheme).
10. **post_type** (social items only).
11. **evidence**: copy up to 12 words that justify your tone code.
12. **notes** (optional): anything ambiguous.

## 4. Worked examples

| Text | relevant | tone | emotional | topics | level_rate | scope | time | actor / valence |
|------|----------|------|-----------|--------|------------|-------|------|-----------------|
| "US adds 162,000 jobs in August, more than double expectations" | 1 | +1 | 0 | jobs_gain | na | national | current | none / none |
| "Inflation stays stubborn at 3.4% as grocery bills squeeze families" | 1 | −1 | 1 | prices_up; wages_income | both | both | current | none / none |
| "Fed hikes rates for first time since 2023, citing inflation" | 1 | 0 | 0 | rates; prices_up | rate | national | current | federal_reserve / neutral_mention |
| "Trump's tariffs are crushing small businesses, owners say" | 1 | −1 | 2 | tariffs_trade | na | household | current | trump_admin / blame |
| "my rent just went up $400 and my raise was 2%. cool cool cool" (post) | 1 | −1 | 1 | housing; wages_income | level | household | current | none / none; post_type personal_experience |
| "Taylor Swift ticket prices hit new record" | 0 | — | — | — | — | — | — | — |
| "What to watch in Thursday's GDP report" | 1 | 0 | 0 | growth | na | national | forecast | none / none |

## 5. Edge cases and decision rules

* **Mixed news.** "Inflation cools but prices remain high" → tone 0, topics `prices_down; prices_up`, level_rate `both`.
* **Markets.** A stock-market move is relevant only when framed as an economic signal
  ("Stocks fall on recession fears" → relevant 1, tone −1, topics `markets; recession`).
  Pure market mechanics ("Nvidia leads tech rally") → relevant 0.
* **Policy without economics.** "Senate passes spending bill" → relevant 1 only if an economic
  consequence is stated; otherwise 0.
* **Attribution.** Blame requires an explicit causal link ("because of", "under", "'s tariffs").
  A politician merely quoted about the economy is `neutral_mention`.
* **Sarcasm/irony** (social): code the intended message.
* **Non-US**: 0 unless the item is about effects on the US economy.
* **Unsure between two codes**: pick the one a neutral reader would choose and add a note.

## 6. Procedure

1. Each annotator codes all 320 rows in their own sheet (`annotator_A`, `annotator_B`).
2. Run `python src/eval_labels.py` — it computes percent agreement, Cohen's κ for every
   single-label field, Krippendorff's α for `topics` (set-valued, Jaccard distance), and lists
   disagreements.
3. **Adjudication.** Both annotators meet and resolve every disagreement by discussion with
   reference to this guide; where no consensus is reached, a third coder decides. The
   adjudicated label is the gold standard. Record the rule used in `notes`; if a rule is
   missing from the guide, add it to the scheme as v1.1 and note which items it affected.
4. The same script then scores the LLM, dictionary and conventional classifiers against the
   gold standard: accuracy, macro-F1, per-class precision/recall, and a breakdown by `kind`
   and by source leaning.

## 7. Ethics

Posts are public and are analysed in aggregate; author handles are stored only in the raw
collection file and are never shown to annotators or reported. No participant data is
collected. The project does not identify individual authors in any output.
