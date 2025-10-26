import json
import os
from openai import AsyncClient

MODULE_DESCRIPTION = """
information_retrieval

This module handles messages related to information retrieval, which can include:
- Requests for information on tenancy agreements, lease terms, and rental policies
- Any queries related to property management, maintenance, or repair responsibilities
- Any queries related to tenant rights and obligations
- Any queries related to rental payment terms, late fees, and deposit handling
- Any queries related to lease renewal, termination, and notice periods
- Any queries related to subletting, guest policies, and property rules
- Any queries related to comparison of different property types and their tenancy terms

property_data_analysis

This module handles messages related to inventory management, which can include:
- Queries about property transaction history, including regions, unit types, unit features and rental pricing
- Requests for analysis of market trends based on historical transaction data
- Queries regarding availability of properties based on specific criteria such as location, unit type, and features
- Inquiries about rental pricing trends and comparisons for different property types and features
- Queries about historical rental data for specific properties or regions
- Requests for summaries of transaction data for reporting purposes
- Requests for insights into popular property features and unit types based on transaction history
- Requests for assistance in identifying suitable properties based on user-defined criteria
"""

CONTEXT = (
    "You are going to assist the chatbot by doing the following tasks:\n"
    "1. For each incoming query, classify it into one of the following modules, or None if no match is found:\n"  # noqa: E501
    f"{MODULE_DESCRIPTION}\n"
    "Do not guess any module on your own. Just extract it.\n"
    "Strictly classify each query into only one report or None. DO NOT GUESS\n"
    "Your Json response should look like this:\n"
    "{'classifications': [{'module': 'assigned report or None', 'reason': 'why this module was chosen or why no module was assigned'}]}\n"  # noqa: E501
    "Note: Each sub-query should be strictly classified into only one module or None."
)

EXAMPLES = """
Example 1 - information_retrieval Messages:
{"user_message": ['What is the diplomatic clause?', 'Who needs to pay to repair when things are broken?', 'What are the different terms of tenancy between condo and HDB flat?']}
{
  'classifications': [
    {
      'module': 'information_retrieval',
      'reason': 'The user is inquiring about terms in a tenancy agreement about diplomatic clause.'
    },
    {
      'module': 'information_retrieval',
      'reason': 'The user is inquiring about repair responsibilities outlined in a tenancy agreement.'
    },
    {
      'module': 'information_retrieval',
      'reason': 'The user is inquiring about the difference between property types in terms of tenancy terms.'
    }
  ]
}

Example 2 - property_data_analysis Messages:
{"user_message": ["What is the average price of 1 Bedroom condo in different regions?", 'If I want a 2 Bedroom HDB flat built after 2010, which regions should I consider?']}
{
  'classifications': [
    {
      'module': 'property_data_analysis',
      'reason': 'The user is inquiring about the price of 1 Bedroom confo flats in different regions.'
    },
    {
      'module': 'property_data_analysis',
      'reason': 'The user is inquiring about possible areas with properties matching the criteria.'
    }
  ]
}

Example 3 - None Messages:

{"user_message": ['What is real estate', 'I want to invest in stocks']}
{
  'classifications': [
    {
      'module': 'None',
      'reason': 'The user is inquiring about real estate which is not related to information retrieval or property data analysis.'
    },
    {
      'module': 'None',
      'reason': 'The user is inquiring about investing in stocks which is not related to information retrieval or property data analysis.'
    }
  ]
}
"""


async def classify(query):
    """Asynchronously classifies a given query using the OpenAI API.

    Args:
        query (str): The query to be classified.
        phone_number (str): The phone number of the user.

    Returns:
        dict: The classification result in JSON format.

    Raises:
        None
    """
    messages = [
        {"role": "system", "content": CONTEXT + EXAMPLES},
        {"role": "user", "content": str(query)},
    ]
    model = "gpt-4o-mini"
    try:
        async_client = AsyncClient(
            api_key=os.getenv("OPENAI_API_KEY")
        )

        # Request a completion from the OpenAI API
        response = await async_client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        response = json.loads(response.choices[0].message.content)
        await async_client.close()
        print(f"Classification result: {response['classifications'][0]['module']}")
        print(f"Reason: {response['classifications'][0]['reason']}")
        return response
    except Exception as e:
        print(f"Exception occured while creating metadata: {e}")
        raise (e)
    
if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()

    test_queries = [
        "What is the minimum notice period for lease termination?",
        "Show me the rental price trends for 2 Bedroom HDB flats in Jurong East.",
        "How to invest in real estate?",
    ]

    for query in test_queries:
        asyncio.run(classify(query))