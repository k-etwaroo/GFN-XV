import os
from pathlib import Path

import pandas as pd


def backfill_scores_from_combined(
    combined_path: str = "data/combined/all_scores.csv",
    data_dir: str = "data",
    overwrite: bool = False,
) -> None:
    """Split data/combined/all_scores.csv into per-season scores_YYYY.csv files.

    This is the easiest way to expose older seasons (e.g. 2011–2016) to the
    Streamlit app, as all of the pages look for files matching
    data/scores_<season>.csv via seasons_available("data").

    Parameters
    ----------
    combined_path:
        Path to the combined scores CSV (default: data/combined/all_scores.csv).
    data_dir:
        Directory where scores_YYYY.csv files should live (default: data).
    overwrite:
        If True, existing scores_YYYY.csv files will be overwritten.
        If False, existing files are left untouched.
    """

    combined_file = Path(combined_path)
    if not combined_file.exists():
        raise FileNotFoundError(f"Combined scores file not found: {combined_file}")

    df = pd.read_csv(combined_file)
    if "season" not in df.columns:
        raise ValueError(
            "Combined scores file must contain a 'season' column to split by."
        )

    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)

    seasons = sorted(df["season"].dropna().unique().tolist())
    print(f"Found seasons in combined scores: {seasons}")

    for season in seasons:
        season_df = df[df["season"] == season].copy()
        if season_df.empty:
            continue

        out_path = data_path / f"scores_{int(season)}.csv"
        if out_path.exists() and not overwrite:
            print(f"Skipping {out_path} (exists, overwrite=False)")
            continue

        season_df.to_csv(out_path, index=False)
        print(f"Wrote {len(season_df)} rows → {out_path}")


if __name__ == "__main__":
    # Basic CLI usage
    backfill_scores_from_combined()