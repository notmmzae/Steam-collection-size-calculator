import urllib.request
import urllib.parse
import json
import time

COLLECTION_ID = "3716855116"

def steam_post(endpoint, params):
    url = f"https://api.steampowered.com/{endpoint}/v1/"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def format_size(b):
    if not b:
        return "0 B"
    if b >= 1 << 30:
        return f"{b / (1 << 30):.2f} GB"
    if b >= 1 << 20:
        return f"{b / (1 << 20):.0f} MB"
    if b >= 1 << 10:
        return f"{b / (1 << 10):.0f} KB"
    return f"{b} B"

print("Fetching collection items...")
col = steam_post("ISteamRemoteStorage/GetCollectionDetails", {
    "collectioncount": 1,
    "publishedfileids[0]": COLLECTION_ID
})
children = col["response"]["collectiondetails"][0].get("children", [])
ids = [c["publishedfileid"] for c in children]
print(f"Found {len(ids)} items\n")

CHUNK = 100
all_items = []
total_bytes = 0
unknown = 0

for i in range(0, len(ids), CHUNK):
    chunk = ids[i:i+CHUNK]
    params = {"itemcount": len(chunk)}
    for j, fid in enumerate(chunk):
        params[f"publishedfileids[{j}]"] = fid

    print(f"Fetching details {i+1}-{min(i+CHUNK, len(ids))} of {len(ids)}...", end="\r")
    data = steam_post("ISteamRemoteStorage/GetPublishedFileDetails", params)
    files = data["response"].get("publishedfiledetails", [])

    for f in files:
        size = int(f.get("file_size") or 0)
        name = f.get("title") or f["publishedfileid"]
        all_items.append({"name": name, "size": size})
        if size > 0:
            total_bytes += size
        else:
            unknown += 1

    time.sleep(0.3)  # be polite to Steam

print("\n" + "="*60)
print(f"RESULTS FOR COLLECTION: {col['response']['collectiondetails'][0].get('title', COLLECTION_ID)}")
print("="*60)
print(f"Total mods:       {len(all_items)}")
print(f"Total size:       {format_size(total_bytes)}")
print(f"No size data:     {unknown} mods")
with_size = [x for x in all_items if x["size"] > 0]
if with_size:
    avg = total_bytes / len(with_size)
    print(f"Average per mod:  {format_size(int(avg))}")

print("\nTOP 15 LARGEST MODS:")
print("-"*60)
sorted_items = sorted(with_size, key=lambda x: x["size"], reverse=True)
for item in sorted_items[:15]:
    print(f"  {format_size(item['size']):>10}  {item['name'][:50]}")

print("\n10 SMALLEST MODS:")
print("-"*60)
for item in sorted_items[-10:]:
    print(f"  {format_size(item['size']):>10}  {item['name'][:50]}")