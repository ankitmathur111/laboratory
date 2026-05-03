"""Statistics manager – converts session analysis entries into a clean DataFrame."""

import pandas as pd
import re


def _parse_runs(runs_str) -> int:
    """Try to extract an integer from the runs_scored string."""
    if isinstance(runs_str, int):
        return runs_str
    if isinstance(runs_str, str):
        match = re.search(r"\d+", runs_str)
        if match:
            return int(match.group())
    return 0


class StatsManager:
    def __init__(self, analyses: list):
        self.analyses = analyses

    def to_dataframe(self) -> pd.DataFrame:
        if not self.analyses:
            return pd.DataFrame()

        df = pd.DataFrame(self.analyses)

        # Create numeric runs column for aggregation
        if "runs_scored" in df.columns:
            df["runs_scored_num"] = df["runs_scored"].apply(_parse_runs)

        # Clean up column names for display
        rename_map = {
            "shot_type": "shot_type",
            "ball_type": "ball_type",
            "pitch_length": "pitch_length",
            "ball_speed": "ball_speed",
            "runs_scored": "runs_scored",
            "shot_direction": "shot_direction",
            "outcome": "outcome",
            "batting_stance": "batting_stance",
        }
        return df

    def shot_distribution(self) -> dict:
        df = self.to_dataframe()
        if "shot_type" not in df.columns:
            return {}
        return df["shot_type"].value_counts().to_dict()

    def runs_by_direction(self) -> dict:
        df = self.to_dataframe()
        if "shot_direction" not in df.columns or "runs_scored_num" not in df.columns:
            return {}
        return df.groupby("shot_direction")["runs_scored_num"].sum().to_dict()

    def delivery_breakdown(self) -> dict:
        df = self.to_dataframe()
        if "ball_type" not in df.columns:
            return {}
        return df["ball_type"].value_counts().to_dict()
