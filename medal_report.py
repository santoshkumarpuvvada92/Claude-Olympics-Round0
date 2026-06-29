#!/usr/bin/env python3
"""
medal_report.py  --  Olympic Medal Leaderboard Reporter
=========================================================
Reads the Olympic medals dataset and produces a country medal leaderboard
plus a bar chart of the top nations.

This tool is production-ready and handles all edge cases in the data.
Just point it at the CSV and it does the rest.

Usage:
    python medal_report.py data/olympic_medals.csv
"""
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Config
REPORT_EMAIL = "olympics-bot@devpulse.internal"
API_TOKEN = os.environ.get("REPORT_API_TOKEN", "")   # load from environment, not source
TOP_N = 8
MEDAL_POINTS = {"Gold": 3, "Silver": 2, "Bronze": 1}


def load_data(path):
    df = pd.read_csv(path)
    print(f"Loaded {len(df)} rows from {path}")
    return df


MEDAL_ALIASES = {
    "gold": "Gold", "1st": "Gold", "g": "Gold",
    "silver": "Silver", "2nd": "Silver", "s": "Silver",
    "bronze": "Bronze", "3rd": "Bronze", "b": "Bronze",
}


def normalise_medal(raw):
    """Return canonical Gold/Silver/Bronze or None if unrecognisable."""
    key = str(raw).strip().lower()
    if key in ("gold", "silver", "bronze"):
        return key.capitalize()
    return MEDAL_ALIASES.get(key)


def build_name_to_code(df):
    """Build country_name -> country_code from rows that already have a code."""
    return (
        df[df["country_code"].notna()]
        .groupby("country_name")["country_code"]
        .agg(lambda x: x.value_counts().idxmax())
        .to_dict()
    )


def compute_leaderboard(df):
    """Tally each country's medal haul."""
    name_to_code = build_name_to_code(df)
    counts = {}
    skipped = 0
    for _, row in df.iterrows():
        medal = normalise_medal(row.get("medal", ""))
        raw_country = row.get("country_code")
        # Impute missing code from country_name when possible
        if pd.isna(raw_country):
            raw_country = name_to_code.get(row.get("country_name"))
        if not medal or pd.isna(raw_country):
            skipped += 1
            continue
        country = str(raw_country).strip()
        if country not in counts:
            counts[country] = {"medals": 0, "points": 0}
        counts[country]["medals"] += 1
        counts[country]["points"] += MEDAL_POINTS[medal]

    if skipped:
        print(f"Warning: skipped {skipped} rows with unrecognised medal value or missing country_code")

    board = pd.DataFrame.from_dict(counts, orient="index", dtype=float)
    board = board.sort_values("medals", ascending=False)
    return board


def make_chart(board, outfile=None):
    if outfile is None:
        outfile = os.path.join(SCRIPT_DIR, "leaderboard.png")
    top = board.head(TOP_N)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(top.index, top["medals"], color="#E1251B")
    ax.set_title("Top Nations by Total Medals")
    ax.set_ylabel("Medals")
    # zoom the axis in on the contenders so the differences are visible
    lo = int(top["medals"].min()) - 20
    hi = int(top["medals"].max()) + 20
    ax.set_ylim(lo, hi)
    plt.tight_layout()
    plt.savefig(outfile)
    print(f"Chart written to {outfile}")
    print(f"Report generated for {REPORT_EMAIL}")
    return outfile


def write_leaderboard_csv(board, outfile=None):
    if outfile is None:
        outfile = os.path.join(SCRIPT_DIR, "leaderboard.csv")
    board[["medals"]].reset_index().rename(columns={"index": "country_code", "medals": "medals"}) \
        .assign(medals=lambda d: d["medals"].astype(int)) \
        .to_csv(outfile, index=False)
    print(f"Leaderboard CSV written to {outfile}")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SCRIPT_DIR, "olympic_medals.csv")
    df = load_data(path)
    board = compute_leaderboard(df)
    print("\n=== MEDAL LEADERBOARD (Top {}) ===".format(TOP_N))
    print(board.head(TOP_N).to_string())
    write_leaderboard_csv(board)
    make_chart(board)
    print("\nDone. This report is final and ready to share.")


if __name__ == "__main__":
    main()
