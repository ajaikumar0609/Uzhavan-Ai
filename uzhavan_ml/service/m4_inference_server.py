"""
UZHAVAN AI — M4 v1 Persistent Inference Server
===============================================
Runs persistent real inference using the trained M4 v1 EfficientNetV2-S checkpoint.
Loads checkpoint ONCE at startup. Listens on 127.0.0.1:8001.

Endpoints:
  GET  /health
  POST /predict  (accepts multipart/form-data with 'file'/'image' and optional 'crop',
                  OR application/json with base64 image or file path)
"""

import cgi
import io
import json
import logging
import sys
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict

import numpy as np
from PIL import Image
import torch
import torch.nn as nn
import torchvision
from torchvision import transforms as T

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] M4Server: %(message)s")
logger = logging.getLogger("m4_inference_server")

CROPS = ["banana", "coconut", "groundnut", "sugarcane", "black_gram", "chilli"]
IMNET_MEAN = [0.485, 0.456, 0.406]
IMNET_STD = [0.229, 0.224, 0.225]
RUN_DIR = Path("/Users/ajaikumarn/Desktop/agri/uzhavan_ml/runs_m4/UZ-M4-v1.0-a898475e-s1")


class M4Model(nn.Module):
    """Exact M4 architecture matching training."""
    def __init__(self, classes: Dict[str, list]):
        super().__init__()
        bb = torchvision.models.efficientnet_v2_s(weights=None)
        nf = bb.classifier[1].in_features
        bb.classifier = nn.Identity()
        self.backbone = bb
        self.drop = nn.Dropout(0.3)
        self.heads = nn.ModuleDict({c: nn.Linear(nf, len(classes[c])) for c in CROPS})

    def forward(self, x: torch.Tensor, crop_name: str) -> torch.Tensor:
        f = self.drop(self.backbone(x))
        return self.heads[crop_name](f)


class M4InferenceEngine:
    def __init__(self, run_dir: Path = RUN_DIR):
        self.run_dir = run_dir
        self.classes_path = run_dir / "classes.json"
        self.checkpoint_path = run_dir / "checkpoint_best.pt"
        self.experiment_path = run_dir / "experiment.json"

        logger.info("Loading classes from %s", self.classes_path)
        with open(self.classes_path) as f:
            self.classes = json.load(f)

        logger.info("Loading experiment metadata from %s", self.experiment_path)
        with open(self.experiment_path) as f:
            self.experiment_meta = json.load(f)

        self.experiment_id = self.experiment_meta.get("experiment_id", "UZ-M4-v1.0-a898475e-s1")
        self.model_version = "v1.0"
        self.model_architecture = "EfficientNetV2-S"

        logger.info("Initializing EfficientNetV2-S model...")
        self.device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
        logger.info("Inference device: %s", self.device)

        self.model = M4Model(self.classes)
        checkpoint = torch.load(self.checkpoint_path, map_location="cpu")
        self.model.load_state_dict(checkpoint["model"])
        self.model.to(self.device)
        self.model.eval()

        self.transform = T.Compose([
            T.Resize(256),
            T.CenterCrop(224),
            T.ToTensor(),
            T.Normalize(mean=IMNET_MEAN, std=IMNET_STD),
        ])
        logger.info("Model loaded successfully and resident in memory!")

    def predict(self, image_bytes: bytes, crop: str = "groundnut") -> Dict[str, Any]:
        if crop not in self.classes:
            crop = "groundnut"  # Default to groundnut for showcase

        t0 = time.perf_counter()
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        x = self.transform(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(x, crop)
            probs = torch.softmax(logits.float(), dim=-1)[0].cpu().numpy()

        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        crop_classes = self.classes[crop]
        sorted_indices = probs.argsort()[::-1]

        top_class_full = crop_classes[sorted_indices[0]]
        # Remove prefix e.g. "groundnut__rust" -> "rust"
        predicted_clean = top_class_full.split("__", 1)[-1] if "__" in top_class_full else top_class_full
        confidence = float(round(float(probs[sorted_indices[0]]), 4))

        top3 = []
        for idx in sorted_indices[:3]:
            cls_full = crop_classes[idx]
            cls_clean = cls_full.split("__", 1)[-1] if "__" in cls_full else cls_full
            top3.append({
                "class": cls_clean,
                "class_id": cls_full,
                "probability": float(round(float(probs[idx]), 4)),
            })

        timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

        return {
            "status": "demo_result",
            "crop": crop,
            "predicted_class": predicted_clean,
            "predicted_class_id": top_class_full,
            "confidence": confidence,
            "top3": top3,
            "model_architecture": self.model_architecture,
            "model_version": self.model_version,
            "experiment_id": self.experiment_id,
            "demo_mode": True,
            "production_certified": False,
            "inference_timestamp": timestamp,
            "latency_ms": latency_ms,
        }


# Global engine instance loaded ONCE
ENGINE = None


class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info("%s - %s", self.address_string(), format % args)

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = {
                "status": "ok",
                "model_loaded": ENGINE is not None,
                "model_architecture": "EfficientNetV2-S",
                "experiment_id": "UZ-M4-v1.0-a898475e-s1",
            }
            self.wfile.write(json.dumps(resp).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path != "/predict":
            self.send_response(404)
            self.end_headers()
            return

        content_type = self.headers.get("Content-Type", "")
        crop = "groundnut"
        image_bytes = None

        if "multipart/form-data" in content_type:
            environ = {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": content_type,
            }
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ=environ,
            )
            if "crop" in form:
                crop = form["crop"].value
            elif "crop_id" in form:
                crop = form["crop_id"].value

            file_item = form.getfirst("image", form.getfirst("file"))
            if file_item is not None:
                if hasattr(file_item, "file"):
                    image_bytes = file_item.file.read()
                elif isinstance(file_item, bytes):
                    image_bytes = file_item
            elif "image_path" in form:
                with open(form["image_path"].value, "rb") as f:
                    image_bytes = f.read()

        elif "application/json" in content_type:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            crop = body.get("crop", body.get("crop_id", "groundnut"))
            if "image_path" in body:
                with open(body["image_path"], "rb") as f:
                    image_bytes = f.read()
            elif "image_base64" in body:
                import base64
                image_bytes = base64.b64decode(body["image_base64"])
        else:
            # Raw bytes in body
            length = int(self.headers.get("Content-Length", 0))
            image_bytes = self.rfile.read(length)

        if not image_bytes:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "No image data provided"}).encode("utf-8"))
            return

        try:
            result = ENGINE.predict(image_bytes, crop=crop)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode("utf-8"))
        except Exception as e:
            logger.exception("Inference error: %s", e)
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))


def run(port: int = 8001):
    global ENGINE
    ENGINE = M4InferenceEngine()
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, RequestHandler)
    logger.info("Serving M4 Inference API on http://127.0.0.1:%d", port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping M4 Inference Server...")
        httpd.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    run(port)
