import pandas as pd

# Read the CSV file containing condo/apt property data and store as a DataFrame
df = pd.read_csv('combined_private_apt_condo_transactions.csv')

# Cleaning duplicate entries if they have the same Project Name, Street Name and Floor Level
duplicates = df[df.duplicated(subset=['Project Name', 'Street Name', 'Floor Level'], keep=False)]
# print("Duplicate entries:")
# print(duplicates)
df_cleaned = df.drop_duplicates(subset=['Project Name', 'Street Name', 'Floor Level'], keep='first')
print("\nDataFrame after removing duplicates:")
print(df_cleaned.shape)

# Create a new DataFrame to store the new data columns for subsequent arrangement in the same format as HDB flat data
new_df = pd.DataFrame()

# Create a Mapping dictionary to map town codes to town names
town_mapping = {
    '1': "Raffles Place, Cecil, Marina, People's Park",
    '2': "Anson, Tanjong Pagar",
    '3': "Queenstown, Tiong Bahru",
    '4': "Telok Blangah, Harbourfront",
    '5': "Pasir Panjang, Hong Leong Garden, Clementi New Town",
    '6': "High Street, Beach Road",
    '7': "Middle Road, Golden Mile",
    '8': "Little India",
    '9': "Orchard, Cairnhill, River Valley",
    '10': "Ardmore, Bukit Timah, Holland Road, Tanglin",
    '11': "Watten Estate, Novena, Thomson",
    '12': "Balestier, Toa Payoh, Serangoon",
    '13': "Macpherson, Braddell",
    '14': "Geylang, Eunos",
    '15': "Katong, Joo Chiat, Amber Road",
    '16': "Bedok, Upper East Coast, Eastwood, Kew Drive",
    '17': "Loyang, Changi",
    '18': "Tampines, Pasir Ris",
    '19': "Serangoon Garden, Hougang, Punggol",
    '20': "Bishan, Ang Mo Kio",
    '21': "Upper Bukit Timah, Clementi Park, Ulu Pandan",
    '22': "Jurong",
    '23': "Hillview, Dairy Farm, Bukit Panjang, Choa Chu Kang",
    '24': "Lim Chu Kang, Tengah",
    '25': "Kranji, Woodgrove",
    '26': "Upper Thomson, Springleaf",
    '27': "Yishun, Sembawang",
    '28': "Seletar",
}

# Function to map each town name in the list
def map_town_name(town_code):
    return town_mapping.get(str(town_code), town_code)

# Function to map floor area to number of rooms as data does not contain flat type. Values are ranges observed from HDB data.
def map_floor_area_to_rooms(floor_area):
    if pd.isna(floor_area):
        return 'Unknown'
    try:
        area = float(floor_area)
        if area < 40:
            return '1 ROOM'
        elif 40 <= area < 50:
            return '2 ROOM'
        elif 50 <= area < 80:
            return '3 ROOM'
        elif 80 <= area < 110:
            return '4 ROOM'
        elif 110 <= area < 130:
            return '5 ROOM'
        elif 130 <= area < 200:
            return 'EXECUTIVE'
        else:
            return 'MANSIONETTE'
    except ValueError:
        return 'Unknown'

# Function to extract lease commence date from tenure
def extract_lease_commence_date(tenure):
    if pd.isna(tenure):
        return None
    try:
        # Extract the last 4 digits as year from tenure in the format "99 years from 2000"
        parts = tenure.split('from')
        if len(parts) == 2:
            year_part = parts[1].strip()
            year = int(year_part)
            return year
        else:
            return 'Freehold'
    except ValueError:
        return None

# Populate the new DataFrame with the required columns in the same format as HDB flat data
new_df['town'] = df_cleaned['Postal District'].apply(map_town_name) # Map town codes to town names
new_df['flat_type'] = df_cleaned['Area (SQM)'].apply(map_floor_area_to_rooms)
new_df['block / building'] = df_cleaned['Project Name']
new_df['street_name'] = df_cleaned['Street Name']
new_df['storey'] = df_cleaned['Floor Level'].str[:2]
new_df['floor_area_sqm'] = df_cleaned['Area (SQM)']
new_df['flat_model'] = df_cleaned['Property Type']
new_df['lease_commence_date'] = df_cleaned['Tenure'].apply(extract_lease_commence_date)
new_df['rental_date'] = pd.to_datetime(df_cleaned['Sale Date'], format='%b-%y').dt.strftime('%Y-%m-%d')
new_df['property_type'] = 'Condo / Private Apartment'

print(new_df.head())

# Save the cleaned dataframe to a new csv file
new_df.to_csv('privateaptcondodata_cleaned.csv', index=False)
print("Cleaned data saved to 'privateaptcondodata_cleaned.csv'")