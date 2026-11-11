from pystac_client import Client

catalog = Client.open("https://stac.dataspace.copernicus.eu/v1/")

# Temporary small Thanjavur agricultural AOI
# lon, lat
aoi = {
    "type": "Polygon",
    "coordinates": [[
        [79.08, 10.80],
        [79.13, 10.80],
        [79.13, 10.84],
        [79.08, 10.84],
        [79.08, 10.80],
    ]],
}

search = catalog.search(
    collections=["sentinel-2-l2a"],
    datetime="2026-09-01/2026-09-28",
    intersects=aoi,
    query={"eo:cloud_cover": {"lte": 20}},
    sortby=[{"field": "properties.eo:cloud_cover", "direction": "asc"}],
    max_items=20,
)

items = list(search.items())
print(f"Found {len(items)} products")

for item in items:
    print("=" * 80)
    print("ID:", item.id)
    print("Date:", item.datetime)
    print("Cloud:", item.properties.get("eo:cloud_cover"))
    print("Tile:", item.properties.get("grid:code") or item.properties.get("s2:mgrs_tile"))
