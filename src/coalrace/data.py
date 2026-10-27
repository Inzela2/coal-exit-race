"""Load Our World in Data's energy dataset, pinned to a commit for reproducibility."""
from pathlib import Path
import urllib.request
import pandas as pd

COMMIT = "f8de88a4f6f9cab44f1cf606047cbd6c4414042c"
SOURCE_URL = f"https://raw.githubusercontent.com/owid/energy-data/{COMMIT}/owid-energy-data.csv"
DEFAULT_PATH = Path("data/owid-energy-data.csv")
FOSSIL = ["coal", "gas", "oil"]
CLEAN = ["nuclear", "hydro", "wind", "solar", "biofuel"]
SOURCES = FOSSIL + CLEAN


def download(path: Path = DEFAULT_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        urllib.request.urlretrieve(SOURCE_URL, path)
    return path


def load(path: Path = DEFAULT_PATH) -> pd.DataFrame:
    """Country-year rows only. OWID mixes in regional aggregates (World, Europe,
    'High-income countries') whose iso codes are blank or start with OWID; keeping
    them would double count."""
    cols = (["country", "year", "iso_code", "electricity_generation", "carbon_intensity_elec"]
            + [f"{s}_share_elec" for s in SOURCES])
    df = pd.read_csv(path, usecols=cols)
    is_country = df["iso_code"].notna() & ~df["iso_code"].str.startswith("OWID", na=False)
    return df[is_country].reset_index(drop=True)
