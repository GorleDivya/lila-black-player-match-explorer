# LILA BLACK – Sample Insights

> Note: These are example insights you can refine after exploring the full dataset with the tool. They illustrate the kind of patterns the app is designed to surface for a Level Designer.

## 1. High-Traffic Choke Points on Ambrose Valley

- **What caught my eye**  
  Using the **traffic heatmap** on Ambrose Valley, one corridor between mid-map and the primary extraction zones consistently shows very high movement density, especially in the mid-to-late match window.

- **Evidence from the data**  
  - Heatmaps of `minimap_x`, `minimap_y` for Ambrose Valley across several days show a bright “band” of traffic.  
  - Filtering to humans only still preserves this band, indicating it is not just bot pathing.  
  - Overlaying kills and deaths on that heatmap reveals a cluster of combat events in the same region.

- **Why it matters / possible actions**  
  - This corridor functions as an unintended choke point.  
  - A Level Designer might:
    - Add alternative flanking routes or cover to reduce predictable sightlines.
    - Adjust loot density away from this corridor to spread players out.  
  - **Metrics to watch**: average survival time when entering this corridor, kill/death ratio by region, match completion (extraction) rates when players avoid vs. pass through it.

## 2. Bot Density vs. Human Engagement on Grand Rift

- **What caught my eye**  
  On Grand Rift, when filtering the minimap to **bots only**, the paths form strong, repeated patterns around certain POIs, but human paths intersect these routes only occasionally.

- **Evidence from the data**  
  - Color-coding humans vs bots shows that many bot patrol loops are not heavily intersected by human routes.  
  - Event markers show a relatively low number of `BotKill` / `BotKilled` events in these regions despite high bot presence.

- **Why it matters / possible actions**  
  - Some bot patrol paths may be “wasted” from a player experience perspective, generating little meaningful interaction.  
  - A Level Designer or systems designer could:
    - Re-route bots closer to high-traffic human paths or extraction routes.
    - Place objectives or higher-tier loot closer to bot-heavy regions to draw players into those spaces.  
  - **Metrics to watch**: number of human–bot encounters per match, time spent near bot-heavy areas, and distribution of BotKill / BotKilled events over time.

## 3. Storm Death Clusters Near Late-Game Extractions

- **What caught my eye**  
  When toggling on `KilledByStorm` and using the timeline slider toward the **late match phase**, certain maps show clusters of storm deaths near extraction zones rather than out in the open field.

- **Evidence from the data**  
  - Filtering events to `KilledByStorm` and sliding the timeline toward the end of matches increases the density of purple markers (`KilledByStorm`) near specific exits.  
  - Many of these deaths occur along common approach paths to extraction and overlap with high-traffic heatmap areas.

- **Why it matters / possible actions**  
  - Players may be underestimating storm speed or getting bottlenecked while trying to reach extraction, leading to “unfair-feeling” deaths at the finish line.  
  - A Level Designer could:
    - Slightly adjust extraction positions or approach routes to reduce path length in storm-heavy directions.
    - Improve environmental signaling (lighting, landmarks) to clarify safe routes as the storm advances.  
  - **Metrics to watch**: rate of `KilledByStorm` deaths near extractions vs mid-map, extraction success rates over time, and changes in average storm-distance when players initiate their final push.

