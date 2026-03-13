# LILA BLACK – Player Match Explorer Architecture

## Tech Stack

- **Backend & Data Processing**: Python 3 with `pandas` and `pyarrow` for loading and shaping Apache Parquet data (the `.nakama-0` files).
- **Web UI**: Streamlit – lightweight Python framework that lets us build an interactive browser app without a separate backend service layer.
- **Visualization**: Plotly for interactive, layered plots (paths, events, heatmaps) on top of the minimap images.
- **Imaging**: Pillow to load the 1024×1024 minimap images.

This stack keeps everything in Python, which matches the sample code in the dataset README and makes local development and cloud hosting (e.g. Streamlit Cloud, Railway) straightforward.

## Data Flow

1. **Raw Data (disk)**  
   - Source: folders like `February_10`, `February_11`, … containing `.nakama-0` Parquet files.  
   - Minimap images in `minimaps/` (`AmbroseValley_Minimap.png`, `GrandRift_Minimap.png`, `Lockdown_Minimap.jpg`).

2. **Loading & Enrichment (`player_data_analysis.py`)**  
   - `load_day(folder)` reads all Parquet files for a day using `pyarrow.parquet.read_table`, converts them to `pandas` DataFrames, and decodes the `event` column from bytes to UTF‑8 strings.
   - `add_player_type_columns(df)` inspects `user_id`:
     - UUID → **human**
     - Numeric string → **bot**
   - `add_minimap_coordinates(df)` converts `(x, z, map_id)` to `(minimap_x, minimap_y)` pixel coordinates using the mapping described in the README.

3. **App Layer (`app.py`)**  
   - On startup, Streamlit discovers available day folders under `LILA_DATA_ROOT` (defaults to the app directory).
   - When the user selects **day / map / match / filters** in the sidebar:
     - The app calls `load_day(day)` (cached) → filters by `map_id` and `match_id`.
     - Applies player-type filters, event toggles, and timeline (filters by `ts <= selected_time`).

4. **Visualization (browser)**  
   - The app loads the appropriate minimap image and creates a Plotly figure:
     - Background: minimap image.
     - **Paths**: line traces for humans vs bots (different colors).
     - **Events**: marker traces with color/shape per event type (Kill, Killed, BotKill, BotKilled, Loot, KilledByStorm).
     - **Heatmap**: optional 2D contour density of positions for “traffic / kill / death zones”.
   - Streamlit embeds the Plotly figure and the summary stats (player counts, event counts) in the page.

## Coordinate Mapping to Minimaps

For each map, the README gives:

- `scale`
- `origin_x` and `origin_z`
- The fact that minimap images are **1024×1024** pixels and Y is flipped (image origin is top‑left).

We use `MAP_CONFIGS` in `player_data_analysis.py`:

- Ambrose Valley: `scale=900`, `origin=(-370, -473)`
- Grand Rift: `scale=581`, `origin=(-290, -290)`
- Lockdown: `scale=1000`, `origin=(-500, -500)`

For each row:

1. Compute UV coordinates in \[0, 1]:
   - \(u = (x - origin_x) / scale\)
   - \(v = (z - origin_z) / scale\)
2. Convert to pixel coordinates (1024×1024):
   - \(pixel\_x = u * 1024\)
   - \(pixel\_y = (1 - v) * 1024\) (flip Y for image space)

These formulas are exactly those in the README. The resulting `minimap_x`, `minimap_y` are used to plot paths and events directly over the minimap images.

## Assumptions & Trade‑offs

- **Assumptions**
  - The dataset is available on disk in the same structure as described in the README (day folders + `minimaps/` next to the app).
  - `ts` can be treated as an increasing **match-relative timestamp** and filtered with a cutoff to approximate timeline playback.
  - All minimap images are square 1024×1024; if that changes, only the mapping constants need updating.

- **Key Trade‑offs**

| Area                 | Choice                                  | Alternatives                       | Rationale |
|----------------------|-----------------------------------------|------------------------------------|-----------|
| Web framework        | Streamlit                               | React + FastAPI, Flask, etc.      | Faster to ship an interactive, data-heavy internal tool; no need for a separate API layer. |
| Visualization        | Plotly                                  | Matplotlib, Bokeh, raw Canvas      | Strong support for layered graphics, heatmaps, and interactivity in-browser. |
| Data access          | On-disk Parquet via `pyarrow`           | Pre-ingested DB / DuckDB / Spark   | The dataset is modest in size; direct Parquet reads keep setup simpler. |
| Timeline playback    | Slider-based filtering on `ts`          | Full animation / video playback    | Slider satisfies the “timeline or playback” requirement without complex client state or performance issues. |

