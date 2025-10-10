import pandas as pd
import numpy as np
from tenancy_agreement_generator import generate_tenancy_agreement

# Read the property database CSV file
df = pd.read_csv('property_database.csv')

# Filter the dataframe to include only rented properties
rented_df = df[df['rental_status'] == 'Rented'].reset_index(drop=True)

# Set a random seed for reproducibility
np.random.seed(123)

# Run a loop over each row of rented_df to generate tenancy agreements
for i in range(len(rented_df)):
    property_type = rented_df.loc[i, 'property_type'].upper().replace('_', ' ')
    ref_no = i + 1  # Set a running Reference number starting from 1 for each tenancy agreement
    landlord_name = rented_df.loc[i, 'owner_name']
    tenant_name = rented_df.loc[i, 'tenant_name']
    # Generate a random property address based on property type by concatenating relevant columns with randomised dummy data
    if rented_df.loc[i, 'property_type'] == 'Landed':
        property_address = f"{np.random.randint(1,21)} {rented_df.loc[i, 'street_name']}, Singapore {np.random.randint(100000, 700000)}"
    elif rented_df.loc[i, 'property_type'] == 'Condo / Private Apartment':
        property_address = f"{rented_df.loc[i, 'block / building']}, {rented_df.loc[i, 'street_name']}, #{rented_df.loc[i, 'storey']}-{rented_df.loc[i, 'storey']}, Singapore {np.random.randint(100000, 700000)}"
    else:
        property_address = f"{rented_df.loc[i, 'block / building']} {rented_df.loc[i, 'street_name']}, #{rented_df.loc[i, 'storey']}-{rented_df.loc[i, 'storey']}, Singapore {np.random.randint(100000, 700000)}"
    rental_price = rented_df.loc[i, 'rental_price']
    rental_type = rented_df.loc[i, 'rental_type']
    # print(property_type, '|', rental_type, '|', property_address, '|', rental_price)

    generate_tenancy_agreement(property_type, rental_type, ref_no, landlord_name, tenant_name, property_address, rental_price)
    print(f"Generated tenancy agreement for {tenant_name} at {property_address}")


