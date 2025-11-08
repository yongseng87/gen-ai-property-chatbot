import streamlit as st
from datetime import datetime
import time
import os
import sys
from dotenv import load_dotenv
import difflib

# Add error handling for imports
try:
    # Import the model
    from model_v2 import PropertySupportBot
except ImportError as e:
    st.error(f"❌ Error importing model: {e}")
    st.error("Please ensure all required files are present and dependencies are installed.")
    st.stop()

# Additional imports for data handling
try:
    import pandas as pd
    import numpy as np
    import altair as alt
    import pydeck as pdk
except ImportError as e:
    st.error(f"❌ Error importing data libraries: {e}")
    st.error("Please install required packages: pip install pandas numpy altair")
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
        background-color: #ffffe0;
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
    st.session_state.current_view = 'property_statistics'

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
            "property_database_v3.csv", 
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
        st.error("- property_database_v3.csv file")
        st.error("- classifier.py file")
        st.error("- Valid OpenAI API key in .env file")
        return None

# Initialize the model
ai_bot = initialize_ai_model()

# Property data loader
@st.cache_data
def load_property_data():
    """Load property dataset with caching"""
    df = pd.read_csv("property_database_v3.csv")
    numeric_columns = [
        "monthly_rent", "rental_price", "sqft", "bedrooms", "bathrooms",
        "floor_level", "distance_to_mrt"
    ]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


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
        
        with st.spinner("🤔 Thinking, please hold on..."):
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
    
    # Main navigation buttons
    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        if st.button("💬 Lease Agreement", use_container_width=True, key="nav_lease"):
            st.session_state.current_view = 'lease_agreement'
            st.rerun()

    with nav_col2:
        if st.button("📊 Property Statistics", use_container_width=True, key="nav_stats"):
            st.session_state.current_view = 'property_statistics'
            st.rerun()

    st.markdown("---")

    # Removed Main Functions and Quick Services sections
    
    # Common questions
    st.markdown("#### Common Questions")
    
    example_questions = [
        "What is the interest rate for late payment of rent?",
        "How long is the defect free period?",
        "Can I keep pets?",
        "Who has to pay for repairs?"
    ]
    
    for question in example_questions:
        if st.button(question, key=f"q_{question}", use_container_width=True):
            st.session_state.messages.append({
                'role': 'user',
                'content': question,
                'timestamp': datetime.now()
            })
            
            # Generate response asynchronously
            import asyncio
            response = asyncio.run(generate_response(question))

            # Conditionally format PDF-type response
            if isinstance(response, dict) and response.get("type") == "pdf":
                answer = response.get("answer")
                sources = response.get("sources")

                # If sources exist, format them with page and preview
                if sources:
                    page = sources[0].get("page", "Unknown")
                    preview = sources[0].get("preview", "No preview available.")
                    # chunk = sources[0].get("chunk", "No content found.")

                    display_content = f"AI Assistant: {answer}\n\n📄 Sources: Page {page}\n\n 📝 Source Text Preview : {preview}"
                else:
                    # If no sources, just display the answer
                    display_content = f"AI Assistant: {answer}\n\nNo sources available."
            else:
                # For non-PDF type response, just display the answer
                display_content = f"AI Assistant: {response}"
            
            # Add AI response to session
            st.session_state.messages.append({
                'role': 'assistant',
                'content': display_content,
                'timestamp': datetime.now()
            })
            st.rerun()
    

    
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
            # Add user message to session
            st.session_state.messages.append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now()
            })

            # Generate response asynchronously
            import asyncio
            response = asyncio.run(generate_response(user_input))

            # Conditionally format PDF-type response
            if isinstance(response, dict) and response.get("type") == "pdf":
                answer = response.get("answer")
                sources = response.get("sources")

                # If sources exist, format them with page and preview
                if sources:
                    page = sources[0].get("page", "Unknown")
                    preview = sources[0].get("preview", "No preview available.")
                    # chunk = sources[0].get("chunk", "No content found.")
                    display_content = f"AI Assistant: {answer}\n\n📄 Sources: Page {page}\n\n 📝 Source Text Preview : {preview}"
                else:
                    # If no sources, just display the answer
                    display_content = f"AI Assistant: {answer}\n\nNo sources available."
            else:
                # For non-PDF type response, just display the answer
                display_content = f"AI Assistant: {response.get('answer')}"

            # Add AI response to session
            st.session_state.messages.append({
                'role': 'assistant',
                'content': display_content,
                'timestamp': datetime.now()
            })

            st.rerun()

elif st.session_state.current_view == 'property_statistics':
    # Property Statistics Interface
    col1, col2, col3 = st.columns([1, 6, 1])
    
    with col2:
        # Scoped styles for light blue backgrounds in this section only
        st.markdown(
            """
            <style>
            /* Scoped to this section via attribute selector on following wrapper */
            .stats-section .text-box {
                background-color: #e3f2fd !important;
                color: #000000 !important;
                border: 1px solid #bbdefb;
                border-radius: 10px;
                padding: 10px 14px;
                margin-bottom: 8px;
            }
            .stats-section [data-testid="stMetric"]{
                background-color: #e3f2fd !important;
                border: 1px solid #bbdefb !important;
                border-radius: 10px !important;
                padding: 8px 12px !important;
            }
            .stats-section [data-testid="stDataFrame"]{
                background-color: #e3f2fd !important;
                border: 1px solid #bbdefb !important;
                border-radius: 10px !important;
                padding: 6px !important;
            }
            .stats-section [data-testid="stDataFrame"] canvas, 
            .stats-section [data-testid="stDataFrame"] div{
                background-color: #e3f2fd !important;
            }
            /* Style Streamlit info/alert boxes inside stats section */
            .stats-section [data-testid="stAlert"],
            .stats-section [role="alert"]{
                background-color: #e3f2fd !important;
                border: 1px solid #bbdefb !important;
                color: #000000 !important;
                border-radius: 10px !important;
            }
            .stats-section [data-testid="stAlert"] * {
                background-color: transparent !important;
                color: #000000 !important;
            }
            .stats-section .chart-caption{
                background-color: #e3f2fd !important;
                border: 1px solid #bbdefb !important;
                border-radius: 8px !important;
                padding: 6px 10px !important;
                display: inline-block;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Wrapper to scope styles
        st.markdown('<div class="stats-section">', unsafe_allow_html=True)

        # Title
        st.markdown('<div class="main-title text-box">📊 Property Statistics Dashboard</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle text-box"><span class="status-online">● Online</span> | Real-time Property Analytics</div>', unsafe_allow_html=True)
        
        # Load property data
        property_df = load_property_data()

        if property_df.empty:
            st.warning("⚠️ Unable to load `property_database_v3.csv`. Please verify the file exists and has data.")
        else:
            price_column = "rental_price" if "rental_price" in property_df.columns else "monthly_rent"

            if price_column not in property_df.columns:
                st.warning("⚠️ The dataset is missing a rental price column. Expected `rental_price` or `monthly_rent`.")
            else:
                # Filter section
                st.markdown('<div class="text-box">### 🎛️ Property Filters</div>', unsafe_allow_html=True)

                filter_col1, filter_col2 = st.columns([1.3, 1.3])

                # Nearest MRT filter with suggestions
                with filter_col1:
                    unique_mrt = sorted(property_df['nearest_mrt_name'].dropna().unique()) if 'nearest_mrt_name' in property_df.columns else []
                    mrt_search = st.text_input("Search nearest MRT name", key="filter_mrt_input")
                    mrt_options = unique_mrt
                    if mrt_search:
                        contains_matches = [opt for opt in unique_mrt if mrt_search.lower() in opt.lower()]
                        close_matches = difflib.get_close_matches(mrt_search, unique_mrt, n=10, cutoff=0.0)
                        merged = []
                        for opt in contains_matches + close_matches:
                            if opt not in merged:
                                merged.append(opt)
                        mrt_options = merged or unique_mrt
                    mrt_select = st.selectbox(
                        "Select nearest MRT",
                        options=["All"] + mrt_options,
                        index=0,
                        key="filter_mrt_select"
                    )

                # Town filter with suggestions
                with filter_col2:
                    unique_towns = sorted(property_df['town'].dropna().unique()) if 'town' in property_df.columns else []
                    town_search = st.text_input("Search town", key="filter_town_input")
                    town_options = unique_towns
                    if town_search:
                        contains_matches = [opt for opt in unique_towns if town_search.lower() in opt.lower()]
                        close_matches = difflib.get_close_matches(town_search, unique_towns, n=10, cutoff=0.0)
                        merged = []
                        for opt in contains_matches + close_matches:
                            if opt not in merged:
                                merged.append(opt)
                        town_options = merged or unique_towns
                    town_select = st.selectbox(
                        "Select town",
                        options=["All"] + town_options,
                        index=0,
                        key="filter_town_select"
                    )

                # Rental price range filter
                price_col = property_df[price_column].dropna()
                min_price_value = float(price_col.min()) if not price_col.empty else 0.0
                default_max_value = float(price_col.max()) if not price_col.empty else 10000.0

                price_col1, price_col2, price_col3 = st.columns([1, 1, 1])

                with price_col1:
                    min_price = st.number_input(
                        "Minimum rental price",
                        min_value=0.0,
                        value=max(0.0, float(min_price_value)),
                        step=50.0,
                        key="filter_min_price"
                    )

                with price_col2:
                    no_max_price = st.checkbox("No maximum rental price", value=True, key="filter_no_max_price")

                with price_col3:
                    if no_max_price:
                        max_price = float("inf")
                        st.markdown("<div class='text-box'>Current max: no limit</div>", unsafe_allow_html=True)
                    else:
                        max_price = st.number_input(
                            "Maximum rental price",
                            min_value=min_price,
                            value=max(min_price + 100.0, default_max_value),
                            step=50.0,
                            key="filter_max_price"
                        )

                filtered_df = property_df.copy()

                if 'nearest_mrt_name' in filtered_df.columns and mrt_select != "All":
                    filtered_df = filtered_df[filtered_df['nearest_mrt_name'] == mrt_select]

                if 'town' in filtered_df.columns and town_select != "All":
                    filtered_df = filtered_df[filtered_df['town'] == town_select]

                filtered_df = filtered_df[(filtered_df[price_column] >= min_price)]
                if max_price != float("inf"):
                    filtered_df = filtered_df[(filtered_df[price_column] <= max_price)]

                if filtered_df.empty:
                    st.warning("⚠️ No properties match the current filters. Please adjust your criteria.")
                else:
                    st.markdown('<div class="text-box">### 📈 Key Metrics</div>', unsafe_allow_html=True)

                    total_properties = len(filtered_df)
                    avg_price = filtered_df[price_column].mean()
                    median_price = filtered_df[price_column].median()
                    available_ratio = (
                        filtered_df['rental_status'].str.contains('Available', case=False, na=False).mean() * 100
                        if 'rental_status' in filtered_df.columns else None
                    )

                    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

                    with metric_col1:
                        st.metric("Matching properties", f"{total_properties}")

                    with metric_col2:
                        st.metric("Average rental price", f"${avg_price:,.0f}")

                    with metric_col3:
                        st.metric("Median rental price", f"${median_price:,.0f}")

                    with metric_col4:
                        if available_ratio is not None:
                            st.metric("Availability share", f"{available_ratio:.1f}%")
                        else:
                            st.metric("Availability share", "N/A")

                    st.markdown("---")

                    # Chart section with dimension & metric selection
                    st.markdown('<div class="text-box">### 📊 Filtered Results Chart</div>', unsafe_allow_html=True)

                    chart_col1, chart_col2 = st.columns([1.2, 1.2])
                    dimension_label_map = {}
                    if 'nearest_mrt_name' in filtered_df.columns:
                        dimension_label_map["By nearest MRT"] = 'nearest_mrt_name'
                    if 'town' in filtered_df.columns:
                        dimension_label_map["By town"] = 'town'

                    if dimension_label_map:
                        with chart_col1:
                            selected_dimension_label = st.selectbox(
                                "Chart dimension",
                                options=list(dimension_label_map.keys()),
                                key="chart_dimension"
                            )
                            selected_dimension = dimension_label_map[selected_dimension_label]
                    else:
                        selected_dimension = None

                    with chart_col2:
                        metric_option = st.radio(
                            "Chart metric",
                            options=["Property count", "Average rental price"],
                            key="chart_metric",
                            horizontal=True
                        )

                    if selected_dimension:
                        aggregated_df = (
                            filtered_df.groupby(selected_dimension)
                            .agg(average_price=(price_column, 'mean'))
                            .reset_index()
                        )
                        counts_df = (
                            filtered_df.groupby(selected_dimension)
                            .size()
                            .reset_index(name='property_count')
                        )
                        aggregated_df = aggregated_df.merge(counts_df, on=selected_dimension, how='left')
                        aggregated_df = aggregated_df.rename(columns={selected_dimension: 'Category'})

                        if metric_option == "Property count":
                            y_field = 'property_count'
                            y_title = 'Number of properties'
                        else:
                            y_field = 'average_price'
                            y_title = 'Average rental price (SGD)'

                        chart = (
                            alt.Chart(aggregated_df)
                            .mark_bar(color="#64b5f6")
                            .encode(
                                x=alt.X('Category:N', sort='-y', title='Category'),
                                y=alt.Y(f'{y_field}:Q', title=y_title),
                                tooltip=[
                                    'Category',
                                    alt.Tooltip('property_count:Q', title='Property count'),
                                    alt.Tooltip('average_price:Q', format=',.0f', title='Average rental price (SGD)')
                                ]
                            )
                            .properties(width='container', height=360, background='#e3f2fd')
                        )
                        st.altair_chart(chart, use_container_width=True)
                        st.markdown(
                            f'<div class="chart-caption">Results by {selected_dimension_label.lower()} ({metric_option})</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.info("No categorical dimension available to plot charts. Please ensure the dataset contains `nearest_mrt_name` or `town` columns.")

                    st.markdown("---")

                    # Data table of filtered results
                    st.markdown('<div class="text-box">### 📋 Filtered Properties</div>', unsafe_allow_html=True)
                    display_columns = [
                        "town", "flat_type", "block / building", "street_name", "property_type",
                        "nearest_mrt_name", price_column, "rental_status", "address"
                    ]
                    available_columns = [col for col in display_columns if col in filtered_df.columns]
                    column_renames = {
                        "town": "Town",
                        "flat_type": "Flat type",
                        "block / building": "Block/Building",
                        "street_name": "Street name",
                        "property_type": "Property type",
                        "nearest_mrt_name": "Nearest MRT",
                        price_column: "Rental price (SGD)",
                        "rental_status": "Rental status",
                        "address": "Address"
                    }

                    st.dataframe(
                        filtered_df[available_columns].rename(columns=column_renames),
                        use_container_width=True
                    )

                    st.markdown("---")

                    # Map of filtered properties
                    if {'latitude', 'longitude'}.issubset(filtered_df.columns):
                        map_df = filtered_df[['latitude', 'longitude', 'address']].dropna(subset=['latitude', 'longitude']).copy()
                        map_df['latitude'] = pd.to_numeric(map_df['latitude'], errors='coerce')
                        map_df['longitude'] = pd.to_numeric(map_df['longitude'], errors='coerce')
                        map_df = map_df.dropna(subset=['latitude', 'longitude'])

                        if not map_df.empty:
                            st.markdown('<div class="text-box">### 🗺️ Map of Filtered Properties</div>', unsafe_allow_html=True)

                            midpoint = [map_df['latitude'].mean(), map_df['longitude'].mean()]

                            scatter_layer = pdk.Layer(
                                "ScatterplotLayer",
                                data=map_df,
                                get_position="[longitude, latitude]",
                                get_radius=80,
                                get_fill_color=[100, 181, 246, 200],
                                pickable=True
                            )

                            tooltip = {
                                "html": "<b>Address:</b> {address}<br/><b>Latitude:</b> {latitude}<br/><b>Longitude:</b> {longitude}",
                                "style": {"backgroundColor": "#f0f6ff", "color": "#000"}
                            }

                            view_state = pdk.ViewState(latitude=midpoint[0], longitude=midpoint[1], zoom=11, pitch=40)

                            deck = pdk.Deck(
                                layers=[scatter_layer],
                                initial_view_state=view_state,
                                tooltip=tooltip,
                                map_style="light"
                            )
                            st.pydeck_chart(deck)
                            st.markdown("---")
                        else:
                            st.info("No valid latitude/longitude data available for the current filters.")
                    else:
                        st.info("Dataset does not include latitude/longitude columns, so the map cannot be displayed.")
        
        # AI-powered insights
        st.markdown('<div class="text-box">### 🧠 AI-Powered Insights</div>', unsafe_allow_html=True)
        
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

        # Close scoped wrapper
        st.markdown('</div>', unsafe_allow_html=True)

# Footer information
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #999; font-size: 0.8rem;'>"
    "🔒 Your conversations are privacy protected | 📱 Mobile-friendly | ⚡ Powered by RAG Technology"
    "</div>",
    unsafe_allow_html=True
)



