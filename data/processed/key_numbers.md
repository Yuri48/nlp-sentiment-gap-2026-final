# Key numbers (2026-10-15 14:36)

## Economic baseline and gap
* gap 2010-2019: mean -3.5, RMSE 6.6, min -20.5 (2011-08)
* gap 2022-2024: mean -23.1, RMSE 23.6, min -34.8 (2022-06)
* gap 2025: mean -31.4, RMSE 31.9, min -37.8 (2025-11)
* gap 2026 (Jan-Oct): mean -34.2, RMSE 34.3, min -40.1 (2026-05)
* latest month 2026-10: ICS 46.3, prediction 84.7, empirical 80% PI [55.0, 87.3], gap -38.4
* um_current gap 2026 mean -45.2
* um_expected gap 2026 mean -27.1
* macro Oct-2026 real-time: u=4.2 (ref 2026-09), pce=3.42 (ref 2026-08), gdp=2.2 (2026Q2)
* cum_price_since_2020 latest 29.8%; cum_price_3y 9.4%; real DPI pc yoy 1.1%; gas 4.34; mortgage 7.34; mich 1y exp 4.0
* ICS by party latest (2026-08): Dem 40.2, Ind 48.0, Rep 82.0; income bottom/top 42.2/63.6
* Michigan news heard, latest (2026-08): unfavorable 104%, favorable 14%; high-price item 23%, unemployment item 25%; govt policy poor 74%
## Corpus
* Raw records kept at collection: 117,416
* After title cleaning / length filter: 115,721
* After URL de-duplication: 115,669
* After same-day wire-reprint and same-week republish removal: 90,260 unique headlines
* Months covered: 2020-12 .. 2026-10; headlines with economic keyword in title: 17,528
* Title source: {'page_title': 90096, 'url_slug': 164}
* Raw posts collected: 43,733; unique after de-duplication: 37,698
* Months: 2025-08 .. 2026-10
* Share replies: 0.45; share with link: 0.16; posts with >=1 copy (suspected copy-pasta/bots): 0.012
## LLM labels
* labelled items 6091 (news 4026, social 2065); months 2024-12..2026-10
* news: relevant share 0.71; tone mean -0.30; neg 0.49 / neu 0.32 / pos 0.19; alarmist (emotional=2) 0.11; household frame 0.13; forecast frame 0.26; numeric claims 0.06; blame 0.14
  - price items: 930; level framing 0.40; rate framing 0.65; prices_up share of all 0.27 vs prices_down 0.07; jobs_loss 0.08 vs jobs_gain 0.06; recession 0.02; tariffs 0.18
  - blame by actor {'trump_admin': 0.49, 'other': 0.22, 'corporations': 0.21, 'foreign_trade_partners': 0.04, 'federal_reserve': 0.02, 'congress_republicans': 0.01, 'biden_admin': 0.01, 'congress_democrats': 0.0}; credit by actor {'trump_admin': 0.56, 'other': 0.23, 'corporations': 0.19, 'congress_republicans': 0.02}
* social: relevant share 0.72; tone mean -0.81; neg 0.85 / neu 0.11 / pos 0.04; alarmist (emotional=2) 0.39; household frame 0.38; forecast frame 0.20; numeric claims 0.04; blame 0.38
  - price items: 779; level framing 0.65; rate framing 0.38; prices_up share of all 0.49 vs prices_down 0.04; jobs_loss 0.13 vs jobs_gain 0.01; recession 0.12; tariffs 0.17
  - blame by actor {'trump_admin': 0.55, 'corporations': 0.2, 'other': 0.15, 'congress_republicans': 0.06, 'biden_admin': 0.02, 'congress_democrats': 0.01, 'foreign_trade_partners': 0.01, 'federal_reserve': 0.0}; credit by actor {'trump_admin': 0.31, 'other': 0.29, 'biden_admin': 0.2, 'corporations': 0.09, 'federal_reserve': 0.09, 'congress_democrats': 0.03}
* news tone by source type: {'local': {'mean': -0.35, 'count': 164}, 'local_other': {'mean': -0.33, 'count': 814}, 'national': {'mean': -0.28, 'count': 552}, 'national_other': {'mean': -0.27, 'count': 354}, 'other': {'mean': -0.27, 'count': 888}}
* news tone by lean: {'center': {'mean': -0.26, 'count': 359}, 'lean_left': {'mean': -0.34, 'count': 192}, 'lean_right': {'mean': -0.25, 'count': 126}, 'left': {'mean': -0.64, 'count': 67}, 'local': {'mean': -0.33, 'count': 978}, 'right': {'mean': -0.12, 'count': 162}, 'unknown': {'mean': -0.27, 'count': 888}}
* blame Trump admin by lean: {'center': 0.061, 'lean_left': 0.068, 'lean_right': 0.071, 'left': 0.418, 'local': 0.06, 'right': 0.037, 'unknown': 0.064}
* credit Trump admin by lean: {'center': 0.017, 'lean_left': 0.021, 'lean_right': 0.048, 'left': 0.015, 'local': 0.018, 'right': 0.093, 'unknown': 0.024}
## Media monthly (last 12 months)
| month   |   llm_news_tone |   llm_news_neg_share |   llm_social_tone |   news_finbert_tone |   news_gdelt_tone |   news_n_kw |   news_claims_accurate_share |   news_claims_n |   llm_news_frame_level_share |   llm_news_topic_prices_up |   llm_news_emotional2_share |   mich_news_unfavorable |
|:--------|----------------:|---------------------:|------------------:|--------------------:|------------------:|------------:|-----------------------------:|----------------:|-----------------------------:|---------------------------:|----------------------------:|------------------------:|
| 2025-11 |          -0.049 |                0.366 |            -0.846 |              -0.197 |            -0.669 |         330 |                        1     |               1 |                        0.333 |                      0.122 |                       0.22  |                     nan |
| 2025-12 |          -0.158 |                0.421 |            -0.739 |              -0.202 |            -0.942 |         381 |                        1     |               2 |                        0.722 |                      0.368 |                       0.053 |                     nan |
| 2026-01 |          -0.173 |                0.365 |            -0.692 |              -0.16  |            -0.818 |         829 |                        1     |               3 |                        0.267 |                      0.115 |                       0.077 |                     nan |
| 2026-02 |          -0.059 |                0.3   |            -0.786 |              -0.216 |            -0.831 |         847 |                        0.75  |               4 |                        0.25  |                      0.079 |                       0.039 |                     nan |
| 2026-03 |          -0.479 |                0.637 |            -0.87  |              -0.199 |            -1.831 |        1088 |                        0.818 |              11 |                        0.354 |                      0.474 |                       0.209 |                     nan |
| 2026-04 |          -0.356 |                0.519 |            -0.74  |              -0.161 |            -1.377 |         962 |                        0.556 |               9 |                        0.33  |                      0.356 |                       0.176 |                     nan |
| 2026-05 |          -0.394 |                0.564 |            -0.85  |              -0.149 |            -1.128 |         922 |                        0.714 |               7 |                        0.344 |                      0.376 |                       0.161 |                     nan |
| 2026-06 |          -0.082 |                0.394 |            -0.844 |              -0.205 |            -0.922 |         770 |                        0.625 |               8 |                        0.299 |                      0.24  |                       0.13  |                     nan |
| 2026-07 |          -0.325 |                0.526 |            -0.797 |              -0.17  |            -1.036 |         719 |                        0.667 |               9 |                        0.325 |                      0.305 |                       0.104 |                     nan |
| 2026-08 |          -0.226 |                0.437 |            -0.797 |              -0.19  |            -1.146 |         742 |                        0.333 |               3 |                        0.507 |                      0.16  |                       0.085 |                     nan |
| 2026-09 |          -0.429 |                0.549 |            -0.824 |              -0.21  |            -0.851 |         801 |                        0.833 |               6 |                        0.475 |                      0.325 |                       0.107 |                     nan |
| 2026-10 |          -0.294 |                0.492 |            -0.809 |              -0.249 |            -0.689 |         361 |                        0.889 |               9 |                        0.543 |                      0.302 |                       0.071 |                     nan |
* claims status: {'accurate': 86, 'unverifiable': 84, 'unverifiable_local': 34, 'wrong': 26, 'stale': 20}; by indicator: {'cpi_mom': 1.0, 'cpi_yoy': 0.55, 'fed_funds': 0.0, 'gas_price': 0.27, 'gdp_qoq_ann': 0.33, 'jobs_added': 0.66, 'other': 0.0, 'pce_yoy': 0.0, 'unemployment_rate': 0.61}
* claims accuracy by source type: {'local': 1.0, 'local_other': 0.33, 'national': 0.88, 'national_other': 0.71, 'other': 0.66, 'social': 0.29}
## baseline_report.md
# Baseline classifiers (2026-10-15)

Items scored: 53,059

## TF-IDF + logistic regression (5-fold CV on 4,262 LLM-labelled relevant items)
accuracy = 0.719, macro-F1 = 0.639

```
              precision    recall  f1-score   support

          -1      0.812     0.831     0.821      2612
           0      0.567     0.551     0.559      1066
           1      0.552     0.524     0.538       584

    accuracy                          0.719      4262
   macro avg      0.644     0.635     0.639      4262
weighted avg      0.715     0.719     0.717      4262
```

## Agreement with LLM tone (LLM is the reference here; human gold labels pending)
| baseline        | kind   |    n |   agreement_with_LLM |   macroF1_vs_LLM |
|:----------------|:-------|-----:|---------------------:|-----------------:|
| gdelt_class     | all    | 2772 |                0.48  |            0.409 |
| gdelt_class     | news   | 2772 |                0.48  |            0.409 |
| vader_class     | all    | 4262 |                0.461 |            0.407 |
| vader_class     | news   | 2772 |                0.453 |            0.432 |
| vader_class     | social | 1490 |                0.475 |            0.306 |
| finbert_class   | all    | 4262 |                0.507 |            0.458 |
| finbert_class   | news   | 2772 |                0.534 |            0.502 |
| finbert_class   | social | 1490 |                0.457 |            0.332 |
| twroberta_class | all    | 4262 |                0.604 |            0.538 |
| twroberta_class | news   | 2772 |                0.56  |            0.528 |
| twroberta_class | social | 1490 |                0.687 |            0.445 |
| tfidf_lr_class  | all    | 4262 |                0.719 |            0.639 |
| tfidf_lr_class  | news   | 2772 |                0.653 |            0.63  |
| tfidf_lr_class  | social | 1490 |                0.841 |            0.45  |

## Class shares by baseline
|    |   gdelt_class |   vader_class |   finbert_class |   twroberta_class |   tfidf_lr_class |
|---:|--------------:|--------------:|----------------:|------------------:|-----------------:|
| -1 |         0.518 |         0.429 |           0.361 |             0.505 |            0.771 |
|  0 |         0.29  |         0.221 |           0.545 |             0.409 |            0.159 |
|  1 |         0.192 |         0.351 |           0.094 |             0.087 |            0.07  |

## perturbation_report.md
# Perturbation tests (classifier robustness)

Labelled variants: 480 of 480

## name_swap
|                               |      0 |
|:------------------------------|-------:|
| n_pairs                       | 80     |
| flip_rate_relevant            |  0     |
| flip_rate_tone                |  0.062 |
| flip_rate_emotional           |  0.038 |
| flip_rate_frame_scope         |  0.2   |
| flip_rate_attribution_actor   |  0.925 |
| flip_rate_attribution_valence |  0.15  |
| mean_tone_change              |  0.012 |

Attribution actor, original (rows) vs swapped (columns) — a clean swap moves trump_admin <-> biden_admin:
| attribution_actor      |   biden_admin |   congress_democrats |   congress_republicans |   corporations |   federal_reserve |   none |   other |   trump_admin |
|:-----------------------|--------------:|---------------------:|-----------------------:|---------------:|------------------:|-------:|--------:|--------------:|
| biden_admin            |             1 |                    0 |                      0 |              0 |                 0 |      0 |       0 |             2 |
| congress_democrats     |             0 |                    0 |                      1 |              0 |                 0 |      0 |       0 |             0 |
| congress_republicans   |             1 |                    1 |                      0 |              0 |                 0 |      1 |       2 |             0 |
| corporations           |             0 |                    0 |                      0 |              1 |                 0 |      0 |       0 |             0 |
| federal_reserve        |             0 |                    0 |                      0 |              0 |                 1 |      0 |       0 |             0 |
| foreign_trade_partners |             1 |                    0 |                      0 |              0 |                 0 |      0 |       0 |             0 |
| other                  |             0 |                    0 |                      0 |              0 |                 0 |      0 |       2 |             1 |
| trump_admin            |            63 |                    0 |                      0 |              0 |                 0 |      1 |       0 |             1 |

## src_left
|                               |      0 |
|:------------------------------|-------:|
| n_pairs                       | 80     |
| flip_rate_relevant            |  0     |
| flip_rate_tone                |  0.05  |
| flip_rate_emotional           |  0.15  |
| flip_rate_frame_scope         |  0.15  |
| flip_rate_attribution_actor   |  0.138 |
| flip_rate_attribution_valence |  0.125 |
| mean_tone_change              | -0.025 |

## src_right
|                               |      0 |
|:------------------------------|-------:|
| n_pairs                       | 80     |
| flip_rate_relevant            |  0.012 |
| flip_rate_tone                |  0.062 |
| flip_rate_emotional           |  0.15  |
| flip_rate_frame_scope         |  0.138 |
| flip_rate_attribution_actor   |  0.088 |
| flip_rate_attribution_valence |  0.075 |
| mean_tone_change              | -0.025 |

## src_wire
|                               |      0 |
|:------------------------------|-------:|
| n_pairs                       | 80     |
| flip_rate_relevant            |  0.012 |
| flip_rate_tone                |  0.038 |
| flip_rate_emotional           |  0.138 |
| flip_rate_frame_scope         |  0.162 |
| flip_rate_attribution_actor   |  0.125 |
| flip_rate_attribution_valence |  0.125 |
| mean_tone_change              | -0.025 |

## models_summary.md
# Models: association and predictive content (2026-10-15; OOS from 2026-01)

Media variables available (>= 24 months): llm_news_tone, llm_news_neg_share, llm_news_emotional2_share, llm_news_topic_prices_up, llm_news_topic_jobs_loss, llm_news_topic_recession, llm_news_frame_level_share, llm_news_frame_household_share, llm_news_blame_share, news_finbert_tone, news_gdelt_tone, news_vader_tone, news_kwshare_prices, llm_social_tone, social_twroberta_tone. Primary pre-specified media variable: **llm_news_tone**.

Media months available: 25. **Short-sample regime** (< 36 months): contemporaneous media (lag 0), reduced control set, HAC(2); out-of-sample comparisons are skipped and all association estimates are preliminary.

## Lag selection (primary media variable, static model)
|   lag |   n |    BIC |    AIC |   coef_media |
|------:|----:|-------:|-------:|-------------:|
|     0 |  23 | 152.28 | 146.6  |         9.7  |
|     1 |  22 | 125.72 | 120.26 |        19.31 |
|     2 |  21 | 124.54 | 119.32 |         7.72 |

Lag used: 0 (fixed at 0 in the short-sample regime; BIC on so few months is not informative).

## In-sample estimates, static levels, 2024-12..2026-09 — coefficient (HAC t-stat)
|                 | M1 econ        | M2 +media      | M3 +controls   |
|:----------------|:---------------|:---------------|:---------------|
| R2              | 0.541          | 0.620          | 0.871          |
| adjR2           | 0.460          | 0.525          | 0.786          |
| const           | 194.586 (5.6)  | 216.011 (4.7)  | 180.308 (4.0)  |
| cum_price_3y    | nan            | nan            | 1.657 (2.8)    |
| g               | 1.499 (2.5)    | 1.383 (2.1)    | -0.790 (-1.3)  |
| gas_price       | nan            | nan            | -8.876 (-3.2)  |
| log_epu         | nan            | nan            | -14.016 (-4.4) |
| media_primary   | nan            | 14.480 (1.8)   | 1.609 (0.4)    |
| n               | 21             | 21             | 21             |
| pi              | -7.189 (-3.2)  | -7.388 (-3.9)  | -1.144 (-0.4)  |
| real_dpi_pc_yoy | nan            | nan            | 0.751 (0.4)    |
| resid_SD        | 5.32           | 4.99           | 3.35           |
| u               | -28.681 (-3.8) | -32.474 (-3.2) | -7.039 (-0.8)  |

## In-sample estimates, dynamic (with y_t-1), 2024-12..2026-09 — coefficient (HAC t-stat)
|                 | M1 econ       | M2 +media     | M3 +controls   |
|:----------------|:--------------|:--------------|:---------------|
| R2              | 0.726         | 0.837         | 0.929          |
| adjR2           | 0.658         | 0.782         | 0.871          |
| const           | 1.960 (0.0)   | 10.308 (0.3)  | 62.546 (1.6)   |
| cum_price_3y    | nan           | nan           | 0.710 (1.5)    |
| g               | -0.097 (-0.1) | -0.378 (-1.0) | -1.667 (-3.9)  |
| gas_price       | nan           | nan           | -8.883 (-4.2)  |
| log_epu         | nan           | nan           | -8.649 (-3.8)  |
| media_primary   | nan           | 17.252 (5.2)  | 7.112 (2.1)    |
| n               | 21            | 21            | 21             |
| pi              | -1.506 (-0.6) | -1.236 (-0.7) | 3.188 (1.3)    |
| real_dpi_pc_yoy | nan           | nan           | 0.477 (0.6)    |
| resid_SD        | 4.23          | 3.37          | 2.60           |
| u               | 3.717 (0.3)   | 2.088 (0.3)   | 6.259 (1.0)    |
| ylag            | 0.752 (2.9)   | 0.819 (6.8)   | 0.587 (4.9)    |

## Out-of-sample accuracy (static): fewer than 12 common OOS months available (0); skipped.

## Out-of-sample accuracy (dynamic): fewer than 12 common OOS months available (0); skipped.

## Two-step association: sentiment gap on each media measure (HAC; coefficient per one s.d. of the media measure; Holm-adjusted p across measures)
| media variable                 |   n |   corr |   coef (pts per 1 s.d.) |   t_HAC |     p |    R2 |   p_holm |
|:-------------------------------|----:|-------:|------------------------:|--------:|------:|------:|---------:|
| news_finbert_tone              |  25 |  0.588 |                   3.517 |   4.037 | 0     | 0.346 |    0.001 |
| llm_news_emotional2_share      |  23 | -0.409 |                  -2.421 |  -2.647 | 0.008 | 0.167 |    0.114 |
| llm_news_topic_recession       |  23 | -0.302 |                  -1.788 |  -1.685 | 0.092 | 0.091 |    1     |
| news_vader_tone                |  25 |  0.326 |                   1.951 |   1.475 | 0.14  | 0.106 |    1     |
| llm_news_neg_share             |  23 | -0.241 |                  -1.425 |  -1.228 | 0.22  | 0.058 |    1     |
| llm_news_frame_household_share |  23 | -0.265 |                  -1.57  |  -1.173 | 0.241 | 0.07  |    1     |
| llm_news_topic_jobs_loss       |  23 | -0.201 |                  -1.191 |  -1.125 | 0.261 | 0.04  |    1     |
| llm_news_frame_level_share     |  23 |  0.228 |                   1.351 |   1.076 | 0.282 | 0.052 |    1     |
| news_kwshare_prices            |  25 | -0.167 |                  -0.996 |  -1.031 | 0.303 | 0.028 |    1     |
| news_gdelt_tone                |  25 |  0.198 |                   1.187 |   0.895 | 0.371 | 0.039 |    1     |
| llm_news_tone                  |  23 |  0.112 |                   0.663 |   0.6   | 0.549 | 0.013 |    1     |
| llm_news_blame_share           |  23 | -0.113 |                  -0.668 |  -0.566 | 0.571 | 0.013 |    1     |
| llm_news_topic_prices_up       |  23 | -0.031 |                  -0.185 |  -0.176 | 0.861 | 0.001 |    1     |
| llm_social_tone                |  15 | -0.023 |                  -0.072 |  -0.131 | 0.896 | 0.001 |    1     |
| social_twroberta_tone          |  15 | -0.011 |                  -0.034 |  -0.038 | 0.969 | 0     |    1     |

## Average sentiment gap (actual minus economic-only prediction) by group and presidential period
|                    |   2017-01..2021-01 (Trump I) |   2021-02..2025-01 (Biden) |   2025-02.. (Trump II) |
|:-------------------|-----------------------------:|---------------------------:|-----------------------:|
| yhat               |                         91.2 |                       88.9 |                   87.2 |
| gap_ics_dem        |                        -14.9 |                       -2.7 |                  -48.7 |
| gap_ics_ind        |                          0.9 |                      -23.4 |                  -36.9 |
| gap_ics_rep        |                         23   |                      -36.3 |                    3.1 |
| gap_ics_inc_bottom |                         -5.9 |                      -24.4 |                  -39   |
| gap_ics_inc_middle |                          3.9 |                      -21.5 |                  -33.1 |
| gap_ics_inc_top    |                          7.2 |                      -14.8 |                  -27.4 |
| gap_ics_age_18_34  |                          4.8 |                      -13.5 |                  -34.7 |
| gap_ics_age_35_54  |                          2.9 |                      -20.6 |                  -35.6 |
| gap_ics_age_55p    |                         -0.7 |                      -23.2 |                  -32.1 |
| gap_all            |                          1.7 |                      -20.4 |                  -33.3 |

## Survey-mode check
Regressing the gap on a web-mode dummy (2024-07 onward), 2017+: coefficient -21.7 pts (HAC t = -6.5). This conflates the mode change with everything else that changed after mid-2024, so it is an upper bound on the mode effect; the Briefing Book estimate is about -9 points.
