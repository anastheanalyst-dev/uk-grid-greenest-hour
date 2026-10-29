"""Step 2: answer the question "When is the UK grid greenest?" and draw the charts.

Reads data/*.csv (from step 1), prints the findings and saves charts in charts/.
Run:  python 02_analyse.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).parent
CHARTS = HERE / "charts"
CHARTS.mkdir(exist_ok=True)
GREY, RED, GREEN, INK = "#C9C3B4", "#C8312A", "#2F8F3A", "#161514"

# 1 · load, and turn UTC into UK time (clocks went back on 25 Oct, so we can't just add an hour)
ci = pd.read_csv(HERE / "data/intensity.csv", parse_dates=["from"])
gen = pd.read_csv(HERE / "data/generation.csv", parse_dates=["from"])
df = ci.merge(gen, on="from")
df["uk_time"] = df["from"].dt.tz_convert("Europe/London")
df["hour"] = df["uk_time"].dt.hour
df["date"] = df["uk_time"].dt.date
df["weekday"] = df["uk_time"].dt.day_name()
df["co2"] = df["actual"].fillna(df["forecast"])          # a few half-hours have no "actual" yet, so use the forecast

# 2 · the average grid, hour by hour
by_hour = df.groupby("hour")["co2"].mean()
green_h, dirty_h = by_hour.idxmin(), by_hour.idxmax()
gap = by_hour.max() / by_hour.min()

# 3 · day to day, and what drives it
by_day = df.groupby("date").agg(co2=("co2", "mean"), wind=("wind", "mean"), gas=("gas", "mean"))
green_d, dirty_d = by_day["co2"].idxmin(), by_day["co2"].idxmax()
wind_corr = df["co2"].corr(df["wind"])
weekend = df[df["weekday"].isin(["Saturday", "Sunday"])]["co2"].mean()
weekday = df[~df["weekday"].isin(["Saturday", "Sunday"])]["co2"].mean()

print(f"Period: {df['date'].min()} to {df['date'].max()} ({len(df)} half-hours)")
print(f"Average: {df['co2'].mean():.0f} gCO2/kWh")
print(f"Greenest hour (UK time): {green_h:02d}:00, avg {by_hour.min():.0f}")
print(f"Dirtiest hour (UK time): {dirty_h:02d}:00, avg {by_hour.max():.0f}  ({gap:.1f}x the greenest)")
print(f"Greenest day: {green_d} at {by_day.loc[green_d, 'co2']:.0f} (wind {by_day.loc[green_d, 'wind']:.0f}%)")
print(f"Dirtiest day: {dirty_d} at {by_day.loc[dirty_d, 'co2']:.0f} (wind {by_day.loc[dirty_d, 'wind']:.0f}%)")
print(f"Day gap: {by_day['co2'].max() / by_day['co2'].min():.1f}x")
print(f"Correlation with wind share: {wind_corr:.2f}")
print(f"Weekend avg {weekend:.0f} vs weekday avg {weekday:.0f}")


# 4 · charts: grey everything, colour ONE thing, and make the title the answer
def style(ax, title, sub):
    ax.set_title(title, loc="left", fontsize=15, fontweight="bold", color=INK, pad=24)
    ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=10, color="#6E6A62")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors="#6E6A62")


fig, ax = plt.subplots(figsize=(10, 5.2))
colors = [GREEN if h == green_h else RED if h == dirty_h else GREY for h in by_hour.index]
ax.bar(by_hour.index, by_hour.values, color=colors)
ax.set_xticks(range(0, 24, 2), [f"{h:02d}:00" for h in range(0, 24, 2)])
ax.set_ylabel("gCO2 per kWh")
style(ax, f"The UK grid is cleanest at {green_h:02d}:00 and dirtiest at {dirty_h:02d}:00",
      f"Average carbon intensity by hour (UK time), {df['date'].min():%d %b} to {df['date'].max():%d %b %Y} · source: NESO Carbon Intensity API")
fig.tight_layout()
fig.savefig(CHARTS / "01_by_hour.png", dpi=160)

fig, ax = plt.subplots(figsize=(10, 5.2))
colors = [GREEN if d == green_d else RED if d == dirty_d else GREY for d in by_day.index]
ax.bar(range(len(by_day)), by_day["co2"], color=colors)
ax.set_xticks(range(0, len(by_day), 5), [f"{d:%d %b}" for d in by_day.index[::5]])
ax.set_ylabel("gCO2 per kWh")
style(ax, f"The day matters more than the hour: {by_day['co2'].max() / by_day['co2'].min():.1f}x gap between days",
      "Daily average carbon intensity. Green = cleanest day, red = dirtiest day")
fig.tight_layout()
fig.savefig(CHARTS / "02_by_day.png", dpi=160)

fig, ax = plt.subplots(figsize=(10, 5.2))
ax.scatter(df["wind"], df["co2"], s=8, color=GREY, alpha=0.6)
ax.scatter(by_day["wind"], by_day["co2"], s=40, color=GREEN, label="daily average")
ax.set_xlabel("Share of electricity from wind (%)")
ax.set_ylabel("gCO2 per kWh")
ax.legend(frameon=False)
style(ax, f"More wind, cleaner grid (correlation {wind_corr:.2f})", "Each grey dot is one half-hour")
fig.tight_layout()
fig.savefig(CHARTS / "03_wind.png", dpi=160)
print(f"charts saved to {CHARTS}")
