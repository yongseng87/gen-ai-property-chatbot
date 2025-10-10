import streamlit as st
from datetime import datetime
import time

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
        background-color: #f8f9fa;
    }
    
    /* Sidebar styles */
    [data-testid="stSidebar"] {
        background-color: #000000;
        color: #ffffff;
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
        background-color: #ffffff;
        color: #333;
        padding: 12px 16px;
        border-radius: 18px;
        border-top-right-radius: 4px;
        margin: 8px 0;
        max-width: 70%;
        float: right;
        clear: both;
        border: 1px solid #e0e0e0;
    }
    
    .bot-message {
        background-color: white;
        color: #333;
        padding: 12px 16px;
        border-radius: 18px;
        border-top-left-radius: 4px;
        margin: 8px 0;
        max-width: 70%;
        float: left;
        clear: both;
        border: 1px solid #e0e0e0;
    }
    
    .message-time {
        font-size: 0.75rem;
        color: #999;
        margin-top: 4px;
    }
    
    /* Title styles */
    .main-title {
        color: #667eea;
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        color: #666;
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
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

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
        'name': 'John Smith',
        'tenant_id': 'T12345'
    }

 

# Sidebar
with st.sidebar:
    # Logo and title
    st.markdown("### 🏠 Tenant AI Assistant")
    st.markdown("---")
    
    # Quick actions
    st.markdown("#### Quick Services")
    
    quick_actions = [
        {"icon": "🏠", "label": "Property Match", "query": "I'm looking for a 2-bedroom apartment"},
        {"icon": "📅", "label": "Schedule Viewing", "query": "I'd like to schedule a property viewing"},
        {"icon": "🔧", "label": "Maintenance", "query": "I need to report a maintenance issue"},
        {"icon": "📄", "label": "Contract Query", "query": "When does my tenancy agreement expire?"}
    ]
    
    for action in quick_actions:
        if st.button(f"{action['icon']} {action['label']}", key=action['label'], use_container_width=True):
            st.session_state.messages.append({
                'role': 'user',
                'content': action['query'],
                'timestamp': datetime.now()
            })
            # Simulate AI response
            time.sleep(0.5)
            st.session_state.messages.append({
                'role': 'assistant',
                'content': f"Processing your '{action['label']}' request...",
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
            # Simulate AI response
            time.sleep(0.5)
            st.session_state.messages.append({
                'role': 'assistant',
                'content': "Retrieving information, please wait...",
                'timestamp': datetime.now()
            })
            st.rerun()
    
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

# Main chat area
col1, col2, col3 = st.columns([1, 6, 1])

with col2:
    # Title
    st.markdown('<div class="main-title">💬 AI Assistant</div>', unsafe_allow_html=True)
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
            placeholder="Type your question here..."
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
        
        # Integrate your AI model here
        # Example: Simple keyword matching response
        response = generate_response(user_input)
        
        # Add AI response
        st.session_state.messages.append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now()
        })
        
        st.rerun()

# Footer information
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #999; font-size: 0.8rem;'>"
    "🔒 Your conversations are privacy protected | 📱 Mobile-friendly | ⚡ Powered by RAG Technology"
    "</div>",
    unsafe_allow_html=True
)