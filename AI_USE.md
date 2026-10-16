Use of AI tools

I used Claude (Anthropic) as a coding and writing assistant for about 20% of this project. I designed the study, wrote most of the code, ran and debugged the pipeline, and wrote the report and slides mostly myself in terms of actual content.

Claude helped in a few specific places:

checking my reading of the project brief and the course spreadsheet against the analysis plan I had drafted;
writing first versions of some supporting code in src/, mainly the report and slide builders and parts of the dashboard, which I then edited and tested;
tracking down a handful of data-source errors (GDELT, Bluesky, FRED/ALFRED, the Michigan archive) and finding background on the 2026 economic events and the Michigan survey methodology, which I checked against the original sources;
tightening the wording of the README and parts of the report after I had written them.

The data collectors, macro panel, economic baseline model, corpus cleaning, classifier baselines, media indices and models are my own code. I wrote the coding scheme and the human-labeling guide. I am responsible for the content and conclusions.

Pre-trained NLP models used as baselines (not generative). FinBERT (ProsusAI/finbert), Twitter-RoBERTa (cardiffnlp/twitter-roberta-base-sentiment-latest), the VADER lexicon and GDELT’s dictionary tone.
