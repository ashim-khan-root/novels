"""Download reference Urdu novels for analysis."""
import os
import re
import json
import urllib.request
import urllib.parse
import shutil
from pathlib import Path

BASE = Path(__file__).parent / "Novels" / "References"
BASE.mkdir(parents=True, exist_ok=True)

NOVELS = [
    {
        "name": "Sulphite",
        "author": "Noor Rajpoot",
        "url": "https://drive.google.com/uc?export=download&id=1Fv-D0ssmRXUYLcBMW0CfATEF3eby_Rpd",
        "file": "Sulphite_Noor_Rajpoot.pdf"
    },
    {
        "name": "Peer-e-Kamil",
        "author": "Umera Ahmed",
        "url": "https://drive.google.com/uc?export=download&id=1e9qJdM35pQaTDkSAuSLmsDQJFKR2cZ92",
        "file": "Peer_e_Kamil_Umera_Ahmed.pdf"
    },
    {
        "name": "Jannat-Kay-Pattay",
        "author": "Nimra Ahmed",
        "url": "https://drive.google.com/uc?export=download&id=1ddowUVp0AQDyZhT2RC7Z1nTKZ7FPen0z",
        "file": "Jannat_Kay_Pattay_Nimra_Ahmed.pdf"
    },
    {
        "name": "Haalim",
        "author": "Nimra Ahmed",
        "url": "https://drive.google.com/uc?export=download&id=1R3SLTqwQisfErs4QUjNSZQoGBJ-0e7tv",
        "file": "Haalim_Nimra_Ahmed.pdf"
    },
    {
        "name": "Mushaf",
        "author": "Nimra Ahmed",
        "url": "https://drive.google.com/uc?export=download&id=1MVQG3vQD9hjCeO4iyb5ST59P5REww4bW",
        "file": "Mushaf_Nimra_Ahmed.pdf"
    },
    {
        "name": "Alif",
        "author": "Umera Ahmed",
        "url": "https://drive.google.com/uc?export=download&id=1DTyPYlMUfCwzjoHuay4G5BAJUv9GKu_F",
        "file": "Alif_Umera_Ahmed.pdf"
    },
    {
        "name": "Mala",
        "author": "Nimra Ahmed",
        "url": "https://drive.google.com/uc?export=download&id=13ACOflxwAMNV-sSVSvrY6RKe9F7EiA8I",
        "file": "Mala_Nimra_Ahmed.pdf"
    },
    {
        "name": "Ishq-Aatish",
        "author": "Sadia Rajpoot",
        "url": "https://drive.google.com/uc?export=download&id=1SrPjX8bRied-E2XQiBkqluvgPYvFhi6G",
        "file": "Ishq_Aatish_Sadia_Rajpoot.pdf"
    },
]

def download_file(url, dest):
    """Download a file from a direct URL."""
    print(f"  Downloading {dest.name}...")
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=120) as resp:
            with open(dest, 'wb') as f:
                shutil.copyfileobj(resp, f)
        size = dest.stat().st_size
        print(f"    OK — {size / 1024 / 1024:.1f} MB")
        return True
    except Exception as e:
        print(f"    FAILED — {e}")
        return False

def main():
    for novel in NOVELS:
        folder = BASE / novel["name"]
        folder.mkdir(exist_ok=True)
        pdf_path = folder / novel["file"]
        
        if pdf_path.exists() and pdf_path.stat().st_size > 100000:
            print(f"[SKIP] {novel['name']} — already exists ({pdf_path.stat().st_size / 1024 / 1024:.1f} MB)")
        else:
            print(f"[DL] {novel['name']} by {novel['author']}")
            download_file(novel["url"], pdf_path)

    print("\nDone downloading novels.")

if __name__ == "__main__":
    main()
