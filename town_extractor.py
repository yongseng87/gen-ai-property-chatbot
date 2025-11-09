import requests
    
url = "https://www.onemap.gov.sg/api/public/popapi/getAllPlanningarea?year=2019"
    
headers = {"Authorization": "Authorisation Key"}
    
response = requests.request("GET", url, headers=headers)


# validate and parse JSON
response.raise_for_status()
api_data = response.json()

# safety: ensure key exists
if "SearchResults" not in api_data:
    raise RuntimeError("API JSON does not contain SearchResults")

# print(response.text)

import json
import math
import pandas as pd

# ---------- geometry helpers ----------
def point_in_ring(x, y, ring):
    # ray-casting algorithm for one linear ring (ring: list of [lon, lat])
    inside = False
    n = len(ring)
    if n < 3:
        return False
    for i in range(n):
        x_i, y_i = ring[i][0], ring[i][1]
        x_j, y_j = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
        # check if edge intersects horizontal ray to the right of (x,y)
        intersect = ((y_i > y) != (y_j > y)) and (x < (x_j - x_i) * (y - y_i) / (y_j - y_i + 1e-20) + x_i)
        if intersect:
            inside = not inside
    return inside

def point_in_polygon(lon, lat, polygon_coords):
    # polygon_coords: list of linear rings (first is exterior, others are holes)
    if not polygon_coords:
        return False
    # exterior ring first
    if not point_in_ring(lon, lat, polygon_coords[0]):
        return False
    # if in exterior, ensure not in any hole
    for hole in polygon_coords[1:]:
        if point_in_ring(lon, lat, hole):
            return False
    return True

def point_in_multipolygon(lon, lat, multipolygon_coords):
    # multipolygon_coords: list of polygons, each polygon is list of rings
    for polygon in multipolygon_coords:
        if point_in_polygon(lon, lat, polygon):
            return True
    return False

def polygon_centroid_from_coords(multipolygon_coords):
    # fallback centroid: compute centroid from all vertex coords (works as fallback only)
    xs = []
    ys = []
    for polygon in multipolygon_coords:
        for ring in polygon:
            for x, y in ring:
                xs.append(x)
                ys.append(y)
    if not xs:
        return None, None
    return sum(ys) / len(ys), sum(xs) / len(xs)  # return (lat, lon) to match CSV order

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

# ---------- build planning-area table with polygons ----------
def build_planning_areas(search_results):
    rows = []
    for item in search_results:
        name = item.get("pln_area_n")
        geojson_str = item.get("geojson")
        if not name or not geojson_str:
            continue
        try:
            geo = json.loads(geojson_str)
        except Exception:
            # some items may double-encode the JSON string
            try:
                geo = json.loads(json.loads(geojson_str))
            except Exception:
                continue
        # expect MultiPolygon / Polygon structure
        coords = None
        if isinstance(geo, dict) and geo.get("type") in ("MultiPolygon", "Polygon"):
            coords = geo.get("coordinates")
            if geo.get("type") == "Polygon" and coords:
                # normalize Polygon -> MultiPolygon-like structure: [ polygon ]
                coords = [coords]
        elif isinstance(geo, dict) and geo.get("geometry"):
            g = geo["geometry"]
            if g.get("type") in ("MultiPolygon", "Polygon"):
                coords = g.get("coordinates")
                if g.get("type") == "Polygon" and coords:
                    coords = [coords]
        if not coords:
            continue
        # coords is now list of polygons; each polygon is list of rings; rings are lists of [lon, lat]
        rows.append({
            "planning_area": name.strip().upper(),
            "multipolygon_coords": coords
        })
    return pd.DataFrame(rows)

# ---------- cleaner logic ----------
def assign_town(row, pa_df, pa_set):
    raw = row.get("town", "")
    lat = row.get("latitude", None)
    lon = row.get("longitude", None)
    if pd.isna(raw):
        raw = ""
    s = str(raw).strip()
    # if no separators, normalize and return (if not found we still keep normalized)
    if ("," not in s) and ("/" not in s):
        nm = s.upper()
        return nm if nm in pa_set else nm

    # tokenize by comma or slash (choose the one present)
    sep = "," if "," in s else "/"
    tokens = [t.strip().upper() for t in s.split(sep) if t.strip()]

    # 1) exact token match
    for t in tokens:
        if t in pa_set:
            return t

    # 2) point-in-polygon using lat/lon (requires valid numbers)
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except Exception:
        lat_f = lon_f = None

    if lat_f is not None and lon_f is not None:
        for _, pa in pa_df.iterrows():
            if point_in_multipolygon(lon_f, lat_f, pa["multipolygon_coords"]):
                return pa["planning_area"]

    # 3) fallback: nearest planning area by centroid distance
    # compute centroids if not present
    centroids = []
    for _, pa in pa_df.iterrows():
        c_lat, c_lon = polygon_centroid_from_coords(pa["multipolygon_coords"])
        if c_lat is not None:
            centroids.append((pa["planning_area"], c_lat, c_lon))
    if lat_f is not None and lon_f is not None and centroids:
        nearest = min(centroids, key=lambda c: haversine(lat_f, lon_f, c[1], c[2]))
        return nearest[0]
    # final fallback: return first token or original normalized
    return tokens[0] if tokens else s.upper()

# ---------- main logic ----------
search_results = api_data['SearchResults']
pa_df = build_planning_areas(search_results)
if pa_df.empty:
    raise RuntimeError("No planning areas parsed")
pa_set = set(pa_df["planning_area"])
df = pd.read_csv("property_database_v3.csv")
df["town"] = df.apply(lambda r: assign_town(r, pa_df, pa_set), axis=1)
df.to_csv("property_database_v4.csv", index=False)
print("Saved property_database_v4.csv")
