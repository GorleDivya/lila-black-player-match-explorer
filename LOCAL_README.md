## LILA BLACK – Player Match Explorer

This repo contains a small web tool for exploring **LILA BLACK** player match data and minimaps.

The tool is built with **Python + Streamlit** and is designed to be easy to run locally and deploy to a platform like Streamlit Cloud, Railway, or similar.

### Tech Stack

- Python 3
- Streamlit (web UI)
- pandas + pyarrow (Parquet data loading)
- Plotly (interactive minimap visualizations)
- Pillow (loading minimap images)

### Running Locally

1. **Install dependencies**

   From the repo root (the folder that contains this file, `app.py`, and the `February_XX` folders):

   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure data is present**

   The app expects the dataset layout described in the original `README.md`:

   - Day folders: `February_10`, `February_11`, `February_12`, `February_13`, `February_14`
   - Minimap images in `minimaps/`

   By default, the app looks for these folders **next to `app.py`**.  
   You can override this by setting an environment variable:

   - `LILA_DATA_ROOT` – path to the folder that contains the `February_XX` day folders.

3. **Run the app**

   From the repo root:

   ```bash
   streamlit run app.py
   ```

   Streamlit will print a local URL (by default `http://localhost:8501`) that you can open in your browser.

### Key Features

- **Minimap Visualization**
  - Renders player movement paths directly on the map minimap.
  - Uses the world-to-minimap coordinate mapping described in the dataset README.

- **Humans vs Bots**
  - Detects humans vs bots by `user_id` format (UUID vs numeric).
  - Colors paths differently for humans and bots.

- **Events**
  - Marks `Kill`, `Killed`, `BotKill`, `BotKilled`, `Loot`, and `KilledByStorm` events with distinct shapes and colors.

- **Filtering**
  - Filter by **day**, **map**, and **match**.
  - Toggle humans vs bots, event markers, paths, and heatmap layers.

- **Timeline Playback**
  - A timeline slider filters events and movement by match-relative timestamp, approximating match playback.

- **Heatmaps**
  - Optional traffic heatmap layer showing where movement is densest.

### Documentation

- `ARCHITECTURE.md` – overview of the tech choices, data flow, and coordinate mapping approach.
- `INSIGHTS.md` – example insights and how a Level Designer might act on them.

