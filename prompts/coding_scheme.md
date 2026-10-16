# Coding scheme v1.0 — economic narratives in news headlines and social posts

**Status:** v1.0 frozen before any model was applied (2026-10-14); v1.1 after a 2-batch pilot (see D). Changes require a new version
number; all labels in `data/processed/` record the scheme version they were produced with.

**Unit of analysis.** One *item* = one news headline (GDELT title + source domain + date) or one
social-media post (Bluesky post text + date + engagement counts). Coders see only the text,
the source domain (news) and the date. They do **not** see the URL body, the author handle,
or any other item.

**Purpose.** The scheme operationalises the five measurement dimensions required by the
project brief (tone, selection/salience, framing, factual calibration, political attribution)
so that the same definitions are applied by (i) two human annotators, (ii) an LLM, and
(iii) dictionary / conventional classifiers. Every field below has a *benchmark* — the
comparison that turns a descriptive measurement into a bias test (Section B).

---

## A. Fields

| # | Field | Values | Definition and decision rules |
|---|-------|--------|-------------------------------|
| 0 | `relevant` | 0 / 1 | 1 if the item conveys information or opinion about **US economic conditions** or their causes (prices, jobs, growth, recession, interest rates, housing, wages/income, tariffs/trade, markets as a signal of the economy, government economic policy). 0 for non-US economies, non-economic topics, sports/entertainment, single-product/corporate news with no macro content ("Apple unveils new iPhone"), or ambiguous fragments. A layoff announcement at one company **is** relevant (jobs). All other fields are coded only when `relevant = 1`; otherwise they are `null`. |
| 1 | `tone` | −1 / 0 / +1 | Direction of the economic message **for a typical US household**. −1 = conditions worsening, losses, hardship, risk; +1 = improving, relief, gains; 0 = neutral/mixed/descriptive with no clear direction (e.g., "Fed meets this week", "What to know about the jobs report"). Code the *economic* message, not the writer's politics: "Tariffs push grocery prices higher" = −1 regardless of who is blamed. Falling inflation = +1 unless the item stresses prices remain high (then 0 or −1 depending on emphasis). |
| 2 | `emotional` | 0 / 1 / 2 | Intensity of wording, **independent of tone**. 0 = factual/descriptive (numbers, "rose", "fell", "reports"). 1 = mildly evaluative ("stubborn inflation", "solid hiring", "weak"). 2 = emotional, alarmist or celebratory ("crushing", "nightmare", "soars", "plunges", "crisis", "boom", "disaster", exclamation marks). This separates factual description from emotional wording. |
| 3 | `topics` | list, ≥1 of: `jobs_loss`, `jobs_gain`, `prices_up`, `prices_down`, `growth`, `recession`, `rates`, `housing`, `wages_income`, `tariffs_trade`, `markets`, `gov_policy`, `other_econ` | Salience/selection measure. `prices_up` = inflation rising **or** prices described as high/elevated; `prices_down` = inflation easing/cooling/falling or price cuts; `jobs_loss` = layoffs, unemployment rising, hiring freezes; `jobs_gain` = hiring, payroll gains, unemployment falling; `recession` = recession risk/downturn/slowdown language; `growth` = GDP, expansion, "strong economy"; `rates` = Fed policy, interest or mortgage rates; `gov_policy` = taxes, spending, shutdown, regulation, economic policy debates. Multiple topics allowed. |
| 4 | `frame_level_rate` | `level` / `rate` / `both` / `na` | Only if the item concerns prices/inflation; otherwise `na`. `level` = emphasis on how expensive things are, cumulative increases, "prices remain high", "$7 eggs". `rate` = emphasis on the pace of change, "inflation cooled to 2.9%", "CPI rose 0.3%". `both` when both appear. |
| 5 | `frame_scope` | `national` / `household` / `both` / `na` | `national` = aggregate statistics, the economy as a whole, markets, policy. `household` = individual or family experience: budgets, paychecks, "families struggle", personal anecdotes, a worker's story. `both` if an aggregate is explicitly linked to household experience. |
| 6 | `frame_time` | `current` / `forecast` / `both` / `na` | `current` = past or present conditions (releases, what happened). `forecast` = expectations, projections, risks, what the Fed/economists expect. `both` if explicitly both. |
| 7 | `numeric_claim` | 0 / 1 | 1 if the text states a specific number for an official statistic (unemployment rate, CPI/PCE inflation, GDP growth, jobs added, fed funds rate, gasoline price). Percentages of survey respondents or company-specific numbers do **not** count. |
| 8 | `claims` | list of {`indicator`, `value`, `period`} | Only if `numeric_claim = 1`. `indicator` ∈ {`unemployment_rate`, `cpi_yoy`, `pce_yoy`, `cpi_mom`, `gdp_qoq_ann`, `jobs_added`, `fed_funds`, `gas_price`, `other`}; `value` numeric; `period` as stated ("2026-08", "2026-Q2") or `null`. Used for the factual-calibration check against the official value available on the publication date. |
| 9 | `attribution_actor` | `trump_admin` / `biden_admin` / `congress_republicans` / `congress_democrats` / `federal_reserve` / `corporations` / `foreign_trade_partners` / `other` / `none` | The institution or political actor credited or blamed for economic conditions, **or** the named subject of the report ("Fed holds rates" → `federal_reserve`). `none` if no such actor is named. Criticism is **not** bias: this field records who is held responsible, not whether that is fair. |
| 10 | `attribution_valence` | `credit` / `blame` / `neutral_mention` / `none` | `credit` = actor presented as responsible for something good; `blame` = responsible for something bad; `neutral_mention` = actor named with no responsibility claim ("Fed holds rates"); `none` when `attribution_actor = none`. |
| 11 | `post_type` (social only) | `personal_experience` / `opinion` / `news_share` / `other` / `na` | `personal_experience` = the author's own finances or job ("my rent went up $300"); `opinion` = commentary without personal anecdote; `news_share` = primarily relays a headline/link. News items are always `na`. |
| 12 | `evidence` | string ≤ 12 words | Verbatim words from the item that justify `tone`. Preserved for audit. |

**Ordering rule.** Code `relevant` first. If 0, stop. Then `tone`, then `emotional`, then
the remaining fields. Do not let the source name influence `tone` or `emotional`.

**Tie-break rules.**
* A headline that reports a negative number with relief framing ("Inflation slows to 3%, still above target") → `tone 0`, `frame_level_rate rate`, `topics [prices_down, prices_up]`.
* "Prices are high but inflation is cooling" → `tone 0`, `frame_level_rate both`.
* Questions ("Is a recession coming?") → `tone −1` only if the body/lead presumes the risk; headline-only items coded as `0` with `topics [recession]` and `frame_time forecast`.
* Sarcasm in social posts: code the intended economic message.

## B. Benchmarks — how each dimension becomes a bias test

Measurement alone cannot establish bias; each dimension is compared with an explicit
benchmark (project brief, section 3).

| Dimension | Benchmark | Test |
|-----------|-----------|------|
| Tone | The **direction and size of the official data change** in the same month (Δ unemployment, Δ PCE inflation, latest GDP growth, payroll change). | *Negativity asymmetry (content-level):* regress monthly mean tone on positive and negative data changes separately; a significantly larger response to deteriorations than to equal-sized improvements = negativity asymmetry in **coverage** (not in readers). |
| Tone | The **same release week across sources** (e.g., every outlet covering the August jobs report). | Source fixed effects on tone within release weeks; differences by audience leaning = source-specific slant conditional on identical facts. |
| Salience | Share of `prices_up` vs `prices_down` items compared with the **sign of the change in inflation**; share of `jobs_loss` vs `jobs_gain` compared with the **sign of payroll/unemployment changes**. | Selection asymmetry: does attention to bad-news topics fall as fast when data improve as it rises when data worsen? |
| Framing | **Inflation rate vs price level** in the official data: when the rate falls but the level stays elevated, `level` framing is not evidence of bias; it is evidence of a framing *choice*. | We report the level-vs-rate share and relate it to the sentiment gap; the test of "bias" is whether level framing exceeds what the cumulative price increase alone predicts. |
| Factual calibration | The **official value available on the publication date** (ALFRED vintage, release calendar). Tolerance ±0.2 pp for rates, ±0.5 pp for GDP growth, ±25k for jobs added. | Share of claims that are accurate, stale (true for an earlier period), or wrong; by source. |
| Political attribution | **Symmetry across administrations** for comparable conditions (e.g., inflation ≈ 3% in 2024 under Biden vs 2026 under Trump) and across sources. | Blame/credit shares by actor conditional on tone and on the data; asymmetry by source leaning = slant in attribution. Criticism per se is not bias. |

## C. What the scheme cannot measure

Text can establish framing, tone and selection in **content supply**. It cannot establish a
reader's cognitive bias. Availability or confirmation bias require exposure, recall or belief
data (we use Michigan's "news heard" questions, tables 23–24, as the only recall measure
available) or an experiment (Section 6 of the report). Anchoring to past prices is
measurable only indirectly through `frame_level_rate` and the price-level control in the
model, not as a reader-level trait.

## D. Versions

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-10-14 | Initial scheme, frozen before labeling. |
| 1.1 | 2026-10-14 | After a 2-batch pilot: field 9 now records the named subject actor as well as credited/blamed actors; field 10 `neutral_mention` applies to subject-only mentions. Pilot labels discarded. |
