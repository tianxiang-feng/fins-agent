# Prompt Log for FINS5545 Project B

## Entry 1: Understanding Project B requirements

### What I wanted
I wanted Codex to read the Project B brief and summarise the required deliverables, output filenames, run order, app requirements, AI workflow requirements, and common risks.

### Prompt(s)
Read PROJECT_BRIEF.md, README.md, and SUBMISSION_CHECKLIST.md in this project folder. Do not edit any files yet.

Summarise:
1. the required Part B deliverables;
2. the required output filenames;
3. the expected run order;
4. the Streamlit app requirements;
5. the AI workflow requirements;
6. the biggest risks or common mistakes I should avoid.

Keep the answer practical and specific to this folder.

### What the assistant produced
Codex summarised that Project B requires a zipped project folder, a public GitHub repository link, and a live Streamlit app URL. It also listed the required outputs, including `results/data/fund_returns.csv`, `results/data/fund_weights.csv`, `results/data/sector_sentiment_index.csv`, and `results/tables/performance_metrics.csv`.

### What was wrong or risky
This was only a summary of the brief. It did not check whether the starter code worked or whether the required files could be generated correctly.

### What I changed and why
I used the summary as a planning checklist. I still need to inspect the starter code, run the project scripts, and verify each output locally before relying on it.


## Entry 2: Implementing the baseline combined fund backtest

### What I wanted
I wanted to implement the first baseline version of the Project B fund and backtest workflow. The goal was to generate the required portfolio output files before working on sentiment analysis, fusion, figures, the report, or the Streamlit app.

### Prompt(s)
I asked Codex to implement a simple, reproducible baseline workflow that generates:

- `results/data/fund_returns.csv`
- `results/data/fund_weights.csv`
- `results/tables/performance_metrics.csv`

I instructed Codex to implement:

- `daily_returns()` in `src/features.py`;
- `performance_metrics()` and `oos_backtest()` in `src/portfolios.py`;
- updates to `scripts/run_part_b.py` to load the data, cap the sample at 2023-12-31, calculate returns before merging, align equity and crypto calendars, run equal-weight and minimum-variance backtests, and save the required CSV outputs.

I also asked Codex not to implement sentiment analysis yet, not to edit the Streamlit app yet, and to add comments explaining how look-ahead bias is avoided.

### What the assistant produced
Codex edited three files:

- `src/features.py`
- `src/portfolios.py`
- `scripts/run_part_b.py`

It implemented adjusted-close daily returns, a combined equity-and-crypto return panel, an equal-weight fund, a long-only minimum-variance fund, a 252-observation walk-forward estimation window, month-end rebalancing, performance metrics, and CSV exports.

The generated outputs were:

- `results/data/fund_returns.csv` with 1,470 rows
- `results/data/fund_weights.csv` with 4,320 rows
- `results/tables/performance_metrics.csv` with 2 rows

### What was wrong or risky
The implementation was only a baseline. It did not include sentiment analysis, sentiment fusion, required figures, the written report, or the Streamlit app.

There were also modelling risks. Complete-case filtering may affect the asset universe. Minimum-variance results may be sensitive to covariance estimation error. The baseline also assumes zero transaction costs, no turnover costs, and a zero risk-free rate.

### What I changed and why
I allowed Codex to run `python scripts/run_part_b.py` and `python scripts/check_handin.py`, then checked the reported outputs.

The script generated the required CSV files. The output schemas matched the required column names, there were no missing values, the portfolio weight vectors summed to 1, and both backtests covered 735 observations from 2021-01-29 to 2023-12-29.

`check_handin.py` reported 20 checks passed. I kept this as the baseline fund and backtest implementation, but noted that sentiment analysis, figures, the report, and the Streamlit app still need to be completed later.


## Entry 3: Creating baseline performance figures

### What I wanted
I wanted to create the required baseline performance figures for Project B using the portfolio outputs that had already been generated. The goal was to produce report-ready figures without recomputing the backtest.

### Prompt(s)
I asked Codex to create four figures under `results/figures/` using the existing CSV outputs:

- `results/data/fund_returns.csv`
- `results/data/fund_weights.csv`
- `results/tables/performance_metrics.csv`

The requested figures were:

- `results/figures/fund_growth_1.png`
- `results/figures/fund_drawdown.png`
- `results/figures/fund_weights_over_time.png`
- `results/figures/fund_risk_return.png`

I instructed Codex to load the existing CSV files, add clear chart titles, axis labels, legends, and source/sample-period notes, and keep the figures clean enough for the report. I also asked it to update `scripts/run_part_b.py` if appropriate so the figures could be reproduced when the main script runs.

### What the assistant produced
Codex created a new script:

- `scripts/make_part_b_figures.py`

It also updated:

- `scripts/run_part_b.py`

The new figure script reads the existing CSV outputs and creates four PNG figures:

- `results/figures/fund_growth_1.png`
- `results/figures/fund_drawdown.png`
- `results/figures/fund_weights_over_time.png`
- `results/figures/fund_risk_return.png`

The figures include a growth-of-$1 comparison, a drawdown chart, a top-10 minimum-variance weights chart, and an annualised risk-return chart with Sharpe ratio labels.

### What was wrong or risky
One formatting issue appeared during validation. The growth-of-$1 chart used a log scale, but Matplotlib initially displayed the y-axis in scientific notation, which was not suitable for a report.

There were also general presentation risks. The portfolio weights chart could become too crowded because the combined universe has 60 assets. To make the chart readable, Codex plotted the ten assets with the largest average absolute weights for the minimum-variance fund.

### What I changed and why
Codex corrected the growth chart by changing the y-axis tick formatter to readable dollar labels. It then regenerated the figures and reran the checks.

The figures were exported as 300-DPI PNG files. Codex also checked image dimensions and blankness, visually inspected the rendered charts, and confirmed that the figures did not have major clipping, legend overlap, or readability problems.

I kept these figures because they satisfy the required baseline performance exhibits and can be inserted into the Project B report later. `python scripts/run_part_b.py` completed successfully, and `python scripts/check_handin.py` reported 20 checks passed. The remaining warnings are expected because sentiment analysis and the report have not been completed yet.


## Entry 4: Building the standalone sector sentiment index

### What I wanted
I wanted to build the standalone sector sentiment index required for Project B. The goal was to generate `results/data/sector_sentiment_index.csv` and a readable sentiment figure before working on sentiment fusion or the Streamlit app.

### Prompt(s)
I asked Codex to implement a standalone sentiment index using the provided news headlines. I instructed it to:

- load news headlines using the provided data access helper;
- remove exact duplicate headlines using ticker, date, and title;
- preserve the original headline text as much as possible;
- calculate headline sentiment using VADER;
- aggregate from headline level to ticker-day level first;
- then aggregate from ticker-day sentiment to sector-day sentiment by equal-weighting tickers;
- align non-trading-day headlines to the next equity trading day;
- lag the signal by at least one additional trading day to avoid look-ahead bias;
- save `results/data/sector_sentiment_index.csv`;
- create `results/figures/sector_sentiment_index.png`;
- update `scripts/run_part_b.py` so the sentiment output is reproduced when the main script runs.

### What the assistant produced
Codex edited three files:

- `src/sentiment.py`
- `scripts/run_part_b.py`
- `scripts/make_part_b_figures.py`

It implemented headline cleaning, VADER scoring, equity-calendar alignment, one-trading-day lagging, ticker-day aggregation, and sector-day aggregation.

The generated outputs were:

- `results/data/sector_sentiment_index.csv`
- `results/figures/sector_sentiment_index.png`

The sentiment CSV contains 9,831 sector-day observations with the columns `date`, `sector`, `sentiment_index`, `headline_count`, and `ticker_count`. The figure shows all ten sectors as small multiples, with daily sentiment shown as faint lines and 21-observation rolling means shown as darker lines.

### What was wrong or risky
The first run exposed a date-format issue. Headline timestamps were timezone-aware, while the equity trading calendar was timezone-naive. This caused a datetime comparison error.

There were also modelling risks. VADER is a general-language sentiment tool, so it may not fully understand finance-specific meanings, sarcasm, or ambiguous headlines. Days without sector news are omitted rather than filled with neutral sentiment.

### What I changed and why
Codex fixed the timezone issue by normalising both headline dates and equity calendar dates to timezone-free calendar dates before alignment. It then reran the full reproduction script.

The final sentiment output passed validation. There were no missing values, no duplicate sector-date rows, no weekend output dates, and VADER scores stayed within a reasonable range. `python scripts/run_part_b.py` completed successfully, and `python scripts/check_handin.py` reported 21 checks passed.

I kept this output because it satisfies the standalone sector sentiment index requirement and avoids look-ahead bias by mapping headlines to the equity calendar and then shifting the signal forward by one trading day.


## Entry 5: Implementing the sentiment fusion extension

### What I wanted
I wanted to implement the sentiment fusion extension for Project B. The goal was to compare a base equity fund with a sentiment-augmented equity fund in a look-ahead-safe way.

### Prompt(s)
I asked Codex to create a comparison between:

- a base equity fund; and
- a sentiment-augmented equity fund.

I instructed Codex to use only equity assets, because crypto has no headline sentiment data. I also asked it to use the precomputed `results/data/sector_sentiment_index.csv`, apply only lagged sentiment values, map each equity ticker to its sector, and create a simple sentiment tilt rule.

The required outputs were:

- `results/tables/sentiment_fusion_metrics.csv`
- `results/figures/sentiment_fusion_growth.png`
- `results/figures/sentiment_fusion_risk_return.png`

I also asked Codex to update `scripts/run_part_b.py`, run the full reproduction script, and validate that there were no missing values, the weights summed to 1, and the sentiment-augmented fund did not use future sentiment.

### What the assistant produced
Codex edited three files:

- `src/fusion.py`
- `scripts/run_part_b.py`
- `scripts/make_part_b_figures.py`

It implemented an equity-only sentiment fusion backtest. The base equity fund used equal weights across the 50 equities. The sentiment-augmented fund also started from equal weights, but applied a small sector sentiment tilt at each monthly rebalance.

Codex generated:

- `results/tables/sentiment_fusion_metrics.csv`
- `results/figures/sentiment_fusion_growth.png`
- `results/figures/sentiment_fusion_risk_return.png`

### What was wrong or risky
The main risk was look-ahead bias. If the sentiment tilt used same-day or future sentiment, the comparison would not be valid. There were also modelling risks because the sentiment tilt rule uses judgement-based choices, including a 21-observation sentiment window and a 0.5 percentage-point maximum weight adjustment.

Another risk is that VADER is not finance-specific, so the sentiment signal may not correctly capture financial meaning in all headlines. Transaction costs and turnover costs are also not included.

### What I changed and why
Codex added validation checks to confirm that the sentiment date used for each rebalance was strictly earlier than the rebalance date. It also checked that the sentiment-augmented portfolio remained long-only and fully invested.

The tilt rule was kept simple and explainable:

- start with 2% in each of the 50 equities;
- use each sector's latest 21 available sentiment observations at each month-end rebalance;
- only use sentiment dates strictly before the rebalance date;
- map sector sentiment scores to equities;
- demean and scale the scores;
- adjust each stock weight by no more than ±0.5 percentage points;
- keep all weights positive and normalise them to sum to 1.

The results showed that the sentiment-augmented fund underperformed the base equity fund. The annualised return and Sharpe ratio were slightly lower, while volatility and maximum drawdown improved slightly. I kept the result rather than forcing the sentiment strategy to improve performance, because the project requires a measured before-and-after comparison.

`python scripts/run_part_b.py` completed successfully, and `python scripts/check_handin.py` reported 21 checks passed.


## Entry 6: Building the Streamlit app

### What I wanted
I wanted to build the investor-facing Streamlit app for Project B. The goal was to create a simple Wealth Radar dashboard that reads the precomputed project outputs and presents them clearly to users.

### Prompt(s)
I asked Codex to implement `streamlit_app.py` and create an app that allows users to:

- compare funds;
- read fund fact sheets;
- set an allocation across funds;
- view sector sentiment analytics;
- view the sentiment fusion before/after comparison.

I also instructed Codex not to recompute backtests, not to run VADER or NLTK, and not to download raw data in the app. The app needed to load only precomputed CSV and PNG files from the `results/` folder.

### What the assistant produced
Codex edited:

- `streamlit_app.py`

It created six Streamlit pages:

- Overview
- Fund comparison
- Fund fact sheets
- Allocation simulator
- Sentiment analytics
- Sentiment fusion

The app includes fund KPI tables, latest holdings, allocation normalisation, simulated allocation growth and metrics, sector sentiment previews, and a clear explanation that the sentiment-augmented equity fund underperformed the base equity fund in this sample.

### What was wrong or risky
The main risk was that the app could accidentally recompute raw data, backtests, or sentiment analysis during deployment. This would make the app slower and could violate the project requirement that the deployed app should load precomputed outputs only.

Another issue was that a generic repository deployment helper expected the app entrypoint to be located at `app/streamlit_app.py`. However, this Project B folder uses the required root-level entrypoint `streamlit_app.py`, so Codex did not move or duplicate the file.

There are also practical deployment risks. The working tree still needs to be committed and pushed before Streamlit Community Cloud deployment. Some pages use PNG figures, which may load more slowly than fully interactive charts, but this keeps dependencies light and avoids recomputation.

### What I changed and why
Codex replaced the starter app with a local-results-only dashboard. The final app:

- reads only CSV and PNG files under `results/`;
- makes no network requests;
- imports no raw-data loaders;
- imports no portfolio backtest functions;
- imports no VADER or NLTK;
- only calculates allocation-simulator results by combining already precomputed fund daily returns.

Codex also added friendly missing-file messages, so the app tells the user to run `python scripts/run_part_b.py` if required result files are missing.

Validation was successful. `python scripts/run_part_b.py` ran successfully, all six pages passed Streamlit testing with zero runtime exceptions, a real headless `streamlit run streamlit_app.py` server returned `200 ok`, Python compilation passed, static scanning found no prohibited runtime imports or calls, and `python scripts/check_handin.py` reported 21 checks passed.


## Entry 7: Adding the crypto-only fund extension

### What I wanted
I wanted to strengthen the Project B fund coverage by adding crypto-only funds. The goal was to make the project cover combined equity-and-crypto funds, equity-only sentiment funds, and crypto-only funds, which better supports the higher-band requirement for multiple fund families.

### Prompt(s)
I asked Codex to add a crypto-only fund extension while keeping the implementation simple, reproducible, and consistent with the existing backtest design.

I instructed Codex to create two crypto-only funds:

- `crypto_equal_weight`
- `crypto_min_variance`

I also asked it to:

- use crypto returns only;
- use a walk-forward out-of-sample backtest;
- avoid look-ahead bias by forming weights only from past data;
- use the native seven-day crypto calendar;
- use a 365-observation estimation window;
- use 365-day annualisation for crypto-only performance metrics;
- keep the existing combined and equity-only results unchanged;
- update `fund_returns.csv`, `fund_weights.csv`, and `performance_metrics.csv`;
- create a crypto-only growth figure if useful;
- update the Streamlit app so the crypto funds appear in the overview, fund comparison, fact sheets, and allocation simulator;
- run `python scripts/run_part_b.py`, `streamlit run streamlit_app.py`, and `python scripts/check_handin.py`.

### What the assistant produced
Codex edited four files:

- `src/portfolios.py`
- `scripts/run_part_b.py`
- `scripts/make_part_b_figures.py`
- `streamlit_app.py`

It added two crypto-only funds:

- `crypto_equal_weight`
- `crypto_min_variance`

Codex also created:

- `results/figures/crypto_only_growth.png`

It updated the shared output files:

- `results/data/fund_returns.csv`
- `results/data/fund_weights.csv`
- `results/tables/performance_metrics.csv`

The Streamlit app was also updated so that the crypto-only funds appear in fund summaries, fact sheets, comparisons, and the allocation simulator.

### What was wrong or risky
The main modelling risk was that crypto trades on a seven-day calendar, while the existing combined fund is aligned to the equity trading calendar. If annualisation or calendar alignment was handled incorrectly, the crypto-only results would not be comparable.

Another risk was that the minimum-variance crypto portfolio could become highly concentrated because the crypto universe is small and covariance estimates can be unstable. The final summary noted that crypto minimum-variance weights can reach 100% in one asset for some rebalances.

There were also real-world risks that the model does not include, such as transaction costs, liquidity, turnover, and exchange-specific execution risks.

### What I changed and why
Codex made the estimation window in `src/portfolios.py` configurable while keeping the existing 252-day default unchanged. This allowed the combined and equity funds to keep their original settings, while crypto-only funds used a 365-observation rolling estimation window.

The crypto-only funds used:

- crypto returns only;
- the native seven-day crypto calendar;
- a 365-observation estimation window;
- month-end rebalancing on the final available crypto date;
- historical returns ending at `t-1` to form weights applied on `t`;
- long-only, fully invested portfolios.

The crypto-only performance results were:

- `crypto_equal_weight`: annualised return 16.14%, volatility 78.87%, Sharpe ratio 0.59, maximum drawdown -81.60%.
- `crypto_min_variance`: annualised return 21.28%, volatility 62.17%, Sharpe ratio 0.62, maximum drawdown -75.60%.

The results showed that crypto minimum variance had the highest annualised return among the four main funds, but it did not improve the best risk-adjusted result. The combined equal-weight fund still had the highest Sharpe ratio. This suggests that crypto added return potential but also much higher volatility and drawdown risk.

Codex validated that there were no missing crypto fund returns, all monthly crypto weight vectors summed to one, crypto weights used only the preceding 365 observations, all six app pages passed runtime tests, the real Streamlit server returned `200 ok`, and `python scripts/check_handin.py` reported 21 checks passed.
