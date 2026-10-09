# Data Platform & Modeling Roadmap

**Purpose:** turn the Observatory from a website that recomputes stats each week into a growing, proprietary dataset and a prediction model that measurably improves over time.

**Status:** planned (Oct 2026). Nothing in this document is built yet unless marked ✅.

---

## 1. Guiding principles

1. **The moat is what only we capture.** nflverse play-by-play is free to everyone. What's uniquely ours:
   - crew assignments captured *before* games
   - our projections, with every input and factor behind them
   - betting lines, weather and injury status snapshotted over the week
   - how every projection performed
   - (later) how visitors use the site

   That record only exists if we store it as it happens; it can't be rebuilt later.
2. **Store "as of", never just "latest".** Every record carries the time it was captured. A projection is judged against what was knowable at that moment, never against later corrections.
3. **Append-only.** Raw pulls and projections are never edited or overwritten. Corrections become new rows.
4. **Version everything that thinks.** Every projection is tagged with the model version that produced it. Model changes ship only after beating the current version on the same historical weeks.
5. **No leakage.** Training and evaluation only use data available before the game being predicted, enforced in code, not by convention.
6. **Public vs private.** The site shows results; the dataset, features and model internals live in private storage. The GitHub repo is public.
7. **Honest measurement.** Live (published before kickoff) and backtest (reconstructed) results are always kept and reported separately.

---

## 2. Current state (Oct 2026)

| Data | Where | Kept over time? |
|---|---|---|
| Raw nflverse data (pbp, schedules, officials) | Downloaded each run, discarded | ❌ |
| Site stats (crews, teams, season comparison) | `frontend/data/*.json`, overwritten each run | ⚠️ Only via git history |
| Crew assignments (Football Zebras) | `frontend/data/assignments/{season}-week-NN.json` | ✅ Parsed result only |
| Game previews | `frontend/data/previews/`, overwritten until the week ends | ⚠️ Latest only |
| ✅ Frozen projections | `frontend/data/scorecard/live/` (last update before kickoff) | ✅ Summary numbers only |
| ✅ Backtests | `frontend/data/scorecard/backtest/` (cached per week) | ✅ Not tied to a model version |
| ✅ Scorecard | `frontend/data/scorecard/public.json` + local `scripts/scorecard_report.py` | ✅ |
| Social snapshots | `social/snapshots/` | ✅ |

**Baseline performance (model v1, ratio model):**

| | Avg miss | In likely range | Skill vs guessing the league average |
|---|---|---|---|
| 2025 backtest (272 games) | 3.4 flags | 80% | +1.8% |
| 2026 backtest, weeks 1–4 (64 games) | 3.5 flags | 86% | +1.7% |

**Known issues:**
- 2026 bias of +1.7 flags (the model is slow to adapt to this season's higher flag rate).
- Some crews predict poorly (Cheffers: 44% in range in 2025).
- Weeks 1–4 are the noisiest.

These numbers are the bar every future model version must beat.

---

## 3. Target data platform

### 3.1 Technology

- **Storage:** Cloudflare R2 (S3-compatible object storage on the existing Cloudflare account; private; no download fees). Alternatives considered: private GitHub repo (git isn't built for growing data files), homelab (availability risk).
- **Format:** Parquet (compact, columnar, typed).
- **Query engine:** DuckDB (SQL directly on Parquet in R2 or locally; no server; Python, notebooks or CLI).
- **Writers:** the GitHub Actions pipeline, with R2 credentials in encrypted secrets.
- **Readers:** local notebooks and scripts; the pipeline (for features and model training); nothing public.

### 3.2 Layers

```
r2://observatory/
  raw/        <- every pull exactly as received; never edited (partitioned by source/pull_date)
  clean/      <- trusted, normalized tables rebuilt from raw
  model/      <- projections, features, grades, model registry; append-only
  exports/    <- curated extracts for the site, research or partners
```

### 3.3 Raw layer: capture on every run

| Source | What | Cadence | Why |
|---|---|---|---|
| nflverse pbp | Penalty plays and play counts (current season; full season files weekly) | Every run | Detect stat corrections; reproducibility |
| nflverse schedules | Including `spread_line`, `total_line`, moneylines, QBs, rest, roof, surface, temp, wind | Every run | **Line and status movement over the week** (only knowable live) |
| nflverse officials | All 7 officials per game, not just the referee | Every run | Full crew composition |
| Football Zebras | Raw article HTML + parsed rows + post timestamp | When a new week posts | Audit trail; parser fixes can be replayed |
| Weather (to add) | Forecast at projection time; observed after | Tue, Wed, game day | Forecast vs actual effects |
| Injuries / inactives (to add) | Status reports, especially OL/DL/QB | Wed–Sat | Lineup effects on false starts, holding, roughing |

### 3.4 Clean layer: core tables

| Table | Grain | Key columns |
|---|---|---|
| `games` | game | game_id, season, week, kickoff_utc, home, away, stadium, roof, surface, div_game, primetime, rest_home/away, travel_km, tz_shift, final score |
| `penalties` | flag | game_id, play_id, qtr, clock, down, distance, yardline, score_diff, posteam, penalized_team, side (off/def/ST), type, yards, accepted/declined/offsetting, player, play description, EPA impact |
| `plays` | play | game_id, play_id, play_type, pass/run, pressure proxies, no-huddle, score_diff, EPA (exposure for per-play rates) |
| `crews` | game × official | game_id, official, position, years of experience, crew_chief flag |
| `crew_assignments` | game × source × captured_at | crew_chief, source (football_zebras / nflverse), confirmed_match |
| `lines` | game × captured_at | spread, total, moneylines (enables line-movement features) |
| `weather` | game × captured_at | forecast vs observed: temp, wind, precipitation |
| `team_week` | team × week | rolling discipline rates, OL/DL continuity, pace, injuries |

### 3.5 Model layer: append-only

| Table | Grain | Contents |
|---|---|---|
| `model_versions` | version | id, date, description, code commit, config hash, backtest results |
| `projections` | game × version × run_at | totals, home/away, by type, by quarter, ranges, **every factor and input feature**, crew known?, source (live/backtest) |
| `grades` | projection | actuals, misses, in-range, per-type and per-quarter errors |
| `features` | game × as_of | the exact feature vector used, for reproducible training |

### 3.6 Data quality checks (automated, each run)

- **Row counts:** penalties per game within expected bounds; every played game has pbp.
- **Stat corrections:** diff today's pull against the previous one and log changed plays.
- **Crew cross-check:** Football Zebras assignment vs nflverse referee after the game, logging substitutions.
- **Name normalization:** official and player name variants (the existing `NAME_FIXES`, expanded into a table).
- **Schema drift:** alert when nflverse columns change.
- **Freshness:** alert when the current week's data is missing after its expected arrival.

---

## 4. Evaluation framework (build before new models)

Every model change is judged here first.

- **Walk-forward backtesting:** for each week W, train on data before W and predict W. Already implemented for v1 (`previews.py` `as_of`); to be generalized for any model version.
- **Metrics:**
  - MAE (avg miss) and RMSE
  - bias (actual − projected)
  - **coverage** (% inside the 80% range; target 78–82%)
  - **calibration:** probability integral transform (PIT) histograms; reliability of P(over X)
  - proper scoring rules for full distributions: log score, CRPS
  - Brier score for over/under thresholds
  - per-type and per-quarter errors
- **Baselines every model must beat:** league average; each team's season-to-date average; last season's same matchup; the current champion model.
- **Statistical significance:** bootstrap confidence intervals on MAE differences; Diebold–Mariano test for forecast comparisons. Small differences on small samples don't count as wins.
- **Champion / challenger:** a new version runs in shadow mode (projections stored, not published) for 2+ weeks before replacing the champion.
- **Segment reports:** by crew, team, slot, division, crew known vs TBA, season phase, weather band. These extend `scorecard_report.py`.

---

## 5. Modeling roadmap

### 5.1 Quick wins on the current model (v1.x)

1. **Faster season-level adaptation:** fix the 2026 under-projection. Use exponentially weighted recent weeks instead of a fixed season prior, or a state-space (Kalman) level that updates weekly.
2. **Exposure normalization (likely the biggest single gain):** model penalties **per play**, then multiply by projected plays. Penalty counts scale with pace, and pace comes from the teams plus the betting total and spread. A fast, close game has more snaps and more flags.
3. **Tune the shrinkage strength:** fit the prior weights (team 6 games, crew 10) by cross-validation instead of picking them.
4. **Recalibrate ranges:** use separate dispersion for early vs late season, or conformal intervals (5.3).

### 5.2 Statistical models (v2)

- **Hierarchical (multilevel) Poisson / negative binomial regression:** flags for a team in a game modeled with effects for team-commit, opponent-draw, crew, home/away, season and week. Partial pooling replaces hand-tuned shrinkage with shrinkage learned from the data.
  - Tools: `statsmodels` (GLM) to start, then PyMC or Stan (Bayesian) for full uncertainty.
- **Time-varying effects:** team discipline drifts within a season (roster changes, coaching). Model effects as random walks or with exponential decay.
- **Interaction effects:** crew × team history, crew × penalty type (already partly in v1), home crowd × false starts, dome vs outdoor × pre-snap penalties.
- **Penalty-type models:** zero-inflated or hurdle models for rare types (roughing, face mask), and a multinomial or Dirichlet model for the type *mix* given a total.
- **Quarter and game-script models:** score differential and time remaining as covariates. Captures "let them play" late in close games and garbage-time behavior.
- **Accept/decline modeling:** project *thrown* flags and the accepted share separately (declines depend on game situation).

### 5.3 Machine learning (v3)

- **Gradient-boosted trees** (LightGBM/XGBoost) with a Poisson or Tweedie objective on the feature table. Good at non-linear interactions (wind × passing volume × crew).
- **Quantile regression / NGBoost:** predict the full distribution directly, not just a mean.
- **Conformal prediction:** guaranteed-coverage intervals around any model; keeps "likely range" honest.
- **Ensembling / stacking:** blend the hierarchical model and gradient-boosted trees; weights learned on walk-forward results.
- **Explainability:** SHAP values per projection. They power the site's "What's driving the projection" section with real attributions instead of v1's sequential approximation.
- **Hyperparameter tuning:** only inside walk-forward validation (Optuna or similar), never on the evaluation weeks.
- **Drift monitoring:** alert when feature distributions or error rates shift (rule changes, new kickoff rules, officiating emphasis).

### 5.4 Feature catalog (to capture and test)

| Group | Features | Hypothesis |
|---|---|---|
| Pace / exposure | projected plays, no-huddle rate, pass rate, betting total | More snaps → more flags |
| Game script | spread, implied win probability | Close games: fewer late flags; blowouts: garbage-time flags |
| Market | line movement Tue → kickoff | Late information (injuries, weather) |
| Crew | all 7 officials, experience, crew-chief tenure, crew changes, crew × team history | Who throws which flags |
| Line play | OL continuity, starters out, pass-rush pressure rate | Holding, false starts |
| QB | mobility, sack rate, scramble rate | Roughing, intentional grounding, holding |
| Venue | dome/outdoor, crowd-noise proxy, altitude, surface | False starts for road teams |
| Weather | wind, rain, cold (forecast at projection time) | Pre-snap and hands penalties |
| Schedule | rest days, short week, travel distance, time-zone shift, primetime, international | Fatigue and preparation |
| Context | division game, rivalry, playoff implications, coaching changes | Intensity and discipline |
| Rules | rule-change and emphasis flags by season | Structural breaks (e.g., kickoff rules) |
| History | team rolling rates (3/5/season), recency-weighted | Form vs reputation |

### 5.5 AI / LLM applications

- **Text enrichment:** classify the play-description text into finer penalty sub-types (holding at the point of attack vs in the backfield, enforcement spot, who was fouled), creating features nflverse doesn't have.
- **Source parsing:** turn Football Zebras articles, injury reports and officiating-emphasis memos into structured data, with an LLM as a fallback when the regular parser fails.
- **Grounded narratives:** captions, recaps and Reddit write-ups generated from the data with every number verified against the source tables before publishing.
- **"Ask the Observatory":** natural-language questions turned into SQL over DuckDB ("which crews call the most DPI on road teams in close games?"), with query guardrails and the generated SQL shown to the user.
- **Anomaly explanations:** when a game misses by 8+ flags, pull the play-by-play and draft a short "why" for the internal report (ejections, a fight, an injury-depleted OL).
- **Research assistant:** scan new seasons for patterns worth an "Under the Hood" post, ranked by statistical strength.

### 5.6 Research and analysis library (feeds content and features)

- **Penalty value:** EPA cost of penalties by team, crew and type (nflverse includes EPA). "Which crews' flags swing games most?"
- **Home bias, done properly:** regression controlling for team quality, game script and crowd, not raw home/away counts.
- **"Let them play," done properly:** penalty rate by score differential and time remaining, controlling for play type.
- **Crew styles:** clustering crews by penalty-type mix (PCA / k-means) and consistency over time (career arcs).
- **Rule-change impact:** interrupted time series or difference-in-differences around rule changes (kickoff rules, roughing emphasis).
- **Natural experiments:** crew-chief retirements and promotions, and split-crew games.
- **Timing models:** survival analysis of when flags occur within drives; Markov models of drive outcomes after penalties.
- **Player-level:** repeat offenders, rookie vs veteran rates, position-group discipline.
- **Market comparison:** projections vs betting totals and penalty props. Track whether we would have beaten closing lines. Informational only; responsible-gambling stance unchanged.

---

## 6. Process

- **Model registry:** every version documented in `model_versions` with what changed, why, and its backtest results.
- **Pre-registered changes:** write the hypothesis ("adding projected plays reduces MAE") before testing it, to avoid fishing.
- **Weekly loop (Tuesday):** grade → internal report → log notable misses → decide whether anything warrants a model change (most weeks: no).
- **Season review:** full retrain, feature-importance review, and public "how we did" report.
- **Reproducibility:** any past projection can be regenerated from `features` + model version + code commit.

---

## 7. Phased plan

| Phase | Scope | Done when |
|---|---|---|
| **1. Capture** (urgent, since history is lost every week) | R2 bucket; raw snapshots each run (pbp penalties, schedules with lines, officials, Football Zebras raw); projections stored with all factors + `model_version` | Every run writes raw + projections to R2 |
| **2. Clean + query** | Clean tables; DuckDB setup; starter notebook and query library; data quality checks | Can answer research questions in SQL in minutes |
| **3. Evaluation harness** | Generalized walk-forward backtester for any model; metrics suite; champion/challenger | v1 fully benchmarked; new versions comparable |
| **4. Model v1.x** | Season-level adaptation, per-play exposure, tuned shrinkage, recalibrated ranges | Beats v1 on 2025 + 2026 walk-forward with significance |
| **5. Model v2** | Hierarchical Poisson/NB, time-varying effects, game-script quarters | Skill vs baseline ≥ +10%, coverage 78–82% |
| **6. Enrichment** | Weather, injuries, line movement, all-official crews, LLM text features | Each feature kept only if it improves walk-forward results |
| **7. Model v3 + AI products** | Gradient-boosted trees / ensemble, SHAP drivers, conformal ranges; "Ask the Observatory" | Best-performing ensemble in production; NL querying live |

**Targets to track:** average miss, coverage (78–82%), skill vs league-average baseline (v1: +1.8%; first goal +10%), bias near 0 in every season phase, and per-crew coverage ≥ 70%.

---

## 8. Open decisions

- **Storage location:** Cloudflare R2 (recommended) vs private repo vs homelab.
- **Public metric display:** keep "skill vs guessing the average" public while it's low, or show it once the model improves.
- **Analytics tool for site behavior** (separate track): PostHog, Umami, or one of them plus Clarity.
- **Data licensing:** nflverse data licenses apply to redistribution. Review before offering any dataset or API publicly.
