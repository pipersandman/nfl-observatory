# Social posts

Weekly post images (1080×1350) + captions, generated from the same data as the site.

## Series

| Series | Hashtag | When | Command |
|---|---|---|---|
| Laundry Day | #LaundryDay | Mon/Tue (after games) | `--kind laundry` |
| Final Flags | #FinalFlags | Mon/Tue (one per game) | `--kind final` (or `--game ID`) |
| Flag Forecast | #FlagForecast | Tue noon (after crews post) | `--kind forecast` |
| Division Laundry | #DivisionLaundry | Wed | `--kind division` (rotates; or `--division "NFC East"`) |
| Team Laundry | #TeamLaundry | Wed | `--kind team` (3 biggest movers; or `--team DAL`) |
| Under the Hood | #UnderTheHood | Fri | `--kind hood` (new question each week, see `t_hood`) |
| Flag Magnets | #FlagMagnets | Sat | `--kind magnets` |
| Flag Watch | #FlagWatch | Before each game | `--kind watch --game 2026_05_TB_DAL` |

Umbrella tag on every post: **#FlagData**

## Setup (once)

```powershell
pip install playwright
python -m playwright install chromium
```

## Weekly use

```powershell
python scripts/social/generate.py --week 5 --kind final --kind laundry   # Monday/Tuesday recaps
python scripts/social/generate.py --kind forecast                         # Tuesday after crews post
python scripts/social/generate.py --kind watch --game 2026_05_TB_DAL      # before a game
```

Images and `captions.md` (caption, alt text, hashtags, tracking link) land in `social/output/{season}-week-NN/`.
**Review every number before posting.**

## Projection snapshots

Posting a **Flag Watch** freezes that game's projection in `social/snapshots/` (committed to git).
The **Final Flags** recap then shows "projected X → actual Y" against the number we actually published.
Commit the snapshot after generating a Flag Watch.

## New "Under the Hood" questions

Copy `hood_close_games()` in `generate.py`, compute your numbers, and return the same fields
(question, stat, stat_label, bars, takeaway, method, slug). The template handles the layout.
