# Economic-only baseline (econ_baseline.py, 2026-10-14)


## Index of Consumer Sentiment (ics)

### In-sample estimates (HAC, 12 lags)

|       |   coef_1978-2026 |    se |   coef_1978-2019 |   se_pre |
|:------|-----------------:|------:|-----------------:|---------:|
| const |           97.654 | 6.901 |          109.259 |    4.622 |
| u     |           -1.32  | 1.032 |           -3.554 |    0.726 |
| pi    |           -2.648 | 0.554 |           -1.786 |    0.409 |
| g     |            0.695 | 0.454 |            1.7   |    0.417 |

R² full sample = 0.259 (n=572); R² 1978-2019 = 0.586; residual SD = 12.41 / 8.21


### Out-of-sample accuracy (expanding window, real-time regressors)
|               |   RMSE |   MAE |   mean_gap |   n |
|:--------------|-------:|------:|-----------:|----:|
| 2010-2019     |   6.62 |  5.01 |      -3.55 | 120 |
| 2020-2021     |  22.91 | 18.68 |      -2.73 |  24 |
| 2022-2024     |  23.6  | 23.08 |     -23.08 |  36 |
| 2025-2026     |  33.05 | 32.68 |     -32.68 |  22 |
| all 2010-2026 |  17.51 | 12.87 |     -10.1  | 202 |


Coverage of parametric 95% / 80% prediction intervals 2010-2026: 0.70 / 0.57 (nominal 0.95 / 0.80); intervals are too narrow because errors are strongly autocorrelated (AR(1) of gap = 0.84); empirical intervals are also reported.

* 2022-2023: ICS -24.4 pts vs 1978-2019 mean; explained by unemployment +9.1, inflation -4.0, GDP -0.7 (pre-2020 coefficients); unexplained real-time gap (expanding model) -25.4 pts
* 2024: ICS -14.0 pts vs 1978-2019 mean; explained by unemployment +7.8, inflation +0.8, GDP +0.2 (pre-2020 coefficients); unexplained real-time gap (expanding model) -18.5 pts
* 2025: ICS -29.0 pts vs 1978-2019 mean; explained by unemployment +7.1, inflation +0.7, GDP -0.7 (pre-2020 coefficients); unexplained real-time gap (expanding model) -31.4 pts
* 2026 (Jan-Oct): ICS -35.4 pts vs 1978-2019 mean; explained by unemployment +6.9, inflation -0.8, GDP -1.0 (pre-2020 coefficients); unexplained real-time gap (expanding model) -34.2 pts
* Robustness — core PCE (spreadsheet series) instead of headline: OOS RMSE 2010-2026 = 17.28; mean gap 2025-2026 = -32.3
* Robustness — pseudo real-time regressors (final data, publication lags): OOS RMSE 2010-2026 = 17.28; mean gap 2025-2026 = -32.6

## Current Economic Conditions (um_current)

### In-sample estimates (HAC, 12 lags)

|       |   coef_1978-2026 |    se |   coef_1978-2019 |   se_pre |
|:------|-----------------:|------:|-----------------:|---------:|
| const |          110.236 | 8.336 |          128.614 |    3.827 |
| u     |           -1.588 | 1.258 |           -4.803 |    0.582 |
| pi    |           -2.709 | 0.67  |           -1.554 |    0.321 |
| g     |            0.688 | 0.448 |            1.556 |    0.435 |

R² full sample = 0.212 (n=572); R² 1978-2019 = 0.671; residual SD = 14.80 / 7.69


### Out-of-sample accuracy (expanding window, real-time regressors)
|               |   RMSE |   MAE |   mean_gap |   n |
|:--------------|-------:|------:|-----------:|----:|
| 2010-2019     |   5.14 |  4.15 |      -1.39 | 120 |
| 2020-2021     |  24.89 | 21.8  |      -6.25 |  24 |
| 2022-2024     |  34.65 | 34.22 |     -34.22 |  36 |
| 2025-2026     |  42.42 | 42.02 |     -42.02 |  22 |
| all 2010-2026 |  22.34 | 15.73 |     -12.25 | 202 |


Coverage of parametric 95% / 80% prediction intervals 2010-2026: 0.65 / 0.61 (nominal 0.95 / 0.80); intervals are too narrow because errors are strongly autocorrelated (AR(1) of gap = 0.90); empirical intervals are also reported.

* 2022-2023: ICS -31.9 pts vs 1978-2019 mean; explained by unemployment +12.2, inflation -3.5, GDP -0.6 (pre-2020 coefficients); unexplained real-time gap (expanding model) -34.9 pts
* 2024: ICS -27.7 pts vs 1978-2019 mean; explained by unemployment +10.6, inflation +0.7, GDP +0.2 (pre-2020 coefficients); unexplained real-time gap (expanding model) -32.8 pts
* 2025: ICS -36.9 pts vs 1978-2019 mean; explained by unemployment +9.6, inflation +0.6, GDP -0.6 (pre-2020 coefficients); unexplained real-time gap (expanding model) -39.4 pts
* 2026 (Jan-Oct): ICS -46.8 pts vs 1978-2019 mean; explained by unemployment +9.3, inflation -0.7, GDP -0.9 (pre-2020 coefficients); unexplained real-time gap (expanding model) -45.2 pts

## Consumer Expectations (um_expected)

### In-sample estimates (HAC, 12 lags)

|       |   coef_1978-2026 |    se |   coef_1978-2019 |   se_pre |
|:------|-----------------:|------:|-----------------:|---------:|
| const |           89.571 | 6.398 |           96.831 |    5.417 |
| u     |           -1.148 | 0.945 |           -2.753 |    0.859 |
| pi    |           -2.609 | 0.568 |           -1.935 |    0.541 |
| g     |            0.699 | 0.463 |            1.791 |    0.43  |

R² full sample = 0.265 (n=572); R² 1978-2019 = 0.483; residual SD = 11.89 / 9.47


### Out-of-sample accuracy (expanding window, real-time regressors)
|               |   RMSE |   MAE |   mean_gap |   n |
|:--------------|-------:|------:|-----------:|----:|
| 2010-2019     |   8.13 |  6.1  |      -4.93 | 120 |
| 2020-2021     |  22.41 | 16.9  |      -0.47 |  24 |
| 2022-2024     |  17    | 15.93 |     -15.93 |  36 |
| 2025-2026     |  27.17 | 26.69 |     -26.69 |  22 |
| all 2010-2026 |  15.19 | 11.38 |      -8.73 | 202 |


Coverage of parametric 95% / 80% prediction intervals 2010-2026: 0.82 / 0.63 (nominal 0.95 / 0.80); intervals are too narrow because errors are strongly autocorrelated (AR(1) of gap = 0.76); empirical intervals are also reported.

* 2022-2023: ICS -19.5 pts vs 1978-2019 mean; explained by unemployment +7.0, inflation -4.4, GDP -0.7 (pre-2020 coefficients); unexplained real-time gap (expanding model) -19.2 pts
* 2024: ICS -5.2 pts vs 1978-2019 mean; explained by unemployment +6.1, inflation +0.8, GDP +0.2 (pre-2020 coefficients); unexplained real-time gap (expanding model) -9.4 pts
* 2025: ICS -23.8 pts vs 1978-2019 mean; explained by unemployment +5.5, inflation +0.8, GDP -0.7 (pre-2020 coefficients); unexplained real-time gap (expanding model) -26.3 pts
* 2026 (Jan-Oct): ICS -28.0 pts vs 1978-2019 mean; explained by unemployment +5.3, inflation -0.8, GDP -1.0 (pre-2020 coefficients); unexplained real-time gap (expanding model) -27.1 pts