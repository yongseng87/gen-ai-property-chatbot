import pandas as pd

# Read the CSV file containing HDB flat data and store as a DataFrame
df = pd.read_csv('publicflatdata.csv')

# Cleaning duplicate entries if they have the same block, street_name and storey_range
duplicates = df[df.duplicated(subset=['block', 'street_name', 'storey_range'], keep=False)]
# print("Duplicate entries:")
# print(duplicates)
df_cleaned = df.drop_duplicates(subset=['block', 'street_name', 'storey_range'], keep='first')
print("\nDataFrame after removing duplicates:")
print(df_cleaned.shape)

# Data processing to clean and format the DataFrame

# Delete the text in the column 'storey_range' after the first two characters
df_cleaned = df_cleaned.copy()
df_cleaned['storey_range'] = df_cleaned['storey_range'].str[:2]

# Rename column name 'storey_range' to 'storey'
df_cleaned = df_cleaned.rename(columns={'storey_range': 'storey'})

# Rename column name 'block' to 'block / building'
df_cleaned = df_cleaned.rename(columns={'block': 'block / building'})

# Drop the column named 'remaining_lease'
df_cleaned = df_cleaned.drop(columns=['remaining_lease'])

# Create a new column named 'property_type' and assign the value 'HDB Flat' to all records as identifier
df_cleaned['property_type'] = 'HDB Flat'

# Save the cleaned dataframe to a new csv file
df_cleaned.to_csv('publicflatdata_cleaned.csv', index=False)
print("Cleaned data saved to 'publicflatdata_cleaned.csv'")