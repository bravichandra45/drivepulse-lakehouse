"""Download the public DrivePulse datasets into ./data (gitignored).
TODO(claude-code): implement per-source downloaders. See docs/datasets.md for URLs.

Sources:
  telematics : Vehicle Energy Dataset (VED) + Extended VED  -> data/telematics/
  policy     : Porto Seguro Safe Driver (Kaggle)            -> data/policy/
  claims     : Allstate Claims Severity (Kaggle)            -> data/claims/
  vehicle    : NHTSA vPIC DB + Recalls API                  -> data/vehicle/
  safety     : NHTSA FARS, ODI complaints                   -> data/safety/
  docs       : NHTSA recall letters, DOI policy forms (PDF) -> data/docs/

Kaggle sources need KAGGLE_USERNAME / KAGGLE_KEY (see .env.example).
Volume floor: >= 50k records per domain.
"""

if __name__ == "__main__":
    raise SystemExit("Not implemented yet — let Claude Code fill this in per docs/datasets.md")
