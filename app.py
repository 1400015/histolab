"""Histolab — HistoIA Web App

Features:
- POST /api/analyze  : real-time AI histology analysis (segmentation + tissue classification)
- POST /api/questions: academic question generation from analysis
- POST /api/chat     : free offline tutor chatbot
- GET  /api/gallery   : preloaded reference tissue gallery
- GET  /api/gallery/<key>/analysis : on-demand analysis of gallery images
"""
from __future__ import annotations

import base64
import io
import json
import threading
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).parent
STATIC = ROOT / "static"
META_PATH = ROOT / "gallery_meta.json"

import sys  # noqa: E402
sys.path.insert(0, str(ROOT))
from analyzer import analyze_image  # noqa: E402
from questions import generate_questions  # noqa: E402
from chatbot import chat_reply  # noqa: E402

app = Flask(__name__, static_folder=str(STATIC), static_url_path="/static")


def _b64_to_bgr(data_uri: str) -> np.ndarray:
    if "," in data_uri:
        data_uri = data_uri.split(",", 1)[1]
    buf = np.frombuffer(base64.b64decode(data_uri), np.uint8)
    img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Imagem inválida ou formato não suportado")
    if max(img.shape) > 1600:
        scale = 1600 / max(img.shape)
        img = cv2.resize(img, (int(img.shape[1] * scale), int(img.shape[0] * scale)))
    return img


@app.post("/api/analyze")
def api_analyze():
    try:
        payload = request.get_json(force=True)
        bgr = _b64_to_bgr(payload["image"])
        result = analyze_image(bgr)
        return jsonify(result)
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 400


@app.post("/api/questions")
def api_questions():
    try:
        payload = request.get_json(force=True)
        analysis = payload.get("analysis", {})
        n = int(payload.get("n", 6))
        difficulty = payload.get("difficulty", "medium")
        seed = payload.get("seed")
        qs = generate_questions(analysis, n=n, difficulty=difficulty, seed=seed)
        return jsonify({"questions": qs})
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 400


@app.post("/api/chat")
def api_chat():
    try:
        payload = request.get_json(force=True)
        msg = payload.get("message", "").strip()
        if not msg:
            return jsonify({"error": "Mensagem vazia"}), 400
        tissue = payload.get("tissue")
        features = payload.get("features")
        reply = chat_reply(msg, tissue=tissue, features=features)
        return jsonify(reply)
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 400


@app.get("/api/gallery")
def api_gallery():
    if not META_PATH.exists():
        return jsonify({"items": []})
    items = json.loads(META_PATH.read_text())
    return jsonify({"items": items})


_gallery_cache: dict[str, dict] = {}
_gallery_lock = threading.Lock()


@app.get("/api/gallery/<key>/analysis")
def api_gallery_analysis(key: str):
    path = STATIC / "gallery" / f"{key}.jpg"
    if not path.exists():
        return jsonify({"error": "Imagem não encontrada"}), 404
    with _gallery_lock:
        if key not in _gallery_cache:
            bgr = cv2.imdecode(np.frombuffer(path.read_bytes(), np.uint8), cv2.IMREAD_COLOR)
            _gallery_cache[key] = analyze_image(bgr)
    return jsonify(_gallery_cache[key])


@app.get("/")
def index():
    return send_from_directory(STATIC, "index.html")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8765, threaded=True)
