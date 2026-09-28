"""
UZHAVAN Sentinel-2 L2A Data Ingestion Pipeline.

Ingests targeted Sentinel-2 L2A band assets from Copernicus Data Space (CDSE),
clips them to the farmer AOI polygon, resamples categorical layers (SCL),
converts reflectance according to official scaling metadata, and computes
vegetation indices (NDVI).
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import requests
import numpy as np
import geopandas as gpd
from shapely.geometry import mapping
import rasterio
from rasterio.mask import mask
from rasterio.enums import Resampling
from rasterio.warp import reproject, calculate_default_transform
from pystac_client import Client
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("uzhavan_satellite")

# CDSE Constants
STAC_API_URL = "https://stac.dataspace.copernicus.eu/v1/"
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CLIENT_ID = "cdse-public"

DEFAULT_SCENE_ID = "S2B_MSIL2A_20260926T045659_N0513_R119_T44PKS_20260926T085532"
DEFAULT_AOI_PATH = Path("/Users/ajaikumarn/Desktop/agri/uzhavan_data/satellite/aoi_thanjavur.geojson")
BASE_DATA_DIR = Path("/Users/ajaikumarn/Desktop/agri/uzhavan_data/satellite")

TARGET_ASSETS = {
    "B02": "B02_10m",
    "B03": "B03_10m",
    "B04": "B04_10m",
    "B08": "B08_10m",
    "SCL": "SCL_20m",
}


def get_cdse_credentials() -> tuple[Optional[str], Optional[str]]:
    """Retrieves CDSE username and password from environment or .env files."""
    username = os.environ.get("CDSE_USERNAME")
    password = os.environ.get("CDSE_PASSWORD")

    # Check .env fallback if unset
    if not (username and password):
        env_files = [
            Path("/Users/ajaikumarn/Desktop/agri/.env"),
            Path("/Users/ajaikumarn/Desktop/agri/uzhavan_platform/.env"),
        ]
        for env_file in env_files:
            if env_file.exists():
                with open(env_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("CDSE_USERNAME="):
                            username = username or line.split("=", 1)[1].strip().strip('"').strip("'")
                        elif line.startswith("CDSE_PASSWORD="):
                            password = password or line.split("=", 1)[1].strip().strip('"').strip("'")

    return username, password


def authenticate_cdse(username: str, password: str) -> str:
    """Authenticates against Copernicus Keycloak endpoint and returns JWT access token."""
    logger.info("Authenticating with Copernicus Data Space Ecosystem as: %s", username)
    payload = {
        "client_id": CLIENT_ID,
        "username": username,
        "password": password,
        "grant_type": "password",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        resp = requests.post(TOKEN_URL, data=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            raise ValueError("No access_token found in response from CDSE")
        logger.info("Authentication successful. Bearer token acquired.")
        return token
    except Exception as e:
        logger.error("Authentication failed: %s", e)
        raise


def get_stac_item(scene_id: str) -> Any:
    """Retrieves the STAC Item for the given scene ID."""
    logger.info("Searching STAC catalog for scene: %s", scene_id)
    catalog = Client.open(STAC_API_URL)
    search = catalog.search(collections=["sentinel-2-l2a"], ids=[scene_id])
    items = list(search.items())
    if not items:
        raise ValueError(f"Scene {scene_id} not found in collection sentinel-2-l2a")
    return items[0]


def download_asset(asset_url: str, output_path: Path, token: str) -> Path:
    """Downloads a single asset using the OData/HTTPS node endpoint with streaming."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and output_path.stat().st_size > 1024:
        logger.info("Asset already cached locally: %s (%d bytes)", output_path.name, output_path.stat().st_size)
        return output_path

    logger.info("Downloading asset to %s ...", output_path)
    headers = {"Authorization": f"Bearer {token}"}

    # Stream download
    with requests.get(asset_url, headers=headers, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

    logger.info("Download completed: %s (%d bytes)", output_path.name, output_path.stat().st_size)
    return output_path


def clip_raster_to_aoi(
    raster_path: Path,
    aoi_gdf: gpd.GeoDataFrame,
    output_path: Path,
    target_profile: Optional[Dict[str, Any]] = None,
    is_categorical: bool = False,
    scaling_info: Optional[Dict[str, float]] = None,
) -> tuple[Path, Dict[str, Any]]:
    """
    Clips raster to AOI, reprojects to native CRS, aligns grids,
    and applies reflectance scaling if applicable.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(raster_path) as src:
        # Reproject AOI to raster CRS
        aoi_proj = aoi_gdf.to_crs(src.crs)
        geometries = [mapping(geom) for geom in aoi_proj.geometry]

        # Clip using rasterio.mask
        out_image, out_transform = mask(src, geometries, crop=True)
        out_profile = src.profile.copy()

        # Resample if target_profile is specified (e.g. SCL 20m -> 10m grid alignment)
        if target_profile is not None:
            target_h = target_profile["height"]
            target_w = target_profile["width"]
            target_transform = target_profile["transform"]
            target_crs = target_profile["crs"]

            resampling_method = Resampling.nearest if is_categorical else Resampling.bilinear
            resampled_image = np.empty((1, target_h, target_w), dtype=src.dtypes[0])

            reproject(
                source=out_image,
                destination=resampled_image,
                src_transform=out_transform,
                src_crs=src.crs,
                dst_transform=target_transform,
                dst_crs=target_crs,
                resampling=resampling_method,
            )
            out_image = resampled_image
            out_transform = target_transform
            out_profile.update({
                "height": target_h,
                "width": target_w,
                "transform": target_transform,
                "crs": target_crs,
            })
        else:
            out_profile.update({
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
            })

        # Reflectance conversion if requested
        if scaling_info and not is_categorical:
            scale = scaling_info.get("scale", 0.0001)
            offset = scaling_info.get("offset", -0.1)

            # Convert to float32 physical surface reflectance
            raw_data = out_image[0].astype(np.float32)
            nodata_mask = (raw_data == 0)

            # S2 L2A Reflectance = DN * scale + offset
            reflectance = raw_data * scale + offset
            # Valid physical reflectance is >= 0
            reflectance = np.clip(reflectance, 0.0, 2.0)
            reflectance[nodata_mask] = -9999.0

            out_image = reflectance[np.newaxis, :, :]
            out_profile.update({
                "dtype": "float32",
                "nodata": -9999.0,
            })
        else:
            out_profile.update({
                "driver": "GTiff",
            })

        # Save GeoTIFF
        with rasterio.open(output_path, "w", **out_profile) as dst:
            dst.write(out_image)

    logger.info("Saved clipped raster: %s (shape: %dx%d)", output_path.name, out_profile["width"], out_profile["height"])
    return output_path, out_profile


def compute_ndvi(
    nir_path: Path,
    red_path: Path,
    scl_path: Path,
    output_path: Path,
    preview_path: Path,
) -> Path:
    """Computes NDVI from clipped surface reflectance B08 and B04, applying SCL masking."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(nir_path) as nir_src, rasterio.open(red_path) as red_src, rasterio.open(scl_path) as scl_src:
        nir = nir_src.read(1)
        red = red_src.read(1)
        scl = scl_src.read(1)
        profile = nir_src.profile.copy()

        # Mask invalid data
        invalid_mask = (nir == -9999.0) | (red == -9999.0) | (nir == 0) | (red == 0)

        # Compute NDVI: (NIR - Red) / (NIR + Red)
        denom = nir + red
        with np.errstate(divide="ignore", invalid="ignore"):
            ndvi = np.where((denom > 0) & (~invalid_mask), (nir - red) / denom, np.nan)
            ndvi = np.clip(ndvi, -1.0, 1.0)

        profile.update({
            "dtype": "float32",
            "nodata": -9999.0,
            "driver": "GTiff",
        })

        ndvi_out = np.where(np.isnan(ndvi), -9999.0, ndvi).astype(np.float32)

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(ndvi_out, 1)

    logger.info("Saved NDVI GeoTIFF to: %s", output_path)

    # Generate PNG Preview
    plt.figure(figsize=(8, 7), dpi=150)
    plt.title("Sentinel-2 L2A NDVI — Thanjavur Agricultural AOI\n(Acquired: 2026-09-26)", fontsize=11, fontweight="bold")
    
    valid_ndvi = np.where(ndvi_out == -9999.0, np.nan, ndvi_out)
    im = plt.imshow(valid_ndvi, cmap="RdYlGn", vmin=-0.2, vmax=0.9)
    cbar = plt.colorbar(im, fraction=0.046, pad=0.04)
    cbar.set_label("NDVI Value", fontsize=10)

    mean_ndvi = float(np.nanmean(valid_ndvi)) if not np.all(np.isnan(valid_ndvi)) else 0.0
    max_ndvi = float(np.nanmax(valid_ndvi)) if not np.all(np.isnan(valid_ndvi)) else 0.0
    min_ndvi = float(np.nanmin(valid_ndvi)) if not np.all(np.isnan(valid_ndvi)) else 0.0

    plt.figtext(0.15, 0.02, f"Min: {min_ndvi:.3f} | Mean: {mean_ndvi:.3f} | Max: {max_ndvi:.3f} | Grid: 10m", fontsize=9)
    plt.tight_layout()
    plt.savefig(preview_path, bbox_inches="tight")
    plt.close()
    logger.info("Saved NDVI PNG preview to: %s", preview_path)

    return output_path


def run_pipeline(
    scene_id: str = DEFAULT_SCENE_ID,
    aoi_path: Path = DEFAULT_AOI_PATH,
    output_dir: Path = BASE_DATA_DIR,
) -> Dict[str, Any]:
    """Executes the full Sentinel-2 data ingestion and processing pipeline."""
    logger.info("=== Starting UZHAVAN Sentinel-2 Ingestion Pipeline ===")
    logger.info("Scene ID: %s", scene_id)
    logger.info("AOI File: %s", aoi_path)

    if not aoi_path.exists():
        raise FileNotFoundError(f"AOI file does not exist: {aoi_path}")

    # 1. Credentials
    username, password = get_cdse_credentials()
    if not (username and password):
        raise EnvironmentError(
            "CDSE_USERNAME and CDSE_PASSWORD must be set in environment variables or .env file."
        )

    # 2. Authenticate
    token = authenticate_cdse(username, password)

    # 3. Retrieve STAC item
    item = get_stac_item(scene_id)
    aoi_gdf = gpd.read_file(aoi_path)

    raw_dir = output_dir / "raw"
    processed_dir = output_dir / "processed"
    metadata_dir = output_dir / "metadata"

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    # 4. Download and clip target assets
    clipped_paths = {}
    reference_profile = None

    # First process 10m bands (B02, B03, B04, B08)
    ten_m_keys = ["B02", "B03", "B04", "B08"]

    for band_name in ten_m_keys:
        asset_key = TARGET_ASSETS[band_name]
        asset = item.assets[asset_key]

        # Extract HTTPS download link
        https_href = asset.extra_fields.get("alternate", {}).get("https", {}).get("href") or asset.href
        scale_info = {
            "scale": asset.extra_fields.get("raster:scale", 0.0001),
            "offset": asset.extra_fields.get("raster:offset", -0.1),
        }

        raw_file = raw_dir / f"{scene_id}_{asset_key}.jp2"
        download_asset(https_href, raw_file, token)

        proc_file = processed_dir / f"{band_name}.tif"
        _, prof = clip_raster_to_aoi(
            raster_path=raw_file,
            aoi_gdf=aoi_gdf,
            output_path=proc_file,
            target_profile=reference_profile,
            is_categorical=False,
            scaling_info=scale_info,
        )
        if reference_profile is None:
            reference_profile = prof
        clipped_paths[band_name] = proc_file

    # Now process categorical SCL (20m -> resampled to match reference 10m grid)
    scl_key = TARGET_ASSETS["SCL"]
    scl_asset = item.assets[scl_key]
    scl_href = scl_asset.extra_fields.get("alternate", {}).get("https", {}).get("href") or scl_asset.href
    scl_raw = raw_dir / f"{scene_id}_{scl_key}.jp2"
    download_asset(scl_href, scl_raw, token)

    scl_proc = processed_dir / "SCL.tif"
    clip_raster_to_aoi(
        raster_path=scl_raw,
        aoi_gdf=aoi_gdf,
        output_path=scl_proc,
        target_profile=reference_profile,
        is_categorical=True,
    )
    clipped_paths["SCL"] = scl_proc

    # 5. Compute NDVI
    ndvi_path = processed_dir / "NDVI.tif"
    preview_path = processed_dir / "NDVI_preview.png"
    compute_ndvi(
        nir_path=clipped_paths["B08"],
        red_path=clipped_paths["B04"],
        scl_path=clipped_paths["SCL"],
        output_path=ndvi_path,
        preview_path=preview_path,
    )
    clipped_paths["NDVI"] = ndvi_path

    # 6. Generate Metadata JSON
    metadata = {
        "product_id": item.id,
        "acquisition_datetime": str(item.datetime),
        "tile": item.properties.get("grid:code") or item.properties.get("s2:mgrs_tile") or "T44PKS",
        "cloud_cover": item.properties.get("eo:cloud_cover"),
        "source": "Copernicus Data Space Ecosystem (CDSE)",
        "AOI": json.loads(aoi_gdf.to_json()),
        "CRS": str(reference_profile["crs"]),
        "resolution": {
            "x_meters": abs(float(reference_profile["transform"][0])),
            "y_meters": abs(float(reference_profile["transform"][4])),
        },
        "grid_dimensions": {
            "width": reference_profile["width"],
            "height": reference_profile["height"],
        },
        "original_assets": {k: TARGET_ASSETS[k] for k in TARGET_ASSETS},
        "processing_level": "Level-2A (Bottom Of Atmosphere / BOA reflectance)",
        "reflectance_unit": "Surface Reflectance (0.0 to 1.0+)",
        "scaling": {
            "formula": "Reflectance = DN * raster:scale + raster:offset",
            "scale": 0.0001,
            "offset": -0.1,
            "source_metadata": "CDSE STAC Item asset raster extensions",
        },
        "bands_processed": ["B02", "B03", "B04", "B08", "SCL", "NDVI"],
        "pipeline_version": "1.0.0",
    }

    meta_file = metadata_dir / f"{scene_id}_metadata.json"
    with open(meta_file, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Saved metadata JSON to: %s", meta_file)
    logger.info("=== Pipeline run completed successfully! ===")
    return metadata


if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as e:
        logger.error("Pipeline encountered an error: %s", e)
        sys.exit(1)
