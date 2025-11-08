import os
from time import time
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
from create_csv_agent import create_csv_agent

# Suppress warnings
warnings.filterwarnings('ignore')

# Load environment variables
load_dotenv()

# Verify API key
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables.")

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


def create_pdf_qa_system(vectorstore_pdf, llm, memory=None):
    """Create Q&A system for PDF documents"""
    
    # Create retrieval QA chain
    qa_chain_pdf = RetrievalQA.from_chain_type(
        llm=llm,
        memory=memory,
        chain_type="stuff",
        retriever=vectorstore_pdf.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}  # Return top 3 relevant chunks
        ),
        return_source_documents=True
    )
    
    print("✅ PDF Q&A system created successfully")
    return qa_chain_pdf



class PropertySupportBot:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")
            
        try:
            self.llm = ChatOpenAI(
                model="gpt-4o", 
                temperature=0.4, 
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
            self.memory = ConversationBufferMemory(output_key='result', memory_key='chat_history', return_messages=True)
            
            # QA chain for policies
            self.qa_chain = create_pdf_qa_system(self.vectorstore, self.llm, memory=self.memory)
            self.csv_agent = create_csv_agent("property_database_v3.csv", self.llm, memory=self.memory)
        except Exception as e:
            print(f"Error initializing knowledge base: {e}")
            raise
        
    async def process_query_async(self, query: str):
        """Process user query based on category classification (asynchronous version)"""

        print(f"🔵 INPUT TO SUPPORT BOT (ASYNC):")
        print(f"Query: {query}")

        try:
            # Step 1: Classify the query
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

            # Step 2: Route based on classification
            if module == "information_retrieval":
                print("\n🔵 HANDLING INFORMATION RETRIEVAL QUERY...")
                try:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, self.qa_chain.invoke, query)
                    print(f"Answer: {result.get('result', '')}")

                    # Format source documents
                    sources = []
                    for doc in result.get("source_documents", []):
                        sources.append({
                            "page": doc.metadata.get("page", "Unknown") + 1,  # Pages are 0-indexed
                            "preview": doc.page_content[:200] + "...",
                        })

                    if sources:
                        print(f"📄 Sources: Page {sources[0]['page']}")
                        print(f"📝 Source Text Preview: {sources[0]['preview']}")

                    return {
                        "answer": result.get("result", ""),
                        "sources": sources,
                        "type": "pdf"
                    }

                except Exception as e:
                    print(f"❌ PDF QA error: {e}")
                    return {
                        "answer": self._fallback_response(query, "PDF knowledge base"),
                        "sources": [],
                        "type": "fallback"
                    }

            elif module == "property_data_analysis":
                print("\n🔵 HANDLING PROPERTY DATA ANALYSIS QUERY...")
                try:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, self.csv_agent.invoke, query)

                    return {
                        "answer": result.get("output", ""),
                        "sources": [],
                        "type": "csv"
                    }

                except Exception as e:
                    print(f"❌ CSV analysis error: {e}")
                    return {
                        "answer": self._fallback_response(query, "property data analysis"),
                        "sources": [],
                        "type": "fallback"
                    }

            else:
                print("\n🔵 HANDLING GENERAL QUERY...")
                try:
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(None, self.llm.invoke, query)

                    return {
                        "answer": response.content,
                        "sources": [],
                        "type": "general"
                    }

                except Exception as e:
                    print(f"❌ General query error: {e}")
                    return {
                        "answer": self._fallback_response(query, "general support"),
                        "sources": [],
                        "type": "fallback"
                    }

        except Exception as e:
            print(f"❌ Critical error in process_query_async: {e}")
            return {
                "answer": f"I apologize, but I encountered an error while processing your query: '{query}'. Please try rephrasing your question or contact support if the issue persists.",
                "sources": [],
                "type": "critical"
            }

    def _fallback_response(self, query: str, context: str):
        """Provide a fallback response when API calls fail"""
        return f"I'm having trouble accessing the {context} right now. Your question '{query}' seems to be about property-related matters. Please try again in a moment, or contact our support team for immediate assistance."

if __name__ == "__main__":

    # Initialize the complete system
    print("🚀 Initializing Complete Property Support Bot...")
    support_bot = PropertySupportBot()

    # Test various query types
    test_queries = [
        "what is the mean price of HDB flats in Bishan?",
        "Do I need to pay for repairs in my rental unit?",
        "how to invest in stocks for beginners?",
    ]

    for query in test_queries:
        print(f"{'='*60}")
        print("PROCESSING NEW QUERY...")
        print(f"{'='*60}")
        
        support_bot.process_query(query)