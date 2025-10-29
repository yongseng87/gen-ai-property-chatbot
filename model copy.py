import os
import warnings
from dotenv import load_dotenv
import asyncio
import pandas as pd

# LangChain Core
from langchain_openai import ChatOpenAI

# Memory & Chains
from langchain_community.memory import ConversationBufferMemory
from langchain_community.chains import RetrievalQA

# Retrieval & Vector Stores
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

from create_csv_agent import create_csv_agent
from classifier import classify
import re
from datetime import datetime

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


class PropertySupportBot:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, api_key=openai_api_key)
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        
        # Knowledge base
        self.vectorstore = load_and_process_pdf("property_data_generator")
        
        # Memory for conversations
        self.memory = ConversationBufferMemory()
        
        # QA chain for policies
        self.qa_chain = create_pdf_qa_system(self.vectorstore, self.llm)
        self.agent_csv = create_csv_agent("property_database_v2.csv", self.llm)
    
    def process_query(self, query: str):
        """Process user query based on category classification"""
        
        print(f"🔵 INPUT TO SUPPORT BOT:")
        print(f"Query: {query}")

        # Classify the query
        classification = asyncio.run(classify(query))
        module = classification['classifications'][0]['module']
        if module == "information_retrieval":
            print("\n🔵 HANDLING INFORMATION RETRIEVAL QUERY...")
            result = self.qa_chain.invoke(query)
            print(f"Answer: {result['result']}")
            print(f"📄 Sources: Page {result['source_documents'][0].metadata.get('page', 'Unknown')} of PDF")
            print(f"📝 Source Text Preview: {result['source_documents'][0].page_content[:150]}...")
        elif module == "property_data_analysis":
            print("\n🔵 HANDLING PROPERTY DATA ANALYSIS QUERY...")
            result = self.agent_csv.invoke(query)
            print(f"Analysis Result: {result['output']}")
        else:
            print("\n🔵 HANDLING GENERAL QUERY...")
            reason = classification['classifications'][0]['reason']
            result = {"message": f"Sorry, I can't assist with that. Please ask about property-related topics."}
            print(result['message'])
            # Prompt user for email to contact (optional)
            email = input("If you'd like a human agent to contact you, enter your email (or press Enter to skip): ").strip()
            if email:
                # Basic email validation
                if re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
                    folder = os.path.join(os.getcwd(), "user_contacts")
                    os.makedirs(folder, exist_ok=True)
                    file_path = os.path.join(folder, "user_emails.csv")

                    # Write header if file does not exist
                    header_needed = not os.path.exists(file_path)
                    with open(file_path, "a", encoding="utf-8") as f:
                        if header_needed:
                            f.write("timestamp,email,original_query\n")
                        ts = datetime.utcnow().isoformat()
                        # Quote fields to handle commas/quotes safely
                        safe_email = email.replace('"', '""')
                        safe_query = query.replace('"', '""')
                        f.write(f'"{ts}","{safe_email}","{safe_query}"\n')

                    print(f"✅ Email saved to {file_path}")
                    result["saved_email"] = email
                    result["message"] = "Thanks — your email has been saved. A human agent will contact you if needed."
                else:
                    print("⚠️ Invalid email format. Email not saved.")
                    result["saved_email"] = None
                    result["message"] = "Invalid email format. Please try again."
            else:
                print("No email provided; skipping save.")
                result["saved_email"] = None
        
        return result

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
        "what is the latest stock price of Apple Inc?",
    ]

    for query in test_queries:
        print(f"{'='*60}")
        print("PROCESSING NEW QUERY...")
        print(f"{'='*60}")
        
        support_bot.process_query(query)