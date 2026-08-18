"""Seed local demo data and start the SmartReco development server.

Usage:
    python run.py

For a server-only start, use:
    python -m uvicorn src.main:app --reload
"""

import uvicorn

from seed import main as seed_catalog
from seed_demo import main as seed_demo


if __name__ == "__main__":
    seed_catalog()
    seed_demo()
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=False)
