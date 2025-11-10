import pandas as pd
from model_v2 import PropertySupportBot

# This file is for testing the PropertySupportBot with various queries and collecting the responses.

# Initialize the PropertySupportBot
support_bot = PropertySupportBot()

# Read the question-answer pairs
df = pd.read_csv("./question_answer_pair/qa_pair_model_test_results_v5.csv", encoding="ISO-8859-1")

# Test various query types
test_queries = df["template_qn"].tolist()

# Test specific questions for result collection
# test_queries = [
#    "Do I need to pay for repairs in my rental unit?",
#    "I am renting a landed house currently. Can I use the unit to conduct my home business?",
#    "I am renting a condominium unit. Am I allowed to keep pets?",
#    "Am I allowed to cook in the house?",
#    "Who is responsible for servicing and maintaining the air-con?",
#    "Who should be responsible for paying the condo management fees?",
#    "I am a foreigner and have just lost my job. However, my rental period has not finished but my work permit will be expiring. How can I terminate my rental agreement and are there any penalties?",
#    "What is the interest rate for late payment of rent?",
#    "I'm currently bankrupt and unable to pay the rent that I have owed, can I still stay at the premises and what do I have to do?"
#]

# Initialize a counter for the queries
i = 0

for query in test_queries:
    print(f"{'='*60}")
    print("PROCESSING NEW QUERY...")
    print(f"{'='*60}")
        
    result = support_bot.process_query(query)
    
    # Handle both dict and string responses
    if isinstance(result, dict):
        df.at[i, 'model_ans'] = result.get('output') or result.get('result') or result.get('message', 'No response')
    else:
        df.at[i, 'model_ans'] = result  # assume it's a plain string
    i += 1

# Save the updated dataframe to a new CSV file
df.to_csv("./question_answer_pair/qa_pair_model_test_results_v5.1.csv", index=False)
