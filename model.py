import os
import warnings
from dotenv import load_dotenv
import asyncio
import pandas as pd

# LangChain Core
from langchain_openai import ChatOpenAI

# Memory & Chains
from langchain.memory import ConversationBufferMemory
from langchain.chains import RetrievalQA

# Retrieval & Vector Stores
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.agents.agent_toolkits.pandas.base import create_pandas_dataframe_agent
from langchain_community.document_loaders import PyPDFLoader

from classifier import classify

# Suppress warnings
warnings.filterwarnings('ignore')

def load_and_process_pdf(pdf_path):
    """Load PDF and process it for Chroma DB"""
    # Knowledge base
    # Load and process multiple PDFs from the examples folder
    pdf_folder = pdf_path
    pdf_files = [os.path.join(pdf_folder, file) for file in os.listdir(pdf_folder) if file.endswith(".pdf")]
    
    all_docs = []
    for pdf_file in pdf_files:
        print(f"Processing file: {pdf_file}")
        loader = PyPDFLoader(pdf_file)
        pages = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        )
        docs = text_splitter.split_documents(pages)
        all_docs.extend(docs)
    
    print(f"📝 Total text chunks from all PDFs: {len(all_docs)}")
    
    # Create embeddings
    embeddings_pdf = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
    
    # Clear any existing chroma database (commented out to prevent errors on rerun)
    db_path = "./pdf_knowledge_base"
    # if os.path.exists(db_path):
    #     shutil.rmtree(db_path)
    #     print("🧹 Cleared existing database")
    
    # Create Chroma vector store
    print("🔍 Creating vector embeddings...")
    vectorstore_pdf = Chroma.from_documents(
        documents=all_docs,
        embedding=embeddings_pdf,
        persist_directory=db_path)
    
    # Persist the database
    vectorstore_pdf.persist()
    print(f"💾 Vector database saved to: {db_path}")
    
    return vectorstore_pdf


def create_pdf_qa_system(vectorstore_pdf, llm):
    """Create Q&A system for PDF documents"""
    
    # Create retrieval QA chain
    qa_chain_pdf = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore_pdf.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}  # Return top 3 relevant chunks
        ),
        return_source_documents=True
    )
    
    print("✅ PDF Q&A system created successfully")
    return qa_chain_pdf


def create_csv_agent(csv_path, llm):
    """Create agent for CSV documents"""
    
    df = pd.read_csv(csv_path)
    agent = create_pandas_dataframe_agent(
        llm=llm,
        df=df,
        verbose=True,
        agent_type="openai-tools",
        allow_dangerous_code=True,
    )
    print("✅ CSV Agent created successfully")
    return agent


class PropertySupportBot:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")
            
        try:
            self.llm = ChatOpenAI(
                model="gpt-4o-mini", 
                temperature=0.1, 
                api_key=self.openai_api_key,
                max_retries=3,
                request_timeout=30
            )
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=self.openai_api_key,
                max_retries=3,
                request_timeout=30
            )
        except Exception as e:
            print(f"Error initializing OpenAI models: {e}")
            raise
        
        try:
            # Knowledge base
            self.vectorstore = load_and_process_pdf("property_data_generator")
            
            # Memory for conversations
            self.memory = ConversationBufferMemory()
            
            # QA chain for policies
            self.qa_chain = create_pdf_qa_system(self.vectorstore, self.llm)
            self.csv_agent = create_csv_agent("property_database_v2.csv", self.llm)
        except Exception as e:
            print(f"Error initializing knowledge base: {e}")
            raise
    
    def process_query(self, query: str):
        """Process user query based on category classification (synchronous version)"""
        
        print(f"🔵 INPUT TO SUPPORT BOT:")
        print(f"Query: {query}")

        try:
            # Classify the query with timeout
            try:
                # Check if we're already in an event loop
                try:
                    loop = asyncio.get_running_loop()
                    # We're in an event loop, use run_in_executor
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, asyncio.wait_for(classify(query), timeout=10.0))
                        classification = future.result(timeout=15.0)  # Give extra time for the executor
                except RuntimeError:
                    # No event loop running, safe to use asyncio.run
                    classification = asyncio.run(asyncio.wait_for(classify(query), timeout=10.0))
                
                module = classification['classifications'][0]['module']
                print(f"🎯 Classification: {module}")
            except asyncio.TimeoutError:
                print("⏰ Classification timeout, using fallback")
                module = "general_support"
            except Exception as e:
                print(f"❌ Classification error: {e}, using fallback")
                module = "general_support"
            
            if module == "information_retrieval":
                print("\n🔵 HANDLING INFORMATION RETRIEVAL QUERY...")
                try:
                    result = self.qa_chain.invoke(query)
                    print(f"Answer: {result['result']}")
                    if result.get('source_documents'):
                        print(f"📄 Sources: Page {result['source_documents'][0].metadata.get('page', 'Unknown')} of PDF")
                        print(f"📝 Source Text Preview: {result['source_documents'][0].page_content[:150]}...")
                    return result['result']
                except Exception as e:
                    print(f"❌ PDF QA error: {e}")
                    return self._fallback_response(query, "PDF knowledge base")
                    
            elif module == "property_data_analysis":
                print("\n🔵 HANDLING PROPERTY DATA ANALYSIS QUERY...")
                try:
                    result = self.csv_agent.invoke(query)
                    print(f"Analysis Result: {result['output']}")
                    return result['output']
                except Exception as e:
                    print(f"❌ CSV analysis error: {e}")
                    return self._fallback_response(query, "property data analysis")
                    
            else:
                print("\n🔵 HANDLING GENERAL QUERY...")
                try:
                    # Use simple LLM for general queries
                    response = self.llm.invoke(query)
                    return response.content
                except Exception as e:
                    print(f"❌ General query error: {e}")
                    return self._fallback_response(query, "general support")
                
        except Exception as e:
            print(f"❌ Critical error in process_query: {e}")
            return f"I apologize, but I encountered an error while processing your query: '{query}'. Please try rephrasing your question or contact support if the issue persists."

    async def process_query_async(self, query: str):
        """Process user query based on category classification (asynchronous version)"""
        
        print(f"🔵 INPUT TO SUPPORT BOT (ASYNC):")
        print(f"Query: {query}")

        try:
            # Classify the query with timeout
            try:
                classification = await asyncio.wait_for(classify(query), timeout=10.0)
                module = classification['classifications'][0]['module']
                print(f"🎯 Classification: {module}")
            except asyncio.TimeoutError:
                print("⏰ Classification timeout, using fallback")
                module = "general_support"
            except Exception as e:
                print(f"❌ Classification error: {e}, using fallback")
                module = "general_support"
            
            if module == "information_retrieval":
                print("\n🔵 HANDLING INFORMATION RETRIEVAL QUERY...")
                try:
                    # Run the synchronous invoke in a thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, self.qa_chain.invoke, query)
                    print(f"Answer: {result['result']}")
                    if result.get('source_documents'):
                        print(f"📄 Sources: Page {result['source_documents'][0].metadata.get('page', 'Unknown')} of PDF")
                        print(f"📝 Source Text Preview: {result['source_documents'][0].page_content[:150]}...")
                    return result['result']
                except Exception as e:
                    print(f"❌ PDF QA error: {e}")
                    return self._fallback_response(query, "PDF knowledge base")
                    
            elif module == "property_data_analysis":
                print("\n🔵 HANDLING PROPERTY DATA ANALYSIS QUERY...")
                try:
                    # Run the synchronous invoke in a thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, self.csv_agent.invoke, query)
                    print(f"Analysis Result: {result['output']}")
                    return result['output']
                except Exception as e:
                    print(f"❌ CSV analysis error: {e}")
                    return self._fallback_response(query, "property data analysis")
                    
            else:
                print("\n🔵 HANDLING GENERAL QUERY...")
                try:
                    # Run the synchronous invoke in a thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(None, self.llm.invoke, query)
                    return response.content
                except Exception as e:
                    print(f"❌ General query error: {e}")
                    return self._fallback_response(query, "general support")
                
        except Exception as e:
            print(f"❌ Critical error in process_query_async: {e}")
            return f"I apologize, but I encountered an error while processing your query: '{query}'. Please try rephrasing your question or contact support if the issue persists."
    
    def _fallback_response(self, query: str, context: str):
        """Provide a fallback response when API calls fail"""
        return f"I'm having trouble accessing the {context} right now. Your question '{query}' seems to be about property-related matters. Please try again in a moment, or contact our support team for immediate assistance."

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()

    # Verify API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables.")
    # Initialize the complete system
    print("🚀 Initializing Complete Property Support Bot...")
    support_bot = PropertySupportBot()

    # Test various query types
    test_queries = [
        "what is the mean price of HDB flats in Bishan?",
        "Do I need to pay for repairs in my rental unit?",
        "how to invest in stocks for beginners?",
        # "I’m renting a landed house currently. Can I use the unit to conduct my home business?",
        # "I’m renting a condominium unit. Am I allowed to keep pets?",
        # "Am I allowed to cook in the house?",
        # "Who is responsible for servicing and maintaining the air-con?",
        # "Can you recommend me an air-con cleaning contractor?",
        # "Who should be responsible for paying the condo management fees?",
        # "I’m looking for a two room HDB unit to rent in Hougang. Can you recommend me some available units with monthly rental below $2,200?",
        # "how far is the unit 998B buangkok cres away from the MRT and which station is it?",
        # "are rental prices in hougang cheaper than rental prices in punggol?",
        # "are rental prices in JB cheaper than rental prices in singapore?",
        # "what is the average rental price of landed houses in singapore?",
        # "recommend me a place to rent that is near to Toa Payoh MRT station",
        # "recommend me a place to rent that is near to Ai Tong School",
        # "I'm looking for a high floor, 2 room unit to rent in yishun. Recommend me some places",
        # "recommend me a good place to stay in singapore",
        # "I am a foreigner and have just lost my job. However, my rental period has not finished but my work permit will be expiring. How can I terminate my rental agreement and are there any penalties?",
        # "What is the interest rate for late payment of rent?",
        # "I'm currently bankrupt and unable to pay the rent that I have owed, can I still stay at the premises and what do I have to do?"
        # "what is the price difference for renting 1 bedroom in 2024 versus 2025?",
        # "what is the cheapest rental price for houses in Orchard",
        # "what is the highest rental price for a unit in Sengkang?",
        # "how many 4 room HDB units are available for rent in Bukit Merah?",
        # "what is the range of rental prices for houses in June 2024.",
        # "what is the average size of 3 room HDB flats?"        
    ]

    for query in test_queries:
        print(f"{'='*60}")
        print("PROCESSING NEW QUERY...")
        print(f"{'='*60}")
        
        support_bot.process_query(query)