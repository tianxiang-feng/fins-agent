# AGENTS.md

This file records my working instructions for AI assistance in FINS5545 Project B.

The AI assistant should help with:
- understanding the Project B brief and starter code;
- planning the Part B workflow;
- writing and debugging Python code for portfolio construction, backtesting, sentiment analysis, and Streamlit app outputs;
- checking for look-ahead bias, calendar alignment issues, and incorrect annualisation;
- improving code clarity and reproducibility;
- helping organise prompt logs and AI-use notes.

The AI assistant should not:
- invent results;
- commit raw data files;
- expose secrets or API keys;
- recompute heavy backtests or VADER sentiment inside the deployed Streamlit app;
- ignore look-ahead bias;
- use future returns or future sentiment when forming portfolio weights;
- replace my own economic interpretation.

Project rules:
- Work only inside `z5642794_projectB`.
- Generate app-readable outputs under `results/data/`.
- Generate report tables under `results/tables/`.
- Generate figures under `results/figures/`.
- Required output filenames are:
  - `results/data/fund_returns.csv`
  - `results/data/fund_weights.csv`
  - `results/data/sector_sentiment_index.csv`
  - `results/tables/performance_metrics.csv`
- The Streamlit app must load precomputed results from `results/` and should not recompute backtests or run NLTK/VADER at startup.
- All code suggestions must be checked by running the relevant script locally.
- Any AI-generated code or text must be reviewed, tested, and revised before submission.
