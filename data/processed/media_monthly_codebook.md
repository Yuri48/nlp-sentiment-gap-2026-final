# media_monthly.csv codebook

| column | definition |
|---|---|
| `llm_news_tone` | Mean LLM tone (-1..+1) of relevant news headlines in the labelled sample |
| `llm_news_neg_share` | Share of relevant headlines with tone = -1 (LLM) |
| `llm_news_emotional2_share` | Share with emotional/alarmist wording (emotional = 2) |
| `llm_news_topic_*` | Share of relevant headlines mentioning each topic (selection / salience) |
| `llm_news_frame_level_share` | Among price headlines: share framed as price LEVEL (level or both) |
| `llm_news_frame_household_share` | Share framed around household experience (household or both) |
| `llm_news_frame_forecast_share` | Share framed as forecast/expectations (forecast or both) |
| `llm_news_blame_<actor>` | Share of relevant headlines blaming the actor (political attribution) |
| `llm_<source_type>_tone / llm_<lean>_tone` | LLM tone by source type and by audience-lean stratum |
| `llm_social_tone` | Mean LLM tone of relevant Bluesky posts (sample); _engagement_weighted weights by likes+reposts+replies+quotes+1 |
| `llm_social_personal_share` | Share of relevant posts that describe the author's own finances (household experience) |
| `news_n_kw` | Number of unique US headlines with an economic keyword in the title (content SUPPLY, from the GKG slice sample) |
| `news_gdelt_tone` | Mean GDELT V2Tone of those articles (dictionary tone of full text, full corpus) |
| `news_kwshare_<topic>` | Keyword-based salience: share of economic headlines mentioning the topic (full corpus) |
| `news_finbert_tone / news_vader_tone / news_twroberta_tone / news_tfidf_lr_tone` | Mean 3-class tone from each baseline classifier over the full keyword corpus |
| `social_n_posts` | Unique Bluesky posts collected per month (supply, capped at 100 per query-week) |
| `news_claims_accurate_share` | Factual calibration: share of verifiable numeric claims in headlines matching the official value available at publication (tolerances in build_media_indices.py) |
| `mich_news_unfavorable` | Michigan survey: % of respondents who recall hearing UNFAVORABLE business news (the only exposure/recall measure available) |
