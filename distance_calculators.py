import requests 
import time 
from tqdm import tqdm 
import pandas as pd
import numpy as np
import os
import re
import json

#Load main dataset
df = pd.read_csv("property_database.csv")

#Prepare a dataset of unique Project Name and Street Name combinations, to reduce number of API calls
df['address'] = df['block / building'] + " " + df['street_name']
unique_addresses = df['address'].drop_duplicates().reset_index(drop=True)

auth_token = os.getenv("OneMapAuthToken")

# Load existing cache if available 

try: 
    cache_df = pd.read_csv("geocoded_addresses.csv") 
except FileNotFoundError: 
    cache_df = pd.DataFrame(columns=["address", "latitude", "longitude"]) 

# Build a set for fast lookup 
cached_set = set(cache_df['address']) 

# Define geocoding function 
def get_lat_lng(address): 
    url = f"https://www.onemap.gov.sg/api/common/elastic/search?searchVal={address}&returnGeom=Y&getAddrDetails=Y&pageNum=1" 
    headers = {"Authorization": auth_token} 
    try: 
        response = requests.get(url, headers=headers, timeout=5) 
        data = response.json() 
        if "results" in data and len(data["results"]) > 0: 
            result = data["results"][0] 
            return result.get("LATITUDE"), result.get("LONGITUDE") 
        else: return None, None 

    except Exception as e: print(f"Error fetching {address}: {e}") 
    return None, None 

# Geocode only missing addresses 
 
new_entries = [] 

for addr in tqdm(unique_addresses): 
    if addr in cached_set: 
        # Already cached → skip 
        continue 
    
    lat, lng = get_lat_lng(addr) 
    new_entries.append({"address": addr, "latitude": lat, "longitude": lng}) 
    
    # Optional: sleep to respect API rate limits 
    time.sleep(0.1) 
    
# Update cache 
if new_entries:
    new_df = pd.DataFrame(new_entries)
    cache_df = pd.concat([cache_df, new_df], ignore_index=True)
    cache_df.to_csv("geocoded_addresses.csv", index=False)

# Merge cache back with all addresses 
all_addresses = pd.DataFrame({"address": unique_addresses}) 
all_addresses = all_addresses.merge(cache_df, on="address", how="left") 

# Second pass: retry failed with Street Name only

failed_idx = all_addresses[all_addresses['latitude'].isna() | all_addresses['longitude'].isna()].index

for idx in tqdm(failed_idx):
    street_only = df.loc[df['address'] == all_addresses.at[idx, 'address'], 'street_name'].values[0]

    # Check if cache has valid coordinates
    cached_row = cache_df.loc[cache_df['address'] == street_only]
    if not cached_row.empty and pd.notna(cached_row['latitude'].values[0]) and pd.notna(cached_row['longitude'].values[0]):
        lat, lng = cached_row['latitude'].values[0], cached_row['longitude'].values[0]
    else:
        # Call API since cache is missing or invalid
        lat, lng = get_lat_lng(street_only)

        # Ensure scalars
        if isinstance(lat, (tuple, list)):
            lat = lat[0] if lat else None
        if isinstance(lng, (tuple, list)):
            lng = lng[0] if lng else None

        # Append to cache safely
        cache_df = pd.concat([cache_df, pd.DataFrame([{
            "address": street_only,
            "latitude": lat,
            "longitude": lng
        }])], ignore_index=True)

        cache_df.to_csv("geocoded_addresses.csv", index=False)

    all_addresses.at[idx, 'latitude'] = lat
    all_addresses.at[idx, 'longitude'] = lng


#Measure travel distance to CBD using OSRM API

# Path to travel distance cache
CACHE_FILE = "travel_distance_cache.csv"

# Load existing cache if available
try:
    dist_cache = pd.read_csv(CACHE_FILE)
except FileNotFoundError:
    dist_cache = pd.DataFrame(columns=["address", "dist_to_CBD_km_osrm"])

cached_set = set(dist_cache['address'])

CBD_LAT = 1.283871989921002
CBD_LON = 103.85149113157198

CBD = (CBD_LON, CBD_LAT)  # (lon, lat)

def get_osrm_distance(lon, lat, retries=3):
    url = f"http://router.project-osrm.org/route/v1/driving/{CBD[0]},{CBD[1]};{lon},{lat}?overview=false"
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=5).json()
            if 'routes' in r and len(r['routes']) > 0:
                distance_m = r['routes'][0]['distance']
                return distance_m / 1000 # km
        except Exception as e:
            print(f"Error fetching {lon},{lat}: {e}, retry {attempt+1}")
            time.sleep(1)
    return None, None

new_entries = []

unique_locations = all_addresses[['address', 'latitude', 'longitude']].drop_duplicates()

for _, row in tqdm(unique_locations.iterrows(), total=len(unique_locations)):
    addr = row['address']
    lon, lat = row['longitude'], row['latitude']
    
    if addr in cached_set or pd.isna(lon) or pd.isna(lat):
        continue
    
    dist_km = get_osrm_distance(lon, lat)
    new_entries.append({"address": addr, "dist_to_CBD_km_osrm": dist_km})
    cached_set.add(addr)
    
    time.sleep(0.1)  # optional: avoid throttling

if new_entries:
    new_df = pd.DataFrame(new_entries)
    dist_cache = pd.concat([dist_cache, new_df], ignore_index=True)
    dist_cache.to_csv(CACHE_FILE, index=False)

# --- Merge cache back to main DataFrame ---
all_addresses = all_addresses.merge(
    dist_cache[['address', 'dist_to_CBD_km_osrm']],
    on='address',
    how='left',
    suffixes=('', '_drop')
)

# Drop duplicate columns if any (from previous merges)
all_addresses = all_addresses.loc[:, ~all_addresses.columns.str.endswith('_drop')]


#Convert school postal codes to latitudes and longitudes, using OneMap API

auth_token = os.getenv("OneMapAuthToken")

# --- Load school CSV ---
schools_df = pd.read_csv("Generalinformationofschools.csv")
schools_df['postal_code'] = schools_df['postal_code'].astype(str).str.zfill(6)

# --- Load existing cache if available ---
try:
    cache_df = pd.read_csv("school_geocoded_postal_cache.csv")
except FileNotFoundError:
    cache_df = pd.DataFrame(columns=["postal_code", "latitude", "longitude"])

# Ensure postal codes are strings with leading zeros if necessary
# --- Build a set for fast lookup ---
cache_df['postal_code'] = cache_df['postal_code'].astype(str).str.zfill(6)
cached_set = set(cache_df['postal_code'])

# --- Geocoding function ---
def get_lat_lng(postal_code):
    url = f"https://www.onemap.gov.sg/api/common/elastic/search?searchVal={postal_code}&returnGeom=Y&getAddrDetails=Y&pageNum=1"
    headers = {"Authorization": auth_token}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        if "results" in data and len(data["results"]) > 0:
            result = data["results"][0]
            return result.get("LATITUDE"), result.get("LONGITUDE")
        else:
            return None, None
    except Exception as e:
        print(f"Error fetching {postal_code}: {e}")
        return None, None

# --- Geocode only missing postal codes ---
new_entries = []

for pc in tqdm(schools_df['postal_code']):
    if pc in cached_set:
        continue
    
    lat, lng = get_lat_lng(pc)
    new_entries.append({"postal_code": pc, "latitude": lat, "longitude": lng})
    cached_set.add(pc)
    
    time.sleep(0.1)  # optional: avoid rate limits

# --- Update cache ---
if new_entries:
    new_df = pd.DataFrame(new_entries)
    cache_df = pd.concat([cache_df, new_df], ignore_index=True)
    cache_df.to_csv("school_geocoded_postal_cache.csv", index=False)

# --- Merge cache back to schools DataFrame ---
schools_df = schools_df.merge(
    cache_df,
    left_on='postal_code',
    right_on='postal_code',
    how='left'
)

# --- Second pass: retry failed with School Name only ---
# Identify rows where latitude or longitude is missing
failed_idx = schools_df[schools_df['latitude'].isna() | schools_df['longitude'].isna()].index

for idx in tqdm(failed_idx):
    school_name = schools_df.at[idx, 'school_name']

    # Check if cache has valid coordinates
    cached_row = cache_df.loc[cache_df['school_name'] == school_name]
    if not cached_row.empty and pd.notna(cached_row['latitude'].values[0]) and pd.notna(cached_row['longitude'].values[0]):
        lat, lng = cached_row['latitude'].values[0], cached_row['longitude'].values[0]
    else:
        # Call API since cache is missing or invalid
        lat, lng = get_lat_lng(school_name)

        # Ensure scalars (sometimes API returns tuple/list)
        if isinstance(lat, (tuple, list)):
            lat = lat[0] if lat else None
        if isinstance(lng, (tuple, list)):
            lng = lng[0] if lng else None

        # Append to cache safely
        cache_df = pd.concat([cache_df, pd.DataFrame([{
            "school_name": school_name,
            "latitude": lat,
            "longitude": lng
        }])], ignore_index=True)

        # Save updated cache
        cache_df.to_csv("school_geocoded_postal_cache.csv", index=False)

    # Update the main DataFrame

    schools_df.at[idx, 'latitude'] = lat
    schools_df.at[idx, 'longitude'] = lng

schools_df['school_name'] = schools_df['school_name_y'].combine_first(schools_df['school_name_x'])
schools_df = schools_df.drop(columns=['school_name_x', 'school_name_y'])

# Convert latitude and longitude to numeric, in case there are any non-numeric values
schools_df['latitude'] = pd.to_numeric(schools_df['latitude'], errors='coerce')
schools_df['longitude'] = pd.to_numeric(schools_df['longitude'], errors='coerce')

# Ensure numeric types
all_addresses['latitude'] = pd.to_numeric(all_addresses['latitude'], errors='coerce')
all_addresses['longitude'] = pd.to_numeric(all_addresses['longitude'], errors='coerce')

# Vectorized Haversine function
def haversine_vec(lat1, lon1, lat2_arr, lon2_arr):
    lat1, lon1 = np.radians(lat1), np.radians(lon1)
    lat2, lon2 = np.radians(lat2_arr), np.radians(lon2_arr)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return 6371 * c  # distance in km

# Prepare arrays
prop_lat = all_addresses['latitude'].values
prop_lon = all_addresses['longitude'].values
school_lat = schools_df['latitude'].values
school_lon = schools_df['longitude'].values

# Initialize lists
nearest_school_dist = []
nearest_school_name = []

# Loop through each property
for lat_p, lon_p in zip(prop_lat, prop_lon):
    distances = haversine_vec(lat_p, lon_p, school_lat, school_lon)
    min_idx = distances.argmin()  # nearest school index
    
    nearest_school_dist.append(distances[min_idx])
    nearest_school_name.append(schools_df.loc[min_idx, 'school_name'])

# Add columns to all_addresses
all_addresses['nearest_school_dist_km'] = nearest_school_dist
all_addresses['nearest_school_name'] = nearest_school_name


# Load GeoJSON
with open("LTAMRTStationExitGEOJSON.geojson", "r") as f:
    geojson_data = json.load(f)

features = geojson_data['features']

mrt_list = []
pattern = r"<th>STATION_NA<\/th>\s*<td>(.*?)<\/td>"

for feat in features:
    coords = feat['geometry']['coordinates']  # [lon, lat, ...]
    desc = feat['properties']['Description']
    
    match = re.search(pattern, desc)
    station_name = match.group(1) if match else None
    
    mrt_list.append({
        'mrt_lon': coords[0],
        'mrt_lat': coords[1],
        'StationName': station_name
    })

mrt_df = pd.DataFrame(mrt_list)

mrt_df['mrt_lat'] = pd.to_numeric(mrt_df['mrt_lat'], errors='coerce')
mrt_df['mrt_lon'] = pd.to_numeric(mrt_df['mrt_lon'], errors='coerce')

# Calculate nearest MRT station for each property, as well as distance
nearest_mrt_dist = []
nearest_mrt_name = []

mrt_lat = mrt_df['mrt_lat'].values
mrt_lon = mrt_df['mrt_lon'].values

for lat_p, lon_p in zip(prop_lat, prop_lon):
    distances = haversine_vec(lat_p, lon_p, mrt_lat, mrt_lon)
    min_idx = distances.argmin()
    nearest_mrt_dist.append(distances[min_idx])
    nearest_mrt_name.append(mrt_df.loc[min_idx, 'StationName'])

all_addresses['nearest_mrt_dist_km'] = nearest_mrt_dist
all_addresses['nearest_mrt_name'] = nearest_mrt_name

df = df.merge(all_addresses, on='address', how='left')
