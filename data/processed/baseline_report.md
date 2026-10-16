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
