from __future__ import annotations

import os
import threading
import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow.keras.applications import VGG16
from tensorflow.keras.applications.vgg16 import preprocess_input as vgg16_preprocess
from tensorflow.keras.applications import ResNet152V2
from tensorflow.keras.applications.resnet_v2 import preprocess_input as resnet_preprocess

# Dataset directories (absolute paths)
# Move up two levels from app/predict/ → project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATASET_ROOT = os.path.join(PROJECT_ROOT, 'Datasets', 'training_set')

NAIL_CLASSES = ["healthy_nails", "unhealthy_nails"]
SKIN_CLASSES = ["healthy_skin", "unhealthy_skin"]

# Globals for lazy init
_vgg16_feature_extractor = None
_resnet_feature_extractor = None
_nail_class_to_centroid: dict[str, np.ndarray] | None = None
_skin_class_to_centroid: dict[str, np.ndarray] | None = None
_init_lock = threading.Lock()
_use_heuristic_fallback = False


def _load_feature_extractors() -> None:
    """Lazily create feature extractors for nails (VGG16) and skin (ResNet152V2)."""
    global _vgg16_feature_extractor, _resnet_feature_extractor
    if _vgg16_feature_extractor is None:
        _vgg16_feature_extractor = VGG16(weights='imagenet', include_top=False, pooling='avg')
    if _resnet_feature_extractor is None:
        _resnet_feature_extractor = ResNet152V2(weights='imagenet', include_top=False, pooling='avg')


def _iter_class_images(class_dir: str):
    if not os.path.isdir(class_dir):
        return
    for name in os.listdir(class_dir):
        if not name.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        yield os.path.join(class_dir, name)


def _image_to_array(image_path: str, size=(224, 224)) -> np.ndarray:
    img = Image.open(image_path).convert('RGB')
    img = img.resize(size)
    arr = np.array(img)
    arr = np.expand_dims(arr, axis=0)
    return arr


def _compute_centroids() -> None:
    """Compute class centroids from the training set for nails and skin."""
    global _nail_class_to_centroid, _skin_class_to_centroid

    # Ensure models are ready
    _load_feature_extractors()

    nail_centroids: dict[str, list[np.ndarray]] = {c: [] for c in NAIL_CLASSES}
    skin_centroids: dict[str, list[np.ndarray]] = {c: [] for c in SKIN_CLASSES}

    # Nails
    for class_name in NAIL_CLASSES:
        class_dir = os.path.join(DATASET_ROOT, class_name)
        for img_path in _iter_class_images(class_dir):
            try:
                x = _image_to_array(img_path)
                x = vgg16_preprocess(x)
                feat = _vgg16_feature_extractor.predict(x, verbose=0)
                nail_centroids[class_name].append(feat.squeeze())
            except Exception:
                continue

    # Skin
    for class_name in SKIN_CLASSES:
        class_dir = os.path.join(DATASET_ROOT, class_name)
        for img_path in _iter_class_images(class_dir):
            try:
                x = _image_to_array(img_path)
                x = resnet_preprocess(x)
                feat = _resnet_feature_extractor.predict(x, verbose=0)
                skin_centroids[class_name].append(feat.squeeze())
            except Exception:
                continue

    # Mean centroids
    _nail_class_to_centroid = {
        c: (np.mean(v, axis=0) if len(v) > 0 else None) for c, v in nail_centroids.items()
    }
    _skin_class_to_centroid = {
        c: (np.mean(v, axis=0) if len(v) > 0 else None) for c, v in skin_centroids.items()
    }

    # If all centroids are None (no dataset found), enable heuristic fallback
    global _use_heuristic_fallback
    no_nail_centroids = all(val is None for val in _nail_class_to_centroid.values())
    no_skin_centroids = all(val is None for val in _skin_class_to_centroid.values())
    _use_heuristic_fallback = no_nail_centroids or no_skin_centroids


def _ensure_initialized() -> None:
    if _nail_class_to_centroid is not None and _skin_class_to_centroid is not None:
        return
    with _init_lock:
        if _nail_class_to_centroid is None or _skin_class_to_centroid is None:
            _compute_centroids()


def _has_valid_centroids(class_to_centroid: dict[str, np.ndarray]) -> bool:
    return any(centroid is not None for centroid in class_to_centroid.values())


def _simple_hsv_heuristic(image_path: str) -> tuple[str, float]:
    """Simple HSV heuristic: lower saturation/value → unhealthy with higher confidence."""
    try:
        from PIL import Image
        img = Image.open(image_path).convert('HSV')
        arr = np.array(img)
        sat = float(np.mean(arr[:, :, 1]))
        val = float(np.mean(arr[:, :, 2]))
        if sat < 60 and val < 110:
            # likely unhealthy
            conf = 0.8 if sat < 45 or val < 90 else 0.7
            return "unhealthy", conf
        elif sat > 120 and val > 160:
            return "healthy", 0.75
        else:
            return "healthy", 0.6
    except Exception:
        return "healthy", 0.5


def _nearest_centroid(feature: np.ndarray, class_to_centroid: dict[str, np.ndarray]) -> tuple[str, float]:
    best_class = None
    best_dist = float('inf')
    for class_name, centroid in class_to_centroid.items():
        if centroid is None:
            continue
        dist = np.linalg.norm(feature - centroid)
        if dist < best_dist:
            best_dist = dist
            best_class = class_name
    # Convert distance to a calibrated pseudo-confidence in (0.05, 0.99]
    # Use a temperature to avoid underflow to 0.0 for large distances
    if np.isfinite(best_dist):
        temperature = 100.0
        scaled = float(np.exp(-best_dist / temperature))
        confidence = max(0.05, min(0.99, scaled))
    else:
        confidence = 0.5
    return best_class or list(class_to_centroid.keys())[0], confidence


def predict_nail(image_path: str) -> tuple[str, float]:
    """Predict nail health using VGG16 features and nearest-centroid over training set."""
    _ensure_initialized()
    if _use_heuristic_fallback or not _has_valid_centroids(_nail_class_to_centroid):
        label, conf = _simple_hsv_heuristic(image_path)
        # Map to expected class names
        return ("unhealthy_nails" if label == "unhealthy" else "healthy_nails"), conf
    x = _image_to_array(image_path)
    x = vgg16_preprocess(x)
    feat = _vgg16_feature_extractor.predict(x, verbose=0).squeeze()
    return _nearest_centroid(feat, _nail_class_to_centroid)


def predict_skin(image_path: str) -> tuple[str, float]:
    """Predict skin health using ResNet152V2 features and nearest-centroid over training set."""
    _ensure_initialized()
    if _use_heuristic_fallback or not _has_valid_centroids(_skin_class_to_centroid):
        label, conf = _simple_hsv_heuristic(image_path)
        return ("unhealthy_skin" if label == "unhealthy" else "healthy_skin"), conf
    x = _image_to_array(image_path)
    x = resnet_preprocess(x)
    feat = _resnet_feature_extractor.predict(x, verbose=0).squeeze()
    return _nearest_centroid(feat, _skin_class_to_centroid)


def get_predictor():
    """Expose predictor functions and class names (for templates/labels)."""
    class_names = [
        "healthy_nails",
        "unhealthy_nails",
        "healthy_skin",
        "unhealthy_skin",
    ]
    return {"nail": predict_nail, "skin": predict_skin}, class_names

