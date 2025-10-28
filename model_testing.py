import pandas as pd
from model import PropertySupportBot

support_bot = PropertySupportBot()

# Read the question-answer pairs
df = pd.read_csv("./question_answer_pair/qa_pair_for_testing_v2.csv", encoding="ISO-8859-1")

# Test various query types
test_queries = [
    "what is the mean price of HDB flats in Bishan?",
    "Do I need to pay for repairs in my rental unit?",
    "how to invest in stocks for beginners?",
    "I’m renting a landed house currently. Can I use the unit to conduct my home business?",
    "I’m renting a condominium unit. Am I allowed to keep pets?",
    "Am I allowed to cook in the house?",
    "Who is responsible for servicing and maintaining the air-con?",
    "Can you recommend me an air-con cleaning contractor?",
    "Who should be responsible for paying the condo management fees?",
    "I’m looking for a two room HDB unit to rent in Hougang. Can you recommend me some available units with monthly rental below $2,200?",
    "how far is the unit 998B buangkok cres away from the MRT and which station is it?",
    "are rental prices in hougang cheaper than rental prices in punggol?",
    "are rental prices in JB cheaper than rental prices in singapore?",
    "what is the average rental price of landed houses in singapore?",
    "recommend me a place to rent that is near to Toa Payoh MRT station",
    "recommend me a place to rent that is near to Ai Tong School",
    "I'm looking for a high floor, 2 room unit to rent in yishun. Recommend me some places",
    "recommend me a good place to stay in singapore",
    "I am a foreigner and have just lost my job. However, my rental period has not finished but my work permit will be expiring. How can I terminate my rental agreement and are there any penalties?",
    "What is the interest rate for late payment of rent?",
    "I'm currently bankrupt and unable to pay the rent that I have owed, can I still stay at the premises and what do I have to do?"
    "what is the price difference for renting 1 bedroom in 2024 versus 2025?",
    "what is the cheapest rental price for houses in Orchard",
    "what is the highest rental price for a unit in Sengkang?",
    "how many 4 room HDB units are available for rent in Bukit Merah?",
    "what is the range of rental prices for houses in June 2024.",
    "what is the average size of 3 room HDB flats?"        
    ]

# Initialize a counter for the queries
i = 0

for query in test_queries:
    print(f"{'='*60}")
    print("PROCESSING NEW QUERY...")
    print(f"{'='*60}")
        
    result = support_bot.process_query(query)
    # Save the result to the dataframe
    df.at[i, 'model_ans'] = result.get('output', result.get('message', 'No response'))
    i += 1

# Save the updated dataframe to a new CSV file
df.to_csv("./question_answer_pair/qa_pair_model_test_results_v3.csv", index=False)
