from pystac_client import Client

catalog = Client.open("https://stac.dataspace.copernicus.eu/v1/")
item_id = "S2B_MSIL2A_20260926T045659_N0513_R119_T44PKS_20260926T085532"

search = catalog.search(
    collections=["sentinel-2-l2a"],
    ids=[item_id],
)

item = next(search.items())
print("ITEM:", item.id)
print("\nASSETS:")
for key, asset in item.assets.items():
    print(f"{key:12} | {asset.title} | {asset.href}")
