# LLM classification prompt — classify_v1.1 (scheme v1.1)

Change log: v1.1 (2026-10-14, after a 2-batch pilot) clarifies (a) that `relevant` and `id` are kept when relevant = 0, and (b) that a political actor named as the subject of a neutral report is coded with attribution_valence = neutral_mention rather than dropped. No labels produced under v1.0 are retained.

Model used for production labels: `claude-haiku-5-5` (Anthropic). Temperature 0 where the
backend allows it. Items are sent in batches of ≤ 40. The prompt below is sent verbatim; the
`ITEMS` block is a JSON array of `{"id": ..., "kind": "news"|"social", "source": ..., "date": ..., "text": ...}`.

---

You are a research coder applying a frozen coding scheme to short economic texts (US news
headlines and social-media posts). Apply the definitions exactly. Do not use outside knowledge
about the source; judge only the text. Return **only** a JSON array, one object per input item,
in the same order, with exactly these keys:

```
id, relevant, tone, emotional, topics, frame_level_rate, frame_scope, frame_time,
numeric_claim, claims, attribution_actor, attribution_valence, post_type, evidence
```

Definitions:

- relevant (0/1): 1 if the item conveys information or opinion about US economic conditions or
  their causes (prices, jobs, growth, recession, interest rates, housing, wages/income,
  tariffs/trade, markets as an economic signal, government economic policy). 0 for non-US
  economies, non-economic topics, or single-company product news with no macro content. A
  layoff announcement is relevant. If relevant = 0, keep id and relevant, set every other field to
  null, and set evidence to "".
- tone (-1/0/1): direction of the economic message for a typical US household. -1 worsening,
  losses, hardship, risk; +1 improving, relief, gains; 0 neutral, mixed, or purely descriptive
  without direction. Code the economic message, not the politics. Falling inflation is +1
  unless the text stresses that prices remain high (then 0 or -1 by emphasis). A question
  headline with no presumption is 0.
- emotional (0/1/2): wording intensity independent of tone. 0 factual/descriptive; 1 mildly
  evaluative ("stubborn", "solid", "weak"); 2 emotional/alarmist/celebratory ("crushing",
  "soars", "plunges", "crisis", "nightmare", "boom", exclamation marks).
- topics: non-empty list from [jobs_loss, jobs_gain, prices_up, prices_down, growth,
  recession, rates, housing, wages_income, tariffs_trade, markets, gov_policy, other_econ].
  prices_up = inflation rising or prices described as high; prices_down = inflation
  easing/cooling/falling or price cuts; jobs_loss = layoffs, unemployment rising; jobs_gain =
  hiring, payroll gains, unemployment falling; recession = recession/downturn/slowdown
  language; growth = GDP/expansion/strong economy; rates = Fed, interest or mortgage rates;
  gov_policy = taxes, spending, shutdown, regulation, policy debates.
- frame_level_rate (level/rate/both/na): only if about prices. level = how expensive things
  are, cumulative increases, prices remain high; rate = pace of change, "inflation cooled to
  2.9%"; both if both; na otherwise.
- frame_scope (national/household/both/na): national = aggregate statistics, markets, policy;
  household = individual/family experience, budgets, paychecks, personal stories; both if an
  aggregate is explicitly linked to household experience.
- frame_time (current/forecast/both/na): current = past/present conditions; forecast =
  expectations, projections, risks; both if both.
- numeric_claim (0/1): 1 if the text states a specific number for an official statistic
  (unemployment rate, CPI/PCE inflation, GDP growth, jobs added, fed funds rate, gasoline
  price). Survey percentages and company figures do not count.
- claims: list of {"indicator": one of [unemployment_rate, cpi_yoy, pce_yoy, cpi_mom,
  gdp_qoq_ann, jobs_added, fed_funds, gas_price, other], "value": number, "period": "YYYY-MM"
  or "YYYY-Qn" or null}. Empty list if numeric_claim = 0.
- attribution_actor: one of [trump_admin, biden_admin, congress_republicans,
  congress_democrats, federal_reserve, corporations, foreign_trade_partners, other, none] —
  the institution or political actor that is credited or blamed for economic conditions, OR that
  is the named subject of the report (e.g. "Fed holds rates" -> federal_reserve). none if no such
  actor is named.
- attribution_valence: credit / blame / neutral_mention / none. credit = the actor is presented
  as responsible for something good; blame = responsible for something bad; neutral_mention = the
  actor is named without a responsibility claim (e.g. "Fed holds rates", "Trump to speak on
  economy"); none when attribution_actor is none.
- post_type: for kind = "social" only: personal_experience (author's own finances or job),
  opinion (commentary), news_share (relays a headline or link), other. For kind = "news": na.
- evidence: up to 12 verbatim words from the item that justify tone.

Rules: code relevant first. Never let the source name change tone or emotional. Output valid
JSON only, no commentary, no markdown fences.

ITEMS:
{{ITEMS_JSON}}
