%% title: Why is consumer sentiment 35 points below the economy?
%% subtitle: AI-measured economic narratives, the sentiment gap and the 2026 midterms — what a forecaster should take from it
%% author: AI Applications in Finance — final project · data cutoff 14 October 2026
%% footer: Sentiment gap project · all figures from data/processed · dashboard/index.html

## The puzzle in one picture
- Michigan sentiment: **46.3** in October 2026 (record low 44.8 in May)
- Unemployment 4.2%, headline PCE inflation 3.4%, real GDP +2.2% (Q2)
- An economic-only model estimated on 1978–2019 says sentiment should be **about 85**
- Three competing explanations, treated as hypotheses: unmeasured pressure, biased information, measurement artefacts
![](figures/fig1_ics_vs_model.png)
> The black line is the Michigan index, the blue line is the one-step-ahead out-of-sample prediction from unemployment, inflation and GDP growth, all as known on the 15th of each month using ALFRED vintages. The bands are empirical intervals because the errors are strongly autocorrelated.

## The sentiment gap
- Gap = actual minus real-time out-of-sample prediction; a negative gap is unexplained pessimism, not proof of bias
- Average gap: −3.5 (2010–19), −23 (2022–24), −31 (2025), **−34 (2026)**; −45 for Current Conditions
- Low unemployment should have added 7 points; inflation subtracted one
- R² of the three-indicator model fell from 0.59 (1978–2019) to 0.26 with 2020–26 included
![](figures/fig2_gap.png)
> The gap opened in 2021 and has not closed. Core versus headline PCE, pseudo versus true real-time data, and the sample start do not change it by more than half a point.

## How we measured the narratives
- 90,000+ unique US economic headlines from systematic GDELT 15-minute slices; 38,000 Bluesky posts (9 consumer-economy queries); supply, not exposure
- Frozen coding scheme, five dimensions with explicit benchmarks: tone, salience, framing, factual calibration, political attribution
- LLM (Claude Haiku 5.5, frozen prompt) on a stratified monthly sample; GDELT tone, VADER, FinBERT, tweet-RoBERTa, TF-IDF logistic regression on the full corpus
- Name-swap and source-label tests: tone flips in only 4–6% of items; attribution flips as it should
- 320-item human workbook and guide ready; two-annotator coding pending (the main validation gap)
> Dictionary baselines agree with the LLM on economic tone in fewer than half of items: 'prices fall' is good news that VADER calls negative. A TF-IDF model trained on the LLM labels reaches 71% agreement, macro-F1 0.64.

## What coverage looked like, December 2024 to October 2026
- 6,100 LLM-labelled items. Headlines: 49% negative, 19% positive, only 11% alarmist; news tone **moved with the data** (worst at the 2025 tariff shock, the autumn-2025 shutdown and March 2026; best after good jobs reports)
- Bluesky: 85% negative, 39% alarmist, 38% about the author's own household — between −0.7 and −0.9 every month
- Rising-price salience 26% vs easing prices 7% (12:1 on Bluesky); price-**level** framing rose from a quarter of price stories in early 2026 to half by autumn
- Attribution is slanted by audience lean: left-rated outlets blame the administration in 41% of items, centre and right 4–8%
- Headline numbers are 79% accurate (87% at national outlets); errors cluster in GDP growth and on social media
![](figures/fig5_media_vs_gap.png)
> The slant shows up in who is blamed, not in the numbers.

## Does media tone explain the gap? Not in this window
- Correlation between LLM news tone and the gap over 23 months: **0.12, not significant**
- Alarmist wording is weakly negative (p 0.01) but does not survive the Holm correction; social tone barely varies
- The one strong correlation (full-corpus FinBERT tone, 0.59) comes from two series that both trend down over two years — a common trend, not evidence
- Out-of-sample tests (Diebold–Mariano, Clark–West) are built and wait for the 2017–2024 panel
- Preliminary verdict: coverage tone tracked the economy; the gap did not

## What does explain it: prices, partisanship, survey mode
- Price level 30% above January 2020; year-ahead inflation expectations 4.7%; real wage growth negative in 2026
- Gap by party: Republicans +23 → −36 → +3 across the three administrations; Democrats −15 → −3 → −49
- **Independents −37** in 2025–26: the gap is real, not just expressive responding
- Bottom income tercile −39 vs top −27
- Web-only survey mode since July 2024: −7 to −9 points on the index (Michigan −6.6; Cummings–Tedeschi −8.9), −14 to −19 on Current Conditions
![](figures/fig7_partisan.png)

## Causal design and what would contradict a media story
- Observational data cannot identify media effects: reverse causality and common shocks
- Proposed: randomized truthful-framing experiment (rate vs level vs balanced summary), n≈1,200, 80% power for a 5-point effect, party as moderator; IRB and consent required
- Transportability to the national index needs exposure estimates, representative weights and a stable per-exposure effect
- Evidence against media bias already in hand: tone tracks data; gap equal for independents and larger for low-income households; numbers accurate
- Evidence still outstanding: whether level and rate frames of the same facts move beliefs differently

## One practical implication for forecasting and risk
- Do not use the Michigan index as an economic signal through this cycle: the economic-only model is wrong by 30–40 points and media tone does not fix it
- Treat the index as a **price-level and partisan-composition gauge**: condition on the price level since 2020, the party of the president and the survey mode break before mapping it to spending or to an election-risk scenario
- For nowcasting consumption, prefer hard data and the Current Conditions component net of the −14 to −19 mode effect
- Monitor with the dashboard: prediction with intervals, gap, media tone/framing/salience/calibration, releases, source composition, model performance
- Prospective plan: re-run after the Oct 23 final, Oct 28 FOMC, Oct 29 GDP/PCE, Nov 3 election, Nov 6 jobs report
> Everything is reproducible from run_all.sh; prompts, model versions, seeds and provenance are in the package. A rigorous finding that media bias does not explain the gap is what the evidence currently supports.
