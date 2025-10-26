import os
import json
import asyncio
from openai import AsyncClient
import pandasql as psql
import pandas as pd
import sys
from langchain_experimental.agents.agent_toolkits.pandas.base import create_pandas_dataframe_agent


csv_query_prompt = """
You are a helpful AI assistant that helps people find information about properties from a CSV file. 

The CSV file has the following columns:

Columns - Description -  Data Type  - Example Values
town - The area/region where the property is located, town names might be a substring of the full address - string - "YISHUN", "TOA PAYOH", "CLEMENTI"
flat_type - The type of the entire property. "room" and "bedroom" can be interchanged. - string - "4 ROOM", "5 ROOM", "EXECUTIVE"
block - The block number of the property if it is a HDB flat, or the development name if it is a condo/private property, or just "LANDED HOUSING DEVELOPMENT" if the property is a landed house and does not have a block number / development name - string - "123", "456A", "SUNNYVALE CONDO", "LANDED HOUSING DEVELOPMENT"
street_name - The street name where the property is located - string - "YISHUN AVENUE 6", "TOA PAYOH CENTRAL", "CLEMENTI ROAD"
storey - The storey of the property, for landed house this column is default to 0 - integer - 1, 5, 12
floor_area_sqm - The floor area of the property in square meters - float - 45.0, 75.5, 120.0
flat_model - The model/type of the flat - string - "IMPROVED", "MODEL A", "DBSS"
lease_commence_year - The year the lease of the property commenced, for freehold properties this is the year the property was built - integer - 1995, 2003, 2010
rental_date - The date when the property was rented out, and empty value means the unit is still available - date - "2020-05-01", "2021-12-15"
property_type - The type of property, one of "HDB Flat", "Condo / Private Apartment", "Landed" - string - "HDB Flat", "Condo / Private Apartment", "Landed"
rental_type - the type of the unit for rental, if this column matches flat_type, the entire property is considered for rental. "room" and "bedroom" can be interchanged. Search this field first for user queries unless specified that entire property is considered, and if not available search flat_type - string - "1 BEDROOM", "5 ROOM"
rental_price - The monthly rental price of the property in Singapore Dollars - integer - 1500, 3000, 4500
owner_name - The name of the property owner - string - "John Tan", "Siti Binte Ahmad"
rental_status - The rental status of the property, either "RENTED" or "AVAILABLE" - string - "RENTED", "AVAILABLE"
tenant_name - The name of the tenant renting the property, empty value means no tenant - string - "Michael Lee", "Alicia Wong"
address - The full address of the property - string - "301 HOUGANG AVE 5", "45 CLEMENTI ROAD"
latitude - The latitude coordinate of the property location - float - 1.3521, 1.2905
longitude - The longitude coordinate of the property location - float - 103.8198, 103.8519
dist_to_CBD_km_osrm - The distance in kilometers from the property to the Central Business District (CBD) calculated using OSRM - float - 10.583, 15.227
nearest_school_dist_km - The distance in kilometers from the property to the nearest school - float - 0.5, 2.3
nearest_school_name - The name of the nearest school to the property - string - "NAVAL BASE SECONDARY SCHOOL", "CLEMENTI PRIMARY SCHOOL"
nearest_mrt_dist_km - The distance in kilometers from the property to the nearest MRT station - float - 0.8, 1.5
nearest_mrt_name - The name of the nearest MRT station to the property - string - "KOVAN MRT STATION", "CLEMENTI MRT STATION"

"""


def create_csv_agent(csv_path, llm):
    """Create agent for CSV documents"""
    
    df = pd.read_csv(csv_path)
    agent = create_pandas_dataframe_agent(
        llm=llm,
        df=df,
        verbose=True,
        agent_type="openai-tools",
        allow_dangerous_code=True,
        prefix=csv_query_prompt, 
        suffix="Use the provided data to answer the questions. Provide the final answer in a clear and structured format."
    )
    print("✅ CSV Agent created successfully")
    return agent



# async def generate_sql_query(user_request: str, openai_api_key: str) -> str:
#     """Generate SQL query from user request using OpenAI API"""
    
#     client = AsyncClient(api_key=openai_api_key)
        
#     response = await client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {"role": "system", "content": sql_query_prompt},
#             {"role": "user", "content": str(user_request)},
#         ],
#         temperature=0.0,
#     )
    
#     sql_query = response.choices[0].message.content.strip()
#     cleaned_response = sql_query.replace("```sql", "").replace("```", "").strip()
#     await client.close()
#     return cleaned_response


# def execute_sql_query(df, sql_query: str):
#     """Execute SQL query on the dataframe and return results"""
#     local_vars = {'df': df}
#     result_df = psql.sqldf(sql_query, local_vars)
#     result_markdown = result_df.to_markdown(index=False)
#     return result_markdown