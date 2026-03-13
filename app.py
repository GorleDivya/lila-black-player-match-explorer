import os
from functools import lru_cache
from typing import List, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from PIL import Image

import streamlit as st

from player_data_analysis import (
    MAP_CONFIGS,
    add_minimap_coordinates,
    add_player_type_columns,
    load_day,
)


@lru_cache(maxsize=None)
def get_available_days(data_root: str) -> List[str]:
    if not os.path.isdir(data_root):
        return []
    return sorted(
        name
        for name in os.listdir(data_root)
        if os.path.isdir(os.path.join(data_root, name))
        and name.startswith("February_")
    )


@lru_cache(maxsize=None)
def load_day_cached(data_root: str, day: str) -> pd.DataFrame:
    folder = os.path.join(data_root, day)
    df = load_day(folder, decode_events=True)
    add_player_type_columns(df)
    add_minimap_coordinates(df)
    return df


@lru_cache(maxsize=None)
def load_minimap_image(map_id: str) -> Optional[Image.Image]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    minimaps_dir = os.path.join(base_dir, "minimaps")
    filenames = {
        "AmbroseValley": "AmbroseValley_Minimap.png",
        "GrandRift": "GrandRift_Minimap.png",
        "Lockdown": "Lockdown_Minimap.jpg",
    }
    filename = filenames.get(map_id)
    if not filename:
        return None
    path = os.path.join(minimaps_dir, filename)
    if not os.path.isfile(path):
        return None
    return Image.open(path)


def make_minimap_figure(
    df: pd.DataFrame,
    map_id: str,
    show_heatmap: bool,
    show_paths: bool,
    show_events: bool,
) -> go.Figure:
    img = load_minimap_image(map_id)
    if img is None:
        # Fallback: just plot points without background
        fig = go.Figure()
        if show_paths:
            for player_type, color in [("human", "cyan"), ("bot", "orange")]:
                mask = df["player_type"] == player_type
                if mask.any():
                    fig.add_trace(
                        go.Scattergl(
                            x=df.loc[mask, "minimap_x"],
                            y=df.loc[mask, "minimap_y"],
                            mode="lines",
                            line=dict(color=color, width=1),
                            name=f"{player_type} path",
                        )
                    )

        if show_events and "event" in df.columns:
            event_markers = {
                "Kill": ("red", "x"),
                "Killed": ("red", "circle-open"),
                "BotKill": ("yellow", "x"),
                "BotKilled": ("yellow", "circle-open"),
                "KilledByStorm": ("purple", "triangle-up"),
                "Loot": ("green", "square"),
            }
            for event_name, (color, symbol) in event_markers.items():
                mask = df["event"] == event_name
                if mask.any():
                    fig.add_trace(
                        go.Scattergl(
                            x=df.loc[mask, "minimap_x"],
                            y=df.loc[mask, "minimap_y"],
                            mode="markers",
                            marker=dict(color=color, size=6, symbol=symbol),
                            name=event_name,
                        )
                    )

        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
            plot_bgcolor="black",
            paper_bgcolor="black",
        )
        fig.update_yaxes(autorange="reversed")
        return fig

    width, height = img.size
    fig = go.Figure()

    # Add background minimap image
    fig.add_layout_image(
        dict(
            source=img,
            xref="x",
            yref="y",
            x=0,
            y=0,
            sizex=width,
            sizey=height,
            sizing="stretch",
            layer="below",
        )
    )

    # Heatmap of movement / traffic
    if show_heatmap and len(df) > 0:
        heat = go.Histogram2dcontour(
            x=df["minimap_x"],
            y=df["minimap_y"],
            ncontours=20,
            colorscale="Hot",
            showscale=True,
            opacity=0.6,
            contours=dict(showlines=False),
            name="Traffic heatmap",
        )
        fig.add_trace(heat)

    # Player paths (lines)
    if show_paths and len(df) > 0:
        for player_type, color in [("human", "cyan"), ("bot", "orange")]:
            mask = df["player_type"] == player_type
            if mask.any():
                # For performance, sample positions for paths
                sampled = df.loc[mask].sort_values("ts").iloc[::5]
                fig.add_trace(
                    go.Scattergl(
                        x=sampled["minimap_x"],
                        y=sampled["minimap_y"],
                        mode="lines",
                        line=dict(color=color, width=1),
                        name=f"{player_type} path",
                    )
                )

    # Combat / loot / storm events
    if show_events and "event" in df.columns:
        event_markers = {
            "Kill": ("red", "x"),
            "Killed": ("red", "circle-open"),
            "BotKill": ("yellow", "x"),
            "BotKilled": ("yellow", "circle-open"),
            "KilledByStorm": ("purple", "triangle-up"),
            "Loot": ("green", "square"),
        }
        for event_name, (color, symbol) in event_markers.items():
            mask = df["event"] == event_name
            if mask.any():
                fig.add_trace(
                    go.Scattergl(
                        x=df.loc[mask, "minimap_x"],
                        y=df.loc[mask, "minimap_y"],
                        mode="markers",
                        marker=dict(color=color, size=8, symbol=symbol, line_width=1),
                        name=event_name,
                    )
                )

    fig.update_xaxes(range=[0, width], visible=False)
    fig.update_yaxes(range=[height, 0], visible=False, scaleanchor="x", scaleratio=1)
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(bgcolor="rgba(0,0,0,0.5)"),
        plot_bgcolor="black",
        paper_bgcolor="black",
    )
    return fig


def main():
    st.set_page_config(
        page_title="LILA BLACK - Match Explorer",
        layout="wide",
    )

    st.title("LILA BLACK - Player Match Explorer")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_root = os.environ.get("LILA_DATA_ROOT", base_dir)

    days = get_available_days(data_root)
    if not days:
        st.error(
            "No day folders found. Expected subfolders like 'February_10' under "
            f"{data_root}. Set the LILA_DATA_ROOT environment variable or place the "
            "dataset alongside this app."
        )
        return

    with st.sidebar:
        st.header("Filters")

        day = st.selectbox("Day", days, index=0)
        df_day = load_day_cached(data_root, day)

        maps = sorted(df_day["map_id"].dropna().unique().tolist())
        map_id = st.selectbox("Map", maps)

        df_map = df_day[df_day["map_id"] == map_id].copy()

        # Match filter
        match_ids = sorted(df_map["match_id"].dropna().unique().tolist())
        match_id = st.selectbox("Match", match_ids)
        df_match = df_map[df_map["match_id"] == match_id].copy()

        # Player type filter
        show_humans = st.checkbox("Show humans", value=True)
        show_bots = st.checkbox("Show bots", value=True)
        player_mask = np.full(len(df_match), False)
        if show_humans:
            player_mask |= df_match["player_type"] == "human"
        if show_bots:
            player_mask |= df_match["player_type"] == "bot"
        df_match = df_match[player_mask]

        # Event filters
        st.subheader("Events")
        show_events = st.checkbox("Show events (kills, loot, storm)", value=True)
        show_heatmap = st.checkbox("Show heatmap (traffic / deaths)", value=False)
        show_paths = st.checkbox("Show player paths", value=True)

        # Timeline slider (ts is per-match relative time)
        if "ts" in df_match.columns and not df_match["ts"].empty:
            # Some Streamlit versions do not accept pandas.Timestamp in sliders.
            # Use an integer slider in milliseconds relative to the match start.
            ts_series = pd.to_datetime(df_match["ts"], errors="coerce")
            ts_series = ts_series.dropna()
            if not ts_series.empty:
                ts_min = ts_series.min()
                ts_max = ts_series.max()
                ts0 = ts_min

                min_ms = 0
                max_ms = int((ts_max - ts0).total_seconds() * 1000)
                cutoff_ms = st.slider(
                    "Timeline (ms since match start)",
                    min_value=min_ms,
                    max_value=max_ms,
                    value=max_ms,
                    step=250,
                )
                cutoff_ts = ts0 + pd.Timedelta(milliseconds=int(cutoff_ms))
                df_match = df_match[pd.to_datetime(df_match["ts"], errors="coerce") <= cutoff_ts]

    # Main layout: minimap + stats
    col_map, col_stats = st.columns([3, 1])

    with col_map:
        st.subheader(f"Minimap - {map_id}")
        fig = make_minimap_figure(
            df=df_match,
            map_id=map_id,
            show_heatmap=show_heatmap,
            show_paths=show_paths,
            show_events=show_events,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_stats:
        st.subheader("Match Summary")
        total_players = df_match["user_id"].nunique()
        human_players = df_match.loc[df_match["player_type"] == "human", "user_id"].nunique()
        bot_players = df_match.loc[df_match["player_type"] == "bot", "user_id"].nunique()

        st.metric("Total players in match", total_players)
        st.metric("Humans", human_players)
        st.metric("Bots", bot_players)

        if "event" in df_match.columns:
            st.markdown("**Event counts**")
            counts = df_match["event"].value_counts()
            for name, count in counts.items():
                st.write(f"{name}: {count}")


if __name__ == "__main__":
    main()

