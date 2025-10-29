import streamlit as st
from datetime import datetime
import time
import os
import sys
from dotenv import load_dotenv

# Add error handling for imports
try:
    # Import the model
    from model import PropertySupportBot
except ImportError as e:
    st.error(f"❌ Error importing model: {e}")
    st.error("Please ensure all required files are present and dependencies are installed.")
    st.stop()

# Additional imports for data handling
try:
    import pandas as pd
    import numpy as np
except ImportError as e:
    st.error(f"❌ Error importing data libraries: {e}")
    st.error("Please install required packages: pip install pandas numpy")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Tenant AI Assistant",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styles
st.markdown("""
    <style>
    /* Main theme colors */
    .stApp {
        background-color: #ffffff;
        color: #000000;
    }
    
    /* Sidebar styles */
    [data-testid="stSidebar"] {
        background-color: #e3f2fd;
        color: #000000;
    }
    
    /* Sidebar button styles */
    [data-testid="stSidebar"] .stButton > button {
        background-color: #f5f5f5 !important;
        color: #000000 !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        margin: 4px 0 !important;
        transition: all 0.3s ease !important;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #eeeeee !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    /* Main content area text color */
    .main .block-container {
        color: #000000;
    }
    
    /* All text elements */
    h1, h2, h3, h4, h5, h6, p, div, span, label {
        color: #000000 !important;
    }
    
    /* Quick action button styles */
    .quick-action-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 20px;
        border-radius: 10px;
        margin: 5px 0;
        cursor: pointer;
        border: none;
        width: 100%;
        text-align: left;
        font-weight: 500;
        transition: transform 0.2s;
    }
    
    .quick-action-btn:hover {
        transform: translateY(-2px);
    }
    
    /* Message bubble styles */
    .user-message {
        background-color: #e3f2fd;
        color: #000000;
        padding: 12px 16px;
        border-radius: 18px;
        border-top-right-radius: 4px;
        margin: 8px 0;
        max-width: 70%;
        float: right;
        clear: both;
        border: 1px solid #bbdefb;
    }
    
    .bot-message {
        background-color: #e3f2fd;
        color: #000000;
        padding: 12px 16px;
        border-radius: 18px;
        border-top-left-radius: 4px;
        margin: 8px 0;
        max-width: 70%;
        float: left;
        clear: both;
        border: 1px solid #bbdefb;
    }
    
    .message-time {
        font-size: 0.75rem;
        color: #999;
        margin-top: 4px;
    }
    
    /* Title styles */
    .main-title {
        color: #000000;
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        color: #000000;
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
    }
    
    /* Status indicator */
    .status-online {
        color: #10b981;
        font-size: 0.875rem;
    }
    
    /* Input box optimization */
    .stTextInput > div > div > input {
        border-radius: 25px;
        padding: 12px 20px;
        border: 2px solid #e0e0e0;
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #bbdefb !important;
        box-shadow: 0 0 0 2px rgba(187, 222, 251, 0.2) !important;
    }
    
    /* Streamlit text elements */
    .stMarkdown, .stText, .stSelectbox label, .stTextInput label {
        color: #000000 !important;
    }
    
    /* Metrics and data elements */
    .metric-container {
        color: #000000 !important;
    }
    
    /* Dataframe styling */
    .dataframe {
        color: #000000 !important;
    }
    
    /* Button text */
    .stButton > button {
        color: #000000 !important;
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Load environment variables
load_dotenv()

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = [
        {
            'role': 'assistant',
            'content': '''Hello! I'm your Tenant AI Assistant. I can help you with:

• Property matching & search
• Schedule property viewings
• Answer tenancy agreement questions
• Handle maintenance requests
• Provide rent payment information

How can I assist you today?''',
            'timestamp': datetime.now()
        }
    ]

if 'user_info' not in st.session_state:
    st.session_state.user_info = {
        'name': 'Capstone Project 4',
        'tenant_id': 'DSS5105'
    }

if 'current_view' not in st.session_state:
    st.session_state.current_view = 'lease_agreement'

# Initialize the AI model
@st.cache_resource
def initialize_ai_model():
    """Initialize the PropertySupportBot with caching"""
    try:
        # Check if API key is available
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            st.error("⚠️ OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")
            return None
        
        # Check if required files exist
        required_files = [
            "property_data_generator",
            "property_database_v2.csv", 
            "classifier.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            st.error("❌ Missing required files:")
            for file in missing_files:
                st.error(f"   - {file}")
            return None
        
        with st.spinner("🤖 Initializing AI model..."):
            bot = PropertySupportBot()
            st.success("✅ AI model loaded successfully!")
            return bot
            
    except ImportError as e:
        st.error(f"❌ Import error: {str(e)}")
        st.error("Please install required packages: pip install -r requirements.txt")
        return None
    except Exception as e:
        st.error(f"❌ Error initializing AI model: {str(e)}")
        st.error("Please check that all required files are present:")
        st.error("- property_data_generator/ folder with PDF files")
        st.error("- property_database_v2.csv file")
        st.error("- classifier.py file")
        st.error("- Valid OpenAI API key in .env file")
        return None

# Initialize the model
ai_bot = initialize_ai_model()

# Test API connection
def test_api_connection():
    """Test if the API connection is working"""
    if ai_bot is None:
        return False
    
    try:
        # Simple test query
        import asyncio
        test_response = asyncio.run(ai_bot.process_query_async("Hello, are you working?"))
        return "error" not in test_response.lower() and "❌" not in test_response
    except Exception as e:
        print(f"API test failed: {e}")
        return False

# Test the connection
api_working = test_api_connection()

# AI response generation function
async def generate_response(user_input):
    """
    Generate AI response using the PropertySupportBot model with async timeout
    """
    if ai_bot is None:
        return "❌ AI model is not available. Please check your OpenAI API key configuration."
    
    try:
        # Use asyncio.wait_for for timeout handling
        import asyncio
        
        try:
            # Set timeout for API calls (30 seconds)
            response = await asyncio.wait_for(
                ai_bot.process_query_async(user_input), 
                timeout=30.0
            )
            return response
        except asyncio.TimeoutError:
            return "⏰ Request timed out. Please try again with a shorter question or check your internet connection."
        except Exception as e:
            return f"❌ Error processing your request: {str(e)}\n\nPlease try again or contact support."
            
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}\n\nPlease try again or contact support."

# Sidebar
with st.sidebar:
    # Logo and title
    st.markdown("### 🏠 Tenant AI Assistant")
    st.markdown("---")
    
    # Main function buttons
    st.markdown("#### Main Functions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄 Lease Agreement", key="lease_btn", use_container_width=True):
            st.session_state.current_view = 'lease_agreement'
            st.rerun()
    
    with col2:
        if st.button("📊 Property Statistics", key="stats_btn", use_container_width=True):
            st.session_state.current_view = 'property_statistics'
            st.rerun()
    
    st.markdown("---")
    
    # Quick actions
    st.markdown("#### Quick Services")
    
    quick_actions = [
        {"icon": "🏠", "label": "Property Match", "query": "I'm looking for a 2-bedroom apartment"},
        {"icon": "📄", "label": "Contract Query", "query": "When does my tenancy agreement expire?"}
    ]
    
    for action in quick_actions:
        if st.button(f"{action['icon']} {action['label']}", key=action['label'], use_container_width=True):
            st.session_state.messages.append({
                'role': 'user',
                'content': action['query'],
                'timestamp': datetime.now()
            })
            
            # Use AI model if available, otherwise show placeholder
            if ai_bot is not None:
                import asyncio
                response = asyncio.run(generate_response(action['query']))
            else:
                response = f"Processing your '{action['label']}' request... (AI model not available)"
            
            st.session_state.messages.append({
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.now()
            })
            st.rerun()
    
    st.markdown("---")
    
    # Common questions
    st.markdown("#### Common Questions")
    
    example_questions = [
        "When is my rent due?",
        "How do I report an AC issue?",
        "Can I keep pets?",
        "What's the notice period for early termination?"
    ]
    
    for question in example_questions:
        if st.button(question, key=f"q_{question}", use_container_width=True):
            st.session_state.messages.append({
                'role': 'user',
                'content': question,
                'timestamp': datetime.now()
            })
            
            # Use AI model if available, otherwise show placeholder
            if ai_bot is not None:
                import asyncio
                response = asyncio.run(generate_response(question))
            else:
                response = "Retrieving information, please wait... (AI model not available)"
            
            st.session_state.messages.append({
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.now()
            })
            st.rerun()
    
    st.markdown("---")
    
    # AI Model Status
    st.markdown("#### 🤖 AI Model Status")
    if ai_bot is not None:
        if api_working:
            st.success("✅ AI Model Active & Connected")
            st.caption("Powered by GPT-4o-mini + RAG")
        else:
            st.warning("⚠️ AI Model Loaded but API Issues")
            st.caption("Check API key or network connection")
    else:
        st.error("❌ AI Model Offline")
        st.caption("Check API configuration")
    
    st.markdown("---")
    
    # User information
    st.markdown("#### 👤 User Profile")
    st.write(f"**Name**: {st.session_state.user_info['name']}")
    st.write(f"**Tenant ID**: {st.session_state.user_info['tenant_id']}")
    
    st.markdown("---")
    
    # Clear conversation button
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = [st.session_state.messages[0]]
        st.rerun()

# Main content area based on selected view
if st.session_state.current_view == 'lease_agreement':
    # Lease Agreement Interface
    col1, col2, col3 = st.columns([1, 6, 1])
    
    with col2:
        # Title
        st.markdown('<div class="main-title">📄 Lease Agreement Assistant</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle"><span class="status-online">● Online</span> | Powered by AI • RAG Technology</div>', unsafe_allow_html=True)
        
        # Message display area
        message_container = st.container()
        
        with message_container:
            for message in st.session_state.messages:
                role = message['role']
                content = message['content']
                timestamp = message['timestamp'].strftime("%H:%M")
                
                if role == 'user':
                    st.markdown(f'''
                        <div style="text-align: right; margin: 20px 0;">
                            <div class="user-message">
                                {content}
                            </div>
                            <div class="message-time" style="text-align: right;">
                                {timestamp}
                            </div>
                        </div>
                        <div style="clear: both;"></div>
                    ''', unsafe_allow_html=True)
                else:
                    st.markdown(f'''
                        <div style="text-align: left; margin: 20px 0;">
                            <div class="bot-message">
                                {content}
                            </div>
                            <div class="message-time" style="text-align: left;">
                                {timestamp}
                            </div>
                        </div>
                        <div style="clear: both;"></div>
                    ''', unsafe_allow_html=True)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Input area
        st.markdown("---")
        
        # Use columns to create input box and send button layout
        input_col1, input_col2 = st.columns([5, 1])
        
        with input_col1:
            user_input = st.text_input(
                "Type your message",
                key="user_input",
                label_visibility="collapsed",
                placeholder="Ask about lease agreement terms..."
            )
        
        with input_col2:
            send_button = st.button("Send 📤", use_container_width=True, type="primary")
        
        # Handle send message
        if send_button and user_input:
            # Add user message
            st.session_state.messages.append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now()
            })
            
            # Generate response
            import asyncio
            response = asyncio.run(generate_response(user_input))
            
            # Add AI response
            st.session_state.messages.append({
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.now()
            })
            
            st.rerun()

elif st.session_state.current_view == 'property_statistics':
    # Property Statistics Interface
    col1, col2, col3 = st.columns([1, 6, 1])
    
    with col2:
        # Title
        st.markdown('<div class="main-title">📊 Property Statistics Dashboard</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle"><span class="status-online">● Online</span> | Real-time Property Analytics</div>', unsafe_allow_html=True)
        
        # Statistics cards
        st.markdown("### 📈 Key Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Properties",
                value="1,234",
                delta="12%"
            )
        
        with col2:
            st.metric(
                label="Occupancy Rate",
                value="94.2%",
                delta="2.1%"
            )
        
        with col3:
            st.metric(
                label="Avg Rent",
                value="$3,200",
                delta="$150"
            )
        
        with col4:
            st.metric(
                label="Maintenance Requests",
                value="23",
                delta="-5"
            )
        
        st.markdown("---")
        
        # Charts section
        st.markdown("### 📊 Property Distribution")
        
        # Sample data for demonstration
        # Property type distribution
        property_data = pd.DataFrame({
            'Property Type': ['1-Bedroom', '2-Bedroom', '3-Bedroom', 'Studio'],
            'Count': [45, 78, 32, 12],
            'Avg Rent': [2800, 3200, 4200, 2200]
        })
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.bar_chart(property_data.set_index('Property Type')['Count'])
            st.caption("Property Count by Type")
        
        with col2:
            st.bar_chart(property_data.set_index('Property Type')['Avg Rent'])
            st.caption("Average Rent by Type")
        
        st.markdown("---")
        
        # Recent activity
        st.markdown("### 🔄 Recent Activity")
        
        activity_data = pd.DataFrame({
            'Time': ['10:30 AM', '09:45 AM', '09:15 AM', '08:30 AM'],
            'Activity': ['New lease signed', 'Maintenance completed', 'Rent payment received', 'Property viewing scheduled'],
            'Property': ['Apt 101', 'Apt 205', 'Apt 302', 'Apt 108']
        })
        
        st.dataframe(activity_data, use_container_width=True)
        
        st.markdown("---")
        
        # AI-powered insights
        st.markdown("### 🧠 AI-Powered Insights")
        
        if ai_bot is not None:
            insight_queries = [
                "Analyze property performance trends",
                "What are the maintenance patterns?",
                "Identify occupancy optimization opportunities"
            ]
            
            selected_insight = st.selectbox(
                "Choose an insight to generate:",
                insight_queries,
                key="insight_selector"
            )
            
            if st.button("🔍 Generate Insight", key="generate_insight"):
                with st.spinner("🤖 AI is analyzing data..."):
                    import asyncio
                    insight_response = asyncio.run(ai_bot.process_query_async(selected_insight))
                    st.markdown("#### 💡 AI Insight:")
                    st.info(insight_response)
        else:
            st.warning("⚠️ AI model not available for insights generation")

# Footer information
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #999; font-size: 0.8rem;'>"
    "🔒 Your conversations are privacy protected | 📱 Mobile-friendly | ⚡ Powered by RAG Technology"
    "</div>",
    unsafe_allow_html=True
)


