# Approach Summary — Round 0 (Ignition)

## 1. Repairs & Fixes

The tool ran without crashing but produced wrong numbers. Four code-level issues were fixed:

- **Command injection** — `os.system("echo ... " + REPORT_EMAIL)` concatenated user-controlled input into a shell call. Replaced with a plain `print()`.
- **Silent data loss** — a bare `except: pass` silently swallowed every row that failed the medal lookup. Replaced with `except KeyError:` and a skip counter that reports how many rows were dropped and why.
- **Non-numeric DataFrame** — `pd.DataFrame(counts).T` produced object-dtype columns, making numeric sort unreliable. Fixed with `pd.DataFrame.from_dict(..., orient="index", dtype=float)`.
- **Hardcoded API token** — a live credential was committed in source. Moved to `os.environ.get()`.

## 2. Data Decisions That Mattered

Fixing the code revealed two data quality issues that had a direct impact on the leaderboard counts:

- **Medal aliases (579 rows)** — the `medal` column contained valid medals in non-canonical form: `GOLD`, `gold`, `1st`, `2nd`, `3rd`, `G`, `S`, `B`, and `Silver ` with a trailing space. All were silently dropped by the original KeyError. A `normalise_medal()` function was added to map every variant to the canonical `Gold / Silver / Bronze` before lookup — recovering 579 real medals.
- **Missing country codes (40 rows)** — 40 rows had `NaN` in `country_code`. Rather than dropping them, a `country_name → country_code` mapping was built from the rest of the dataset. All 40 resolved cleanly with no ambiguity. An important subtlety: `str(NaN)` = `"nan"` which is truthy, so a simple `if not country` guard would silently bucket all 40 under a phantom `"nan"` country. The fix uses `pd.isna()` to detect nulls correctly.

Net effect: the repaired tool processes all 19,326 rows versus the original's effective 18,747.

## 3. Finding

We tested the popular hypothesis that hosting the Olympics gives a country a medal boost. Using the repaired leaderboard, we compared each host nation's medal count in their hosting year against their per-Games average across all other years.

The result holds: **12 of 13 hosts recorded more medals at home**, with a **median boost of +54%**. The two largest raw boosts (URS 1980, USA 1984) were driven by Cold War boycotts — the main competitor was absent. Removing those years, the pattern still holds across 12 of 13 remaining cases. The sole exception is **Greece 2004** (−13%), where hosting infrastructure investment did not translate to athlete performance.

Caveat: sample is small (one hosting event per country) and the dataset is synthetic — the direction is consistent but the magnitude should not be over-interpreted.
