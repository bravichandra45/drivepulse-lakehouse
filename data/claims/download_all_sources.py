#!/usr/bin/env python3
"""
download_all_sources.py (Claims domain) — fetch the 5 claim sources into this folder.
    pip install requests
    python download_all_sources.py          # 4 small/medium files
    python download_all_sources.py --big      # also NHTSA complaints (~366MB)
No logins required.
"""
import argparse, os, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))

FILES = [
    ("insurance_claims.csv",
     "https://data.mendeley.com/public-files/datasets/992mh7dk9y/files/a39df307-4896-4bb7-a4b8-f7d7fcdefed1/file_downloaded"),
    ("carclaims.csv",
     "https://raw.githubusercontent.com/Rashmi-77/Vehicle-Insurance-Fraud-Detection/main/carclaims.csv"),
    ("sample_type_claim.csv",
     "https://data.mendeley.com/public-files/datasets/5cxyb5fp4f/files/f06af09a-39fa-41e2-9ac1-31a70535531e/file_downloaded"),
    ("freMTPL2sev.arff", "https://openml.org/data/v1/download/20649149/freMTPL2sev.arff"),
]
BIG = [("FLAT_CMPL.zip", "https://static.nhtsa.gov/odi/ffdd/cmpl/FLAT_CMPL.zip")]

def fetch(name, url):
    dst = os.path.join(HERE, name)
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        print(f"  ✓ {name}"); return
    print(f"  → {name} ...", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r, open(dst, "wb") as f:
        f.write(r.read())
    print(f"    done ({os.path.getsize(dst):,} bytes)")

if __name__ == "__main__":
    a = argparse.ArgumentParser(); a.add_argument("--big", action="store_true")
    big = a.parse_args().big
    for n, u in FILES + (BIG if big else []):
        try: fetch(n, u)
        except Exception as e: print(f"    !! {n}: {e}")
    print("\nfreMTPL2sev is ARFF -> `pip install liac-arff`, convert to CSV in silver.")
