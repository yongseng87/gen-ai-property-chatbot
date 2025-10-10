import pandas as pd
import numpy as np

# Set desired number of entries for creating property database
X = 10000 # For number of entries in database
Y = 100 # For number of rented entries with tenant name

# Read the cleaned CSV files for HDB, Condo/Apt, and Landed properties
hdb_df = pd.read_csv('publicflatdata_cleaned.csv')
condo_df = pd.read_csv('privateaptcondodata_cleaned.csv')
landed_df = pd.read_csv('landeddata_cleaned.csv')

# Concatenate the three dataframes
df_cleaned = pd.concat([hdb_df, condo_df, landed_df], ignore_index=True)
df_cleaned['storey'] = df_cleaned['storey'].astype(str).str.zfill(2) # Ensure storey is two digits

# Set a random seed for reproducibility
np.random.seed(123)

# Randomly choose X rows from the cleaned dataframe and reset index
df_cleaned = df_cleaned.sample(n=X, random_state=1)
print(df_cleaned.shape)
df_cleaned = df_cleaned.reset_index(drop=True)

# Function to set whether rental is based on whole unit or just 1 or 2 bedrooms
def map_flat_type_to_rental_type(flat_type):
    if pd.isna(flat_type):
        return flat_type  # Handle NaN values
    flat_type = flat_type.upper()
    if flat_type in ['1 ROOM', '2 ROOM']:
        return flat_type   # Rental type is same as flat type as unit is too small
    elif flat_type in ['3 ROOM', '4 ROOM']:
        return np.random.choice(['1 BEDROOM', flat_type])   # Randomly set as 1 bedroom or whole unit for rental
    elif flat_type in ['5 ROOM']:
        return np.random.choice(['1 BEDROOM', '2 BEDROOM', flat_type])   # Randomly set as 1 or 2 bedroom or whole unit for rental
    elif flat_type in ['EXECUTIVE', 'MANSIONETTE']:
        return flat_type   # Rental type is same as flat type as unit is large enough
    else:
        return flat_type  # Default to same rental type as flat type for unrecognized types

# Create rental_type column based on flat_type
df_cleaned['rental_type']  = df_cleaned['flat_type'].apply(map_flat_type_to_rental_type)

# Generate dummy data for nearby amenities
df_cleaned['dist_to_MRT'] = np.random.randint(100, 2001, size=len(df_cleaned))
df_cleaned['dist_to_bus'] = np.random.randint(100, 401, size=len(df_cleaned))
df_cleaned['dist_to_school'] = np.random.randint(100, 3001, size=len(df_cleaned))
df_cleaned['near_supermarket'] = np.random.choice(['TRUE', 'FALSE'], size=len(df_cleaned))
df_cleaned['near_coffeeshop'] = np.random.choice(['TRUE', 'FALSE'], size=len(df_cleaned))
df_cleaned['near_hawkercentre'] = np.random.choice(['TRUE', 'FALSE'], size=len(df_cleaned))
df_cleaned['near_park'] = np.random.choice(['TRUE', 'FALSE'], size=len(df_cleaned))

# Generate dummy data for rental price based on rental_type
ranges = {
    '1 BEDROOM': np.arange(1000, 1201, 100),
    '2 BEDROOM': np.arange(2000, 3001, 100),
    '1 ROOM': np.arange(1500, 2001, 100),
    '2 ROOM': np.arange(2000, 2501, 100),
    '3 ROOM': np.arange(3000, 3501, 100),
    '4 ROOM': np.arange(4000, 5001, 100),
    '5 ROOM': np.arange(5000, 6001, 100),
    'EXECUTIVE': np.arange(6000, 8001, 100),
    'MANSIONETTE': np.arange(8000, 12001, 100),
    'MULTI-GENERATION': np.arange(10000, 15001, 100),
    'TERRACE HOUSE': np.arange(10000, 15001, 100),
    'SEMI-DETACHED HOUSE': np.arange(15000, 20001, 100),
    'DETACHED HOUSE': np.arange(20000, 30001, 100),
}
df_cleaned['rental_price'] = df_cleaned['rental_type'].apply(lambda t: np.random.choice(ranges.get(t, [0])))

# Read names database
df_names = pd.read_csv('names_database.csv')

# Generate owner name randomly from names database
combinations_1 = set()
while len(combinations_1) < X:
    s1 = np.random.choice(df_names['first_name'])
    s2 = np.random.choice(df_names['last_name'])
    combined = s1 + ' ' + s2
    combinations_1.add(combined)
combinations_1 = list(combinations_1)
df_cleaned['owner_name'] = combinations_1

# Generate Y number of random names for tenants
combinations_2 = set()
while len(combinations_2) < Y:
    s1 = np.random.choice(df_names['first_name'])
    s2 = np.random.choice(df_names['last_name'])
    combined = s1 + ' ' + s2
    combinations_2.add(combined)
combinations_2 = list(combinations_2)

# Sets up empty columns first for rental status
df_cleaned['rental_status'] = None
df_cleaned['tenant_name'] = None

# Sets up random indices for inserting rented status into Y records with tenant name
rand_indices = np.sort(np.random.choice(X, size=Y, replace=False))

# Assign 'Rented' and tenant names using zip based on random indices
for idx, name in zip(rand_indices, combinations_2):
    df_cleaned.loc[idx, 'rental_status'] = 'Rented'
    df_cleaned.loc[idx, 'tenant_name'] = name

# Assign 'Avail' to all other rows with null values for tenant name
df_cleaned.loc[~df_cleaned.index.isin(rand_indices), 'rental_status'] = 'Avail'
df_cleaned.loc[~df_cleaned.index.isin(rand_indices), 'tenant_name'] = None
            
# Save the cleaned dataframe to a new csv file
df_cleaned.to_csv('property_database.csv', index=False)
print("Cleaned data saved to 'property_database.csv'")