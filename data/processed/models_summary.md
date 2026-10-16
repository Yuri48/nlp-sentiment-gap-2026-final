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
