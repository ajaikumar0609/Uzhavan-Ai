"""
UZHAVAN AI — M4 v1 Standalone Demo Inference Script
===================================================
Runs REAL inference using the existing trained M4 v1 EfficientNetV2-S checkpoint.
NO training. NO data modifications. NO fabricated metrics.

Usage:
  python demo_m4_inference.py --image PATH_TO_IMAGE --crop CROP_NAME [--run_dir PATH_TO_RUN]
"""

import argparse
import json
import time
from pathlib import Path
from PIL import Image
import torch
import torch.nn as nn
import torchvision
from torchvision import transforms as T

CROPS = ["banana", "coconut", "groundnut", "sugarcane", "black_gram", "chilli"]
IMNET_MEAN = [0.485, 0.456, 0.406]
IMNET_STD = [0.229, 0.224, 0.225]


class M4Model(nn.Module):
    """Exact M4 architecture from train_m4.py."""
    def __init__(self, classes):
        super().__init__()
        bb = torchvision.models.efficientnet_v2_s(weights=None)
        nf = bb.classifier[1].in_features
        bb.classifier = nn.Identity()
        self.backbone = bb
        self.drop = nn.Dropout(0.3)
        self.heads = nn.ModuleDict({c: nn.Linear(nf, len(classes[c])) for c in CROPS})

    def forward(self, x, crop_name):
        f = self.drop(self.backbone(x))
        return self.heads[crop_name](f)


def get_inference_transform():
    """Exact inference transform from train_m4.py."""
    return T.Compose([
        T.Resize(256),
        T.CenterCrop(224),
        T.ToTensor(),
        T.Normalize(mean=IMNET_MEAN, std=IMNET_STD),
    ])


def main():
    parser = argparse.ArgumentParser(description="Run real inference with existing M4 v1 checkpoint")
    parser.add_argument("--image", type=str, required=True, help="Path to input crop leaf image")
    parser.add_argument("--crop", type=str, required=True, choices=CROPS, help="Target crop name")
    parser.add_argument(
        "--run_dir",
        type=str,
        default="uzhavan_ml/runs_m4/UZ-M4-v1.0-a898475e-s1",
        help="Path to existing trained M4 v1 experiment directory",
    )
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    image_path = Path(args.image)

    if not image_path.exists():
        raise FileNotFoundError(f"Input image not found: {image_path}")

    # Load classes and experiment metadata
    classes_file = run_dir / "classes.json"
    experiment_file = run_dir / "experiment.json"
    checkpoint_file = run_dir / "checkpoint_best.pt"

    with open(classes_file) as f:
        classes = json.load(f)

    with open(experiment_file) as f:
        experiment_meta = json.load(f)

    # Initialize model with exact architecture
    model = M4Model(classes)
    checkpoint = torch.load(checkpoint_file, map_location="cpu")
    model.load_state_dict(checkpoint["model"])
    model.eval()

    # Preprocess image
    tf = get_inference_transform()
    img = Image.open(image_path).convert("RGB")
    x = tf(img).unsqueeze(0)  # Shape: (1, 3, 224, 224)

    # Measure inference latency
    t0 = time.perf_counter()
    with torch.no_grad():
        logits = model(x, args.crop)
        probs = torch.softmax(logits.float(), dim=-1)[0].cpu().numpy()
    latency_ms = (time.perf_counter() - t0) * 1000.0

    crop_classes = classes[args.crop]
    top_indices = probs.argsort()[::-1]

    predicted_idx = top_indices[0]
    predicted_class = crop_classes[predicted_idx]
    confidence = float(probs[predicted_idx])

    top3 = [
        {"class": crop_classes[idx], "probability": float(probs[idx])}
        for idx in top_indices[:min(3, len(crop_classes))]
    ]

    # Terminal output
    print("=" * 60)
    print("UZHAVAN AI — M4 v1 REAL INFERENCE RESULT")
    print("=" * 60)
    print(f"Crop:               {args.crop}")
    print(f"Input Image:        {image_path.name}")
    print(f"Predicted Class:    {predicted_class}")
    print(f"Confidence:         {confidence * 100:.2f}% ({confidence:.4f})")
    print("\nTop-3 Probabilities:")
    for rank, item in enumerate(top3, 1):
        print(f"  {rank}. {item['class']:<32} : {item['probability'] * 100:6.2f}%")
    print("-" * 60)
    print(f"Model Architecture: EfficientNetV2-S")
    print(f"Model Version:      {experiment_meta.get('model_version', 'v1.0')}")
    print(f"Experiment ID:      {experiment_meta.get('experiment_id', 'Unknown')}")
    print(f"Checkpoint Epoch:   {checkpoint.get('epoch')}")
    print(f"Inference Latency:  {latency_ms:.2f} ms")
    print("=" * 60)


if __name__ == "__main__":
    main()
