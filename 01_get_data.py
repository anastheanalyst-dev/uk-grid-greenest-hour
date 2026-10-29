"""Step 1: download 30 days of public UK electricity data from the Carbon Intensity API (no key needed).

Saves two CSV files in data/:
  intensity.csv   half-hourly carbon intensity (gCO2/kWh), forecast + actual
  generation.csv  half-hourly generation mix (% from wind, gas, solar, nuclear, ...)

Run:  python 01_get_data.py
Data: National Energy System Operator (NESO) Carbon Intensity API, https://carbonintensity.org.uk (CC BY 4.0)
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import csv
import time

import requests

API = "https://api.carbonintensity.org.uk"
END = datetime(2026, 10, 28, tzinfo=timezone.utc)     # change these two lines to study any period
DAYS = 30
OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)


def fetch(endpoint, start, stop):
    """The API returns at most 14 days per call, so we ask for one week at a time."""
    url = f"{API}/{endpoint}/{start:%Y-%m-%dT%H:%MZ}/{stop:%Y-%m-%dT%H:%MZ}"
    r = requests.get(url, headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()["data"]


intensity, generation = [], []
start = END - timedelta(days=DAYS)
while start < END:
    stop = min(start + timedelta(days=7), END)
    for row in fetch("intensity", start, stop):
        intensity.append({"from": row["from"], "forecast": row["intensity"]["forecast"], "actual": row["intensity"]["actual"]})
    for row in fetch("generation", start, stop):
        mix = {g["fuel"]: g["perc"] for g in row["generationmix"]}
        generation.append({"from": row["from"], **mix})
    print(f"got {start:%d %b} to {stop:%d %b}")
    start = stop
    time.sleep(0.5)                                      # be polite to a free API


def save(rows, name):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(OUT / name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows({r["from"]: r for r in rows}.values())   # drop the overlapping half-hour between weeks


save(intensity, "intensity.csv")
save(generation, "generation.csv")
print(f"saved {len(intensity)} intensity rows and {len(generation)} generation rows to {OUT}")
