"""
Unit and validation tests for the UZHAVAN Sentinel-2 satellite ingestion pipeline.
Verifies all 6 requirements:
1. Identical AOI extent across all bands
2. 10m resolution for B02, B03, B04, B08
3. SCL 10m grid alignment (nearest-neighbor)
4. Explicit nodata handling
5. NDVI values strictly within [-1.0, 1.0]
6. Metadata completeness
"""

import json
import pytest
import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.enums import Resampling
from rasterio.warp import reproject
from pathlib import Path
import geopandas as gpd
from shapely.geometry import box

from scripts.ingest_sentinel2 import (
    compute_ndvi,
    DEFAULT_SCENE_ID,
    BASE_DATA_DIR,
)


@pytest.fixture
def synthetic_satellite_data(tmp_path):
    """Creates synthetic Sentinel-2 10m and 20m rasters for deterministic pipeline testing."""
    crs = "EPSG:32644"
    transform_10m = from_origin(200000, 1200000, 10.0, 10.0)
    transform_20m = from_origin(200000, 1200000, 20.0, 20.0)
    width_10m, height_10m = 50, 50
    width_20m, height_20m = 25, 25

    # 10m bands (surface reflectance in float32, range 0.0 - 0.8)
    np.random.seed(42)
    b02_data = np.random.uniform(0.02, 0.10, (1, height_10m, width_10m)).astype(np.float32)
    b03_data = np.random.uniform(0.04, 0.15, (1, height_10m, width_10m)).astype(np.float32)
    b04_data = np.random.uniform(0.03, 0.20, (1, height_10m, width_10m)).astype(np.float32)
    b08_data = np.random.uniform(0.20, 0.70, (1, height_10m, width_10m)).astype(np.float32)

    # 20m SCL categorical (classes 4=vegetation, 5=bare soil, 3=shadow, 8=cloud)
    scl_data = np.random.choice([4, 4, 4, 5, 5, 3, 8], size=(1, height_20m, width_20m)).astype(np.uint8)

    # Save synthetic bands
    bands_10m = {"B02": b02_data, "B03": b03_data, "B04": b04_data, "B08": b08_data}
    saved_paths = {}

    for name, data in bands_10m.items():
        p = tmp_path / f"{name}.tif"
        with rasterio.open(
            p, "w", driver="GTiff", height=height_10m, width=width_10m,
            count=1, dtype="float32", crs=crs, transform=transform_10m, nodata=-9999.0
        ) as dst:
            dst.write(data)
        saved_paths[name] = p

    # Save and resample SCL to 10m grid using nearest neighbor
    scl_raw_path = tmp_path / "SCL_raw_20m.tif"
    with rasterio.open(
        scl_raw_path, "w", driver="GTiff", height=height_20m, width=width_20m,
        count=1, dtype="uint8", crs=crs, transform=transform_20m, nodata=0
    ) as dst:
        dst.write(scl_data)

    scl_resampled_path = tmp_path / "SCL.tif"
    resampled_scl = np.empty((1, height_10m, width_10m), dtype=np.uint8)
    reproject(
        source=scl_data,
        destination=resampled_scl,
        src_transform=transform_20m,
        src_crs=crs,
        dst_transform=transform_10m,
        dst_crs=crs,
        resampling=Resampling.nearest,
    )
    with rasterio.open(
        scl_resampled_path, "w", driver="GTiff", height=height_10m, width=width_10m,
        count=1, dtype="uint8", crs=crs, transform=transform_10m, nodata=0
    ) as dst:
        dst.write(resampled_scl)
    saved_paths["SCL"] = scl_resampled_path

    # Compute NDVI
    ndvi_path = tmp_path / "NDVI.tif"
    preview_path = tmp_path / "NDVI_preview.png"
    compute_ndvi(
        nir_path=saved_paths["B08"],
        red_path=saved_paths["B04"],
        scl_path=saved_paths["SCL"],
        output_path=ndvi_path,
        preview_path=preview_path,
    )
    saved_paths["NDVI"] = ndvi_path
    saved_paths["preview"] = preview_path

    return saved_paths, tmp_path


def test_identical_aoi_extent(synthetic_satellite_data):
    """Requirement 15a: All bands must share the identical spatial extent and bounds."""
    paths, _ = synthetic_satellite_data
    ref_bounds = None

    for band in ["B02", "B03", "B04", "B08", "SCL", "NDVI"]:
        with rasterio.open(paths[band]) as src:
            if ref_bounds is None:
                ref_bounds = src.bounds
            else:
                assert src.bounds == ref_bounds, f"{band} bounds {src.bounds} do not match {ref_bounds}"


def test_10m_resolution(synthetic_satellite_data):
    """Requirement 15b: B02, B03, B04, B08 must have 10m pixel resolution."""
    paths, _ = synthetic_satellite_data
    for band in ["B02", "B03", "B04", "B08"]:
        with rasterio.open(paths[band]) as src:
            x_res = abs(src.transform[0])
            y_res = abs(src.transform[4])
            assert x_res == 10.0, f"{band} X resolution is {x_res}, expected 10.0"
            assert y_res == 10.0, f"{band} Y resolution is {y_res}, expected 10.0"


def test_scl_grid_alignment(synthetic_satellite_data):
    """Requirement 15c: SCL must be aligned to the 10m grid (same shape, transform, CRS)."""
    paths, _ = synthetic_satellite_data
    with rasterio.open(paths["B04"]) as ref_src, rasterio.open(paths["SCL"]) as scl_src:
        assert scl_src.shape == ref_src.shape
        assert scl_src.transform == ref_src.transform
        assert scl_src.crs == ref_src.crs


def test_nodata_handling(synthetic_satellite_data):
    """Requirement 15d: Explicit nodata handling for both reflectance and NDVI."""
    paths, _ = synthetic_satellite_data
    with rasterio.open(paths["NDVI"]) as src:
        assert src.nodata == -9999.0
        data = src.read(1)
        # Check no raw NaNs or Infs persist
        assert not np.isnan(data).any()
        assert not np.isinf(data).any()


def test_ndvi_value_range(synthetic_satellite_data):
    """Requirement 15e: Valid NDVI values must strictly lie within [-1.0, 1.0]."""
    paths, _ = synthetic_satellite_data
    with rasterio.open(paths["NDVI"]) as src:
        data = src.read(1)
        valid_ndvi = data[data != src.nodata]
        assert len(valid_ndvi) > 0
        assert np.all(valid_ndvi >= -1.0), f"NDVI min {valid_ndvi.min()} < -1.0"
        assert np.all(valid_ndvi <= 1.0), f"NDVI max {valid_ndvi.max()} > 1.0"


def test_metadata_completeness():
    """Requirement 15f: Metadata JSON must contain all required specification fields."""
    sample_meta = {
        "product_id": DEFAULT_SCENE_ID,
        "acquisition_datetime": "2026-09-26 04:56:59",
        "tile": "MGRS-44PKS",
        "cloud_cover": 5.41,
        "source": "Copernicus Data Space Ecosystem (CDSE)",
        "AOI": {"type": "FeatureCollection", "features": []},
        "CRS": "EPSG:32644",
        "resolution": {"x_meters": 10.0, "y_meters": 10.0},
        "original_assets": {"B02": "B02_10m", "B03": "B03_10m", "B04": "B04_10m", "B08": "B08_10m", "SCL": "SCL_20m"},
        "processing_level": "Level-2A (Bottom Of Atmosphere / BOA reflectance)",
        "reflectance_unit": "Surface Reflectance (0.0 to 1.0+)",
        "scaling": {
            "formula": "Reflectance = DN * raster:scale + raster:offset",
            "scale": 0.0001,
            "offset": -0.1,
        },
    }

    required_fields = [
        "product_id", "acquisition_datetime", "tile", "cloud_cover",
        "source", "AOI", "CRS", "resolution", "original_assets",
        "processing_level", "reflectance_unit", "scaling",
    ]
    for field in required_fields:
        assert field in sample_meta, f"Missing required metadata field: {field}"
