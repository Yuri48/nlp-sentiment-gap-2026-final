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
