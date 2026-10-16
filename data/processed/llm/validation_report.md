# LLM label validation

* Items in manifest: 6270
* Labelled and valid: 6091
* Invalid records: 179
* Batches without output: [] (0)

## Distribution
| kind   |   count |   share_relevant |
|:-------|--------:|-----------------:|
| news   |    4026 |         0.710879 |
| social |    2065 |         0.72155  |

| kind   |   -1.0 |   0.0 |   1.0 |
|:-------|-------:|------:|------:|
| news   |  0.488 | 0.323 | 0.189 |
| social |  0.848 | 0.114 | 0.038 |

| kind   |   0.0 |   1.0 |   2.0 |
|:-------|------:|------:|------:|
| news   | 0.571 | 0.315 | 0.114 |
| social | 0.154 | 0.452 | 0.394 |

## Problems (first 100)
* batch 14: n20260914143000_854 — missing id
* batch 91: n20260421143000_18 — frame_level_rate=None
* batch 91: n20260708203000_1221 — frame_level_rate=None
* batch 91: s3mq67pvwq4k2v — frame_level_rate=None
* batch 91: n20260515143000_1397 — frame_level_rate=None
* batch 91: n20251029143000_1713 — frame_level_rate=None
* batch 91: n20260306203000_1183 — frame_level_rate=None
* batch 91: n20251012143000_149 — frame_level_rate=None
* batch 91: n20260116203000_251 — frame_level_rate=None
* batch 91: n20251117143000_251 — frame_level_rate=None
* batch 91: n20260427203000_638 — frame_level_rate=None
* batch 91: n20260904203000_346 — frame_level_rate=None
* batch 91: s3mv46232fm22r — frame_level_rate=None
* batch 91: n20260723203000_560 — frame_level_rate=None
* batch 91: n20260623203000_898 — frame_level_rate=None
* batch 91: s3mmunbqvodc2g — frame_level_rate=None
* batch 91: n20260220203000_1245 — frame_level_rate=None
* batch 91: n20260903203000_181 — frame_level_rate=None
* batch 92: s3mxciavz7es2l — frame_level_rate=None
* batch 92: n20261010143000_79 — frame_level_rate=None
* batch 92: n20260825203000_1170 — frame_level_rate=None
* batch 92: n20260816143000_240 — frame_level_rate=None
* batch 92: s3mxumrwzp5s2f — frame_level_rate=None
* batch 92: n20260904143000_1029 — frame_level_rate=None
* batch 92: n20260207203000_571 — frame_level_rate=None
* batch 92: s3mrbj4tv2nc2h — frame_level_rate=None
* batch 92: n20251211143000_316 — frame_level_rate=None
* batch 92: n20251202143000_1403 — frame_level_rate=None
* batch 92: s3mmuowzrod22k — frame_level_rate=None
* batch 92: n20260505143000_722 — frame_level_rate=None
* batch 92: n20260217143000_1097 — frame_level_rate=None
* batch 92: n20260109143000_195 — frame_level_rate=None
* batch 93: s3mtziixuwos27 — frame_level_rate=None
* batch 93: n20260119143000_406 — frame_level_rate=None
* batch 93: n20260221143000_644 — frame_level_rate=None
* batch 93: n20251107143000_1425 — frame_level_rate=None
* batch 93: n20260724203000_679 — frame_level_rate=None
* batch 93: n20260801203000_432 — frame_level_rate=None
* batch 93: n20260201203000_670 — frame_level_rate=None
* batch 93: n20260522143000_899 — frame_level_rate=None
* batch 93: n20260928143000_953 — frame_level_rate=None
* batch 93: n20260423143000_512 — frame_level_rate=None
* batch 93: s3mgsvigqhuc2n — frame_level_rate=None
* batch 93: n20251007143000_570 — frame_level_rate=None
* batch 93: n20260902203000_1270 — frame_level_rate=None
* batch 94: s3me2yxzdaj22d — frame_level_rate=None
* batch 94: n20260916203000_1022 — frame_level_rate=None
* batch 94: n20260917203000_162 — frame_level_rate=None
* batch 94: n20260127203000_214 — frame_level_rate=None
* batch 94: s3mqonothhyk2d — frame_level_rate=None
* batch 94: n20260822143000_486 — frame_level_rate=None
* batch 94: n20260129203000_1577 — frame_level_rate=None
* batch 94: n20260611143000_1016 — frame_level_rate=None
* batch 94: n20251017143000_524 — frame_level_rate=None
* batch 94: n20261007143000_212 — frame_level_rate=None
* batch 94: n20260318203000_1619 — frame_level_rate=None
* batch 94: n20260211143000_107 — frame_level_rate=None
* batch 94: n20251124143000_1069 — frame_level_rate=None
* batch 95: n20251210143000_1461 — frame_level_rate=None
* batch 95: s3mth3w46xfs2g — frame_level_rate=None
* batch 95: s3mthjkhlj3c22 — frame_level_rate=None
* batch 95: n20260917143000_452 — frame_level_rate=None
* batch 95: n20260204203000_1464 — frame_level_rate=None
* batch 95: n20260519203000_14 — frame_level_rate=None
* batch 95: s3mxd2eqr5us2k — frame_level_rate=None
* batch 95: n20260129203000_421 — frame_level_rate=None
* batch 95: n20260929203000_568 — frame_level_rate=None
* batch 95: n20260403143000_1154 — frame_level_rate=None
* batch 95: n20260220203000_233 — frame_level_rate=None
* batch 95: n20260625143000_773 — frame_level_rate=None
* batch 95: n20260707203000_396 — frame_level_rate=None
* batch 128: n20260908203000_1205 — missing id
* batch 128: n20260825203000_856 — missing id
* batch 136: n20250122143000_1077 — frame_level_rate=None
* batch 136: n20250803143000_751 — frame_level_rate=None
* batch 136: n20250706143000_827 — frame_level_rate=None
* batch 136: n20250708143000_1201 — frame_level_rate=None
* batch 136: n20250409143000_1046 — frame_level_rate=None
* batch 136: s3m2ptslw5ek2j — frame_level_rate=None
* batch 136: s3lzltph4c322q — frame_level_rate=None
* batch 136: n20250521143000_998 — frame_level_rate=None
* batch 136: s3lyijb7rnh22p — frame_level_rate=None
* batch 136: n20250613143000_1279 — frame_level_rate=None
* batch 136: s3mbufcsqgvc2q — frame_level_rate=None
* batch 136: s3mcxffldctc2f — frame_level_rate=None
* batch 136: n20250403143000_761 — frame_level_rate=None
* batch 136: n20250404143000_1009 — frame_level_rate=None
* batch 136: s3mdjgaqhs7s2e — frame_level_rate=None
* batch 136: n20250605143000_1844 — frame_level_rate=None
* batch 136: s3m5zgdaqrys24 — frame_level_rate=None
* batch 136: s3m3t256gwxc2l — frame_level_rate=None
* batch 136: n20250213143000_1140 — frame_level_rate=None
* batch 136: n20250122143000_2024 — frame_level_rate=None
* batch 136: s3mbcdtisg2s2q — frame_level_rate=None
* batch 136: n20250218143000_1393 — frame_level_rate=None
* batch 137: n20250908143000_1401 — frame_level_rate=None
* batch 137: n20250723143000_1594 — frame_level_rate=None
* batch 137: n20250303143000_746 — frame_level_rate=None
* batch 137: n20250808143000_1200 — frame_level_rate=None
* batch 137: n20250910143000_1210 — frame_level_rate=None
