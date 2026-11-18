"""Download the real indicator series used by the project (Our World in Data CSV endpoint).

Immunisation series are WHO/UNICEF WUENIC estimates; context series come from the World Bank,
UN and WHO via the same source. Raw files are saved to data/raw/ so the app never needs the network.
Run:  python src/fetch_data.py
"""
import os
import requests

BASE = "https://ourworldindata.org/grapher/{slug}.csv?v=1&csvType=full&useColumnShortNames=true"

SERIES = {
    "dtp3": "share-of-children-immunized-dtp3",
    "mcv1": "share-of-children-vaccinated-against-measles",
    "child_mortality": "child-mortality-rate",
    "gdp_pc": "gdp-per-capita-worldbank",
    "physicians": "physicians-per-1000-people",
    "health_spend": "public-health-expenditure-share-gdp",
    "skilled_birth": "births-attended-by-health-staff-sdgs",
    "fertility": "total-fertility-rate",
    "population": "urban-and-rural-population",
}


def fetch_all(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for name, slug in SERIES.items():
        for attempt in range(4):  # a proxy on some networks breaks TLS now and then
            try:
                r = requests.get(BASE.format(slug=slug), timeout=120)
                r.raise_for_status()
                break
            except requests.RequestException:
                if attempt == 3:
                    raise
        path = os.path.join(out_dir, f"{name}.csv")
        with open(path, "wb") as f:
            f.write(r.content)
        print(f"saved {path} ({len(r.content) // 1024} KB)")


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fetch_all(os.path.join(root, "data", "raw"))
