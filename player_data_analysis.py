import os
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import pyarrow.parquet as pq
import pandas as pd


@dataclass(frozen=True)
class MapConfig:
    """Configuration for converting world (x, z) coordinates to minimap pixels."""

    scale: float
    origin_x: float
    origin_z: float


MAP_CONFIGS: Dict[str, MapConfig] = {
    "AmbroseValley": MapConfig(scale=900, origin_x=-370, origin_z=-473),
    "GrandRift": MapConfig(scale=581, origin_x=-290, origin_z=-290),
    "Lockdown": MapConfig(scale=1000, origin_x=-500, origin_z=-500),
}


UUID_REGEX = re.compile(
    r"^[0-9a-fA-F]{8}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{12}$"
)


def is_uuid(value: str) -> bool:
    """Return True if the given string looks like a UUID (human player)."""
    if not isinstance(value, str):
        return False
    return bool(UUID_REGEX.match(value))


def classify_player_type(user_id: str) -> str:
    """
    Classify a player as 'human' or 'bot' based on user_id format.

    - Humans use UUID user_ids.
    - Bots use short numeric IDs.
    """
    if is_uuid(user_id):
        return "human"
    if isinstance(user_id, str) and user_id.isdigit():
        return "bot"
    # Fallback for any unexpected patterns
    return "unknown"


def decode_event_column(df: pd.DataFrame, column: str = "event") -> pd.DataFrame:
    """
    Decode the Parquet 'event' column from bytes to string, in-place.

    The README notes that 'event' is stored as bytes and should be decoded
    with UTF-8 to get values such as 'Position', 'Kill', etc.
    """
    if column not in df.columns:
        return df

    def _decode(x):
        if isinstance(x, bytes):
            return x.decode("utf-8")
        return x

    df[column] = df[column].apply(_decode)
    return df


def read_parquet_file(path: str, decode_events: bool = True) -> pd.DataFrame:
    """
    Read a single Parquet file into a pandas DataFrame.

    Parameters
    ----------
    path:
        Path to a `.nakama-0` file. Although there is no '.parquet' extension,
        the README confirms these are valid Apache Parquet files.
    decode_events:
        Whether to decode the 'event' column from bytes to string.
    """
    table = pq.read_table(path)
    df = table.to_pandas()
    if decode_events:
        decode_event_column(df, "event")
    return df


def load_day(folder: str, decode_events: bool = True) -> pd.DataFrame:
    """
    Load all player-journey Parquet files from a single day folder.

    This generalizes the 'load_day' example from the README and:
      - skips non-Parquet / corrupt files robustly
      - optionally decodes the 'event' column
    """
    frames: List[pd.DataFrame] = []
    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        if not os.path.isfile(filepath):
            continue
        try:
            df = read_parquet_file(filepath, decode_events=decode_events)
            frames.append(df)
        except Exception:
            # If any file cannot be read, skip it so that the rest of the data loads.
            continue

    if not frames:
        raise RuntimeError(f"No Parquet files could be loaded from folder: {folder}")

    return pd.concat(frames, ignore_index=True)


def load_days(
    base_dir: str,
    day_folders: Optional[Iterable[str]] = None,
    decode_events: bool = True,
) -> pd.DataFrame:
    """
    Load and combine multiple day folders (e.g., 'February_10', 'February_11').

    Parameters
    ----------
    base_dir:
        Directory containing the day folders.
    day_folders:
        Iterable of folder names to load. If None, will attempt to load all
        subdirectories whose names start with 'February_'.
    decode_events:
        Whether to decode the 'event' column from bytes to string.
    """
    if day_folders is None:
        # Auto-detect folders like 'February_10', 'February_11', etc.
        day_folders = sorted(
            name
            for name in os.listdir(base_dir)
            if os.path.isdir(os.path.join(base_dir, name))
            and name.startswith("February_")
        )

    frames: List[pd.DataFrame] = []
    for day in day_folders:
        day_path = os.path.join(base_dir, day)
        if not os.path.isdir(day_path):
            continue
        df_day = load_day(day_path, decode_events=decode_events)
        df_day["day_folder"] = day
        frames.append(df_day)

    if not frames:
        raise RuntimeError(f"No day folders could be loaded from base_dir: {base_dir}")

    return pd.concat(frames, ignore_index=True)


def add_player_type_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add 'player_type' and 'is_bot' columns derived from 'user_id'.

    Based on the README:
      - humans use UUID user_ids
      - bots use numeric user_ids
    """
    if "user_id" not in df.columns:
        return df

    df["player_type"] = df["user_id"].astype(str).apply(classify_player_type)
    df["is_bot"] = df["player_type"] == "bot"
    return df


def world_to_minimap(
    x: float,
    z: float,
    map_id: str,
) -> Tuple[float, float]:
    """
    Convert world (x, z) coordinates to minimap (pixel_x, pixel_y) coordinates.

    Implements the exact conversion described in the README:

        Step 1: Convert world coords to UV (0-1 range)
            u = (x - origin_x) / scale
            v = (z - origin_z) / scale

        Step 2: Convert UV to pixel coords (1024x1024 image)
            pixel_x = u * 1024
            pixel_y = (1 - v) * 1024    # Y is flipped; image origin is top-left
    """
    if map_id not in MAP_CONFIGS:
        raise ValueError(f"Unknown map_id '{map_id}'. Expected one of {list(MAP_CONFIGS)}.")

    cfg = MAP_CONFIGS[map_id]
    u = (x - cfg.origin_x) / cfg.scale
    v = (z - cfg.origin_z) / cfg.scale

    pixel_x = u * 1024.0
    pixel_y = (1.0 - v) * 1024.0
    return pixel_x, pixel_y


def add_minimap_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add 'minimap_x' and 'minimap_y' columns for rows with a known 'map_id'.

    Uses the world_to_minimap() function and the map configuration from the README.
    """
    required_cols = {"x", "z", "map_id"}
    if not required_cols.issubset(df.columns):
        return df

    def _compute(row):
        try:
            return world_to_minimap(row["x"], row["z"], row["map_id"])
        except Exception:
            return (float("nan"), float("nan"))

    minimap_coords = df.apply(_compute, axis=1, result_type="expand")
    minimap_coords.columns = ["minimap_x", "minimap_y"]
    df[["minimap_x", "minimap_y"]] = minimap_coords
    return df


def summarize_basic_stats(df: pd.DataFrame) -> Dict[str, object]:
    """
    Produce a few quick summary statistics similar to the README's quick stats.

    Returns a dictionary with:
      - 'unique_players'
      - 'unique_matches'
      - 'maps'
      - 'event_counts'
    """
    stats: Dict[str, object] = {}
    if "user_id" in df.columns:
        stats["unique_players"] = df["user_id"].nunique()
    if "match_id" in df.columns:
        stats["unique_matches"] = df["match_id"].nunique()
    if "map_id" in df.columns:
        stats["maps"] = sorted(df["map_id"].dropna().unique().tolist())
    if "event" in df.columns:
        stats["event_counts"] = df["event"].value_counts().to_dict()
    return stats


if __name__ == "__main__":
    """
    Example usage:

    Run this script from the root of the dataset (the folder that contains
    'February_10', 'February_11', ... and 'README.md'):

        python player_data_analysis.py
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Load one day (February 10) as a quick-start example.
    feb10_folder = os.path.join(base_dir, "February_10")
    if os.path.isdir(feb10_folder):
        df_feb10 = load_day(feb10_folder, decode_events=True)
        add_player_type_columns(df_feb10)
        add_minimap_coordinates(df_feb10)
        stats = summarize_basic_stats(df_feb10)

        print("Loaded February_10 data")
        print(f"Rows: {len(df_feb10)}")
        print(f"Unique players: {stats.get('unique_players')}")
        print(f"Unique matches: {stats.get('unique_matches')}")
        print("Maps:", stats.get("maps"))
        print("Event counts (top 10):")
        if "event_counts" in stats:
            for event, count in list(stats["event_counts"].items())[:10]:
                print(f"  {event}: {count}")
    else:
        print(
            "Could not find 'February_10' folder next to this script. "
            "Please run from the dataset root."
        )

