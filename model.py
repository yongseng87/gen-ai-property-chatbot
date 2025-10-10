import os
import warnings
import json
import shutil
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, List, Optional

# LangChain Core
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Memory & Chains
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
from langchain.chains import ConversationChain, LLMChain, RetrievalQA

# Retrieval & Vector Stores
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader

# Tools & Agents
from langchain.tools import tool
from langchain.agents import initialize_agent, AgentType


# Suppress warnings
warnings.filterwarnings('ignore')

def load_and_process_pdf(pdf_path):
    """Load PDF and process it for Chroma DB"""
    
    print("📚 Loading PDF document...")
    print(f"File: {pdf_path}")
    
    # Load PDF
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    
    print(f"✅ Loaded {len(pages)} pages from PDF")
    
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    
    docs = text_splitter.split_documents(pages)
    print(f"📝 Split into {len(docs)} text chunks")
    
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
        documents=docs,
        embedding=embeddings_pdf,
        persist_directory=db_path
    )
    
    # Persist the database
    vectorstore_pdf.persist()
    print(f"💾 Vector database saved to: {db_path}")
    
    return vectorstore_pdf

def create_pdf_qa_system(vectorstore_pdf):
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

class PropertySupportBot:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, api_key=openai_api_key)
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        
        # Knowledge base
        self.vectorstore = load_and_process_pdf("examples/Track_B_Tenancy_Agreement.pdf")
        
        # Memory for conversations
        self.memory = ConversationBufferMemory()
        
        # QA chain for policies
        self.qa_chain = create_pdf_qa_system(self.vectorstore)
        
    
    def process_query(self, query: str):
        """Process user query intelligently"""
        
        print(f"🔵 INPUT TO SUPPORT BOT:")
        print(f"Query: {query}")
        
        # Simple intent detection
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["tenancy", "agreement", "terms", "contract", "conditions"]):
            # Use retrieval for policy questions
            print("🎯 Intent: Tenancy Agreement Question → Using Knowledge Base")
            print("\n🔵 SEARCHING KNOWLEDGE BASE...")
            result = self.qa_chain.invoke(query)
            print(f"Answer: {result['result']}")
            print(f"📄 Sources: Page {result['source_documents'][0].metadata.get('page', 'Unknown')} of PDF")
            print(f"📝 Source Text Preview: {result['source_documents'][0].page_content[:150]}...")
            
        else:
            # Use memory conversation for general support
            print("🎯 Intent: General Support → Using Conversation Memory")
            print("\n🔵 CALLING GPT WITH MEMORY...")
            conversation = ConversationChain(llm=self.llm, memory=self.memory)
            result = conversation.invoke({"input": query})["response"]
        
        print(f"\n🤖 SUPPORT BOT RESPONSE:")
        print(result)
        return result

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()

    # Verify API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    # Initialize OpenAI model
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        api_key=openai_api_key
    )
    
    # Initialize the complete system
    print("🚀 Initializing Complete Property Support Bot...")
    support_bot = PropertySupportBot()

    # Test various query types
    test_queries = [
        "What's name of the property?",
        "Look up the terms related to lease duration in the tenancy agreement", 
        "I'm feeling unsure of what to prioritize when searching for properties to rent, any suggestions?"
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"TESTING COMPLETE SUPPORT BOT")
        print(f"{'='*60}")
        
        support_bot.process_query(query)