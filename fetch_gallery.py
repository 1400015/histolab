"""Fetch reference gallery images from Wikimedia Commons (final).

Pinned list of verified real H&E micrographs, with per-item fallback
search terms. Candidates are validated as genuine histology micrographs.
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from gallery_source import GALLERY  # noqa: E402

ROOT = Path(__file__).parent
IMAGES_DIR = ROOT / "static" / "gallery"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
META_PATH = ROOT / "gallery_meta.json"

UA = {"User-Agent": "HistolabEdu/1.0 (educational histology app; sandbox)"}
API = "https://commons.wikimedia.org/w/api.php"

# Pinned verified Commons files per gallery entry (in priority order)
PINNED = {
    "colon_adenocarcinoma": [
        "Mucinous adenocarcinoma of the colon, HE 1.JPG",
        "Mucinous adenocarcinoma of the colon, HE 2.JPG",
    ],
    "stratified_squamous": [
        "A classic view of non-keratinized stratified squamous epithelium.jpg",
    ],
    "transitional_epithelium": [
        "A high-magnification microscope image of the urinary bladder wall, clearly showing the thick, multi-layered transitional epithelium with its characteristic dome-shaped surface cells, all resting on top of dense layers of smooth muscle.jpg",
        "Trasversal histologic section of human esophagus.jpg",
        "Human Esophagus, CS Lower Region Connecticut Valley Southampton, Mass. USA c.jpg",
    ],
    "connective_loose": [
        "Granulation tissue in an infected wound, HE 1.JPG",
    ],
    "dense_connective": [
        "Dense regular3.jpg",
        "Dense regular2.jpg",
        "Dense regular1.jpg",
    ],
    "smooth_muscle": [
        "Muscle Tissue Cardiac Muscle (27187637567).jpg",
        "A high-magnification microscope image of a cross section of smooth muscle.jpg",
    ],
    "skeletal_muscle": [
        "Skeletal muscle (FNA 2a- high mag).jpg",
        "0319 Multinucleate Muscle Tissue Micrograph.jpg",
    ],
    "cardiac_muscle": [
        "Cardiac muscle histology 400x.jpg",
        "Muscle Tissue Cardiac Muscle (28184529378).jpg",
    ],
    "nervous_ganglion": [
        "SFEC-2012-EXP-DOG-SPINAL GANGLION-H&E009.JPG",
    ],
    "nervous_cortex": [
        "Slide 119 - Cerebrum, Cerebral cortex (gray matter).jpg",
        "Cerebral cortex slide.jpg",
    ],
    "adipose_tissue": [
        "A microscopy image of rabbit's adipose tissue.JPG",
        "Adipose tissue - intermedial mag.jpg",
    ],
    "liver": [
        "Alpha-smooth muscle actin (ASMA) expression in normal fetal liver.jpg",
        "Liver - intermedial mag.jpg",
    ],
}

SEARCH_TERMS = {
    "epithelial": ["simple columnar epithelium histology H&E"],
    "connective": ["dense regular connective tissue histology", "granulation tissue HE"],
    "muscular": ["cardiac muscle histology 400x", "skeletal muscle histology high magnification"],
    "nervous": ["cerebral cortex histology slide H&E", "spinal ganglion H&E"],
    "adipose": ["adipose tissue histology microscopy"],
    "liver": ["liver histology H&E hepatocytes"],
}


def _fetch(url, binary=False, retries=6):
    last = None
    for attempt in range(retries):
        time.sleep(2 + attempt * 2)
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read() if binary else json.load(r)
        except Exception as e:  # noqa: BLE001
            last = e
    raise RuntimeError(f"Failed {url}: {last}")


def _api(params: dict) -> dict:
    return _fetch(f"{API}?{urllib.parse.urlencode({'format': 'json', **params})}")


def _validate(bgr) -> bool:
    """True if the image looks like a real histology micrograph."""
    if bgr is None or bgr.shape[0] < 300 or bgr.shape[1] < 300:
        return False
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    if float((gray > 235).mean()) > 0.25:
        return False
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h, s = hsv[..., 0].astype(int), hsv[..., 1].astype(int)
    if (s > 30).mean() < 0.3:
        return False
    pink = ((h >= 130) & (h <= 180) & (s > 30)).mean()
    return pink > 0.05


def _info(title: str):
    data = _api({"action": "query", "titles": f"File:{title}",
                 "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": "960"})
    page = next(iter(data["query"]["pages"].values()))
    if "imageinfo" not in page:
        return None
    ii = page["imageinfo"][0]
    em = ii.get("extmetadata", {})
    lic = em.get("LicenseShortName", {}).get("value", "")
    author = re.sub(r"<[^>]+>", "", em.get("Artist", {}).get("value", "Unknown")).strip() or "Unknown"
    return {"thumb": ii["thumburl"], "orig": ii["url"], "license": lic, "author": author,
            "title": title}


def _search_files(term: str, used: set[str]) -> list[str]:
    try:
        data = _api({"action": "query", "list": "search", "srsearch": term,
                     "srnamespace": "6", "srlimit": "20"})
    except RuntimeError:
        return []
    out = []
    for m in data["query"]["search"]:
        t = m["title"].removeprefix("File:")
        if t.lower().endswith((".jpg", ".jpeg", ".png")) and t not in used:
            out.append(t)
    return out


def _try_download(key: str, title: str, out: Path):
    """Return info dict if downloaded+validated, else None."""
    try:
        info = _info(title)
        if not info:
            return None
        data_bytes = _fetch(info["thumb"], binary=True)
        arr = cv2.imdecode(np.frombuffer(data_bytes, np.uint8), cv2.IMREAD_COLOR)
        if not _validate(arr):
            return None
        out.write_bytes(data_bytes)
        print(f"downloaded {key} ← {title}")
        return info
    except Exception as e:  # noqa: BLE001
        print(f"  skip {title}: {e}")
        return None


def download_gallery() -> None:
    meta = []
    for item in GALLERY:
        key = item["key"]
        out = IMAGES_DIR / f"{key}.jpg"
        info = None
        if out.exists() and out.stat().st_size > 10000:
            if _validate(cv2.imread(str(out))):
                info = {"title": item["commons"], "author": "", "license": ""}
                print(f"cached {key}")
        if info is None:
            used = set(PINNED.get(key, [])) | {item["commons"]}
            for title in PINNED.get(key, []):
                info = _try_download(key, title, out)
                if info:
                    break
            if info is None:
                for term in SEARCH_TERMS.get(item["tissue"], []):
                    for title in _search_files(term, used):
                        used.add(title)
                        info = _try_download(key, title, out)
                        if info:
                            break
                    if info:
                        break
        if info:
            meta.append({**item, "file": f"gallery/{key}.jpg",
                         "source_title": info["title"], "author": info["author"],
                         "license": info["license"]})
        else:
            print(f"MISS {key}")
    META_PATH.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"Wrote {len(meta)} entries")


if __name__ == "__main__":
    download_gallery()
