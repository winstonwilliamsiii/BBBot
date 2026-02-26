"""
Bentley ChatBot Component
=========================
AI-powered chatbot for financial analysis and Q&A using DeepSeek or similar LLM.

Features:
- Natural language Q&A about portfolio and financial data
- Macro and micro economic news analysis
- BLS and Census data integration
- Context-aware responses based on user's data
- Conversation history
"""

import streamlit as st
from typing import List, Dict, Optional
from datetime import datetime
import requests
import os
import logging

# Setup logging
logger = logging.getLogger(__name__)


class BentleyChatBot:
    """AI-powered financial chatbot"""
    
    def __init__(self):
        """Initialize chatbot with API credentials"""
        self.api_key = os.getenv('DEEPSEEK_API_KEY', '')
        self.api_endpoint = os.getenv('DEEPSEEK_API_ENDPOINT', 'https://api.deepseek.com/v1/chat/completions')
        self.model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
        
        # Initialize conversation history in session state
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        if 'chat_context' not in st.session_state:
            st.session_state.chat_context = self._build_initial_context()
    
    def _build_initial_context(self) -> str:
        """Build initial context about available data and capabilities"""
        context = """
        I am Bentley, your AI financial assistant. I can help you with:
        
        1. **Portfolio Analysis** - Insights about your investment portfolio
        2. **Budget Analysis** - Personal spending patterns and recommendations
        3. **Market Data** - Stock prices, crypto trends, and market news
        4. **Economic Data** - BLS employment data, Census statistics, macro indicators
        5. **Trading Insights** - Analysis for your broker accounts (WeBull, IBKR, Binance, NinjaTrader, Meta5)
        
        I have access to:
        - Your personal budget and transaction data
        - Investment portfolio positions and performance
        - Real-time market data via yfinance
        - Cryptocurrency prices and trends
        - Economic indicators from BLS and Census
        - News and sentiment analysis
        
        Ask me anything about your finances, investments, or the markets!
        """
        return context
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history"""
        st.session_state.chat_history.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now()
        })
    
    def get_response(self, user_message: str, context_data: Dict = None) -> str:
        """
        Get AI response from DeepSeek or fallback to rule-based responses.
        
        Args:
            user_message: User's question or prompt
            context_data: Additional context (portfolio data, budget info, etc.)
        
        Returns:
            AI-generated response
        """
        # Add user message to history
        self.add_message('user', user_message)
        
        # Try API call if configured
        if self.api_key:
            try:
                response = self._call_api(user_message, context_data)
                self.add_message('assistant', response)
                return response
            except Exception as e:
                st.warning(f"API call failed: {e}. Using fallback responses.")
        
        # Fallback to rule-based responses
        response = self._fallback_response(user_message, context_data)
        self.add_message('assistant', response)
        return response
    
    def _call_api(self, user_message: str, context_data: Dict = None) -> str:
        """Call DeepSeek API for AI response"""
        
        # Build context from available data
        context_parts = [st.session_state.chat_context]
        
        if context_data:
            if 'portfolio_summary' in context_data:
                context_parts.append(f"\nCurrent Portfolio: {context_data['portfolio_summary']}")
            if 'budget_summary' in context_data:
                context_parts.append(f"\nBudget Status: {context_data['budget_summary']}")
            if 'market_data' in context_data:
                context_parts.append(f"\nMarket Data: {context_data['market_data']}")
        
        full_context = "\n".join(context_parts)
        
        # Build messages for API
        messages = [
            {"role": "system", "content": full_context}
        ]
        
        # Add recent conversation history (last 5 messages)
        recent_history = st.session_state.chat_history[-5:] if len(st.session_state.chat_history) > 0 else []
        for msg in recent_history:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Make API call
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        response = requests.post(self.api_endpoint, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content']
    
    def _fallback_response(self, user_message: str, context_data: Dict = None) -> str:
        """Generate rule-based response when API is unavailable"""
        
        message_lower = user_message.lower()
        
        # Portfolio questions
        if any(word in message_lower for word in ['portfolio', 'stocks', 'investment', 'holdings']):
            if context_data and 'portfolio_summary' in context_data:
                return f"📊 Based on your portfolio data: {context_data['portfolio_summary']}\n\nI can provide more detailed analysis once the AI API is configured."
            else:
                return "📊 I can help with portfolio analysis! Please navigate to the Investment Analysis page to view your holdings and performance."
        
        # Budget questions
        elif any(word in message_lower for word in ['budget', 'spending', 'expenses', 'income']):
            if context_data and 'budget_summary' in context_data:
                return f"💰 Your budget summary: {context_data['budget_summary']}\n\nConnect your bank account for more detailed insights!"
            else:
                return "💰 I can help analyze your budget! Visit the Personal Budget page to connect your bank account via Plaid and track your spending."
        
        # Crypto questions
        elif any(word in message_lower for word in ['crypto', 'bitcoin', 'ethereum', 'binance']):
            return "🔴 For cryptocurrency analysis, check out the Live Crypto Dashboard page. I can help analyze trends and provide trading insights!"
        
        # Trading questions
        elif any(word in message_lower for word in ['trade', 'broker', 'ibkr', 'webull', 'ninjatrader']):
            return "💼 You have accounts with WeBull, IBKR, Binance, NinjaTrader, and Meta5. Visit the Broker Trading page to manage your positions and execute trades."
        
        # Economic data questions
        elif any(word in message_lower for word in ['bls', 'employment', 'census', 'economic', 'macro', 'unemployment', 'inflation', 'cpi', 'jobs', 'release', 'gdp', 'housing']):
            try:
                from frontend.utils.economic_data import get_economic_fetcher
                fetcher = get_economic_fetcher()
                
                # Check if user is asking about today's releases
                if any(w in message_lower for w in ['today', 'release', 'schedule', 'happening', 'coming']):
                    economic_summary = fetcher.format_for_chatbot(include_calendar=True)
                else:
                    economic_summary = fetcher.get_economic_summary()
                
                response = f"📈 **Economic Data Insights**\n\n{economic_summary}\n\n"
                response += "Learn more at [BLS.gov](https://www.bls.gov) • [FRED](https://fred.stlouisfed.org) • [Census](https://www.census.gov)"
                return response
            except Exception as e:
                logger.warning(f"Economic data fetch failed: {e}")
                return f"📈 I can provide insights on economic indicators from BLS and Census data. (Technical issue: {str(e)})"
        
        # Market news
        elif any(word in message_lower for word in ['news', 'market', 'sentiment']):
            return "📰 Market news and sentiment analysis is coming soon! I'll be able to summarize macro and micro news relevant to your portfolio."
        
        # Bot capabilities
        elif any(word in message_lower for word in ['help', 'what can you do', 'capabilities']):
            return """
            🤖 **I'm Bentley, your AI financial assistant!**
            
            I can help you with:
            - 📊 Portfolio analysis and investment insights
            - 💰 Budget tracking and spending recommendations
            - 🔴 Cryptocurrency trends and analysis
            - 💼 Broker account management
            - 📈 Economic data (BLS, Census)
            - 📰 Market news and sentiment
            - 🤖 Automated trading strategies
            
            **To get started:**
            - Ask me about your portfolio or budget
            - Navigate to different pages for detailed views
            - Connect your bank account for personalized insights
            
            *Note: Full AI capabilities require DeepSeek API configuration*
            """
        
        # Default response
        else:
            return f"🤖 I received your question: '{user_message}'\n\nI'm still learning! For now, I can help with specific questions about:\n- Your portfolio\n- Budget and spending\n- Crypto markets\n- Trading strategies\n\nTry asking something specific, or configure the DeepSeek API for full AI capabilities."
    
    def clear_history(self):
        """Clear conversation history"""
        st.session_state.chat_history = []
        st.session_state.chat_context = self._build_initial_context()


def render_chatbot_interface(context_data: Dict = None):
    """
    Render the chatbot UI component with Bot Status styling.
    
    Args:
        context_data: Dictionary with portfolio_summary, budget_summary, market_data, etc.
    """
    # Initialize chatbot
    chatbot = BentleyChatBot()
    
    # Header section with status cards and Mansa Capital branding
    st.markdown("""
    <div style='text-align: center; margin-bottom: 1rem;'>
        <h2 style='color: #FFFFFF; font-size: 2rem; margin-bottom: 0.5rem;'>
            🤖 Bentley AI Assistant
        </h2>
        <p style='color: #FFFFFF; font-size: 1rem; margin-bottom: 0.3rem;'>
            Your intelligent financial advisor - Ask me anything about your portfolio, budget, or the markets
        </p>
        <div style='background: linear-gradient(135deg, #0A0A0A 0%, #111827 100%); 
                    padding: 0.75rem 1.5rem; border-radius: 8px; margin: 1rem auto; 
                    max-width: 400px; border: 1px solid #FACC15; box-shadow: 0 2px 8px rgba(250, 204, 21, 0.2);'>
            <p style='color: #FACC15; font-size: 0.85rem; font-weight: 600; margin: 0; letter-spacing: 0.5px;'>
                ⚡ Powered by Mansa Capital, LLC
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Status cards row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_icon = "🟢" if chatbot.api_key else "🟡"
        status_text = "AI Connected" if chatbot.api_key else "Rule-Based Mode"
        st.markdown(f"""
        <div class='metric-card' style='background: linear-gradient(135deg, #111827 0%, #0A0A0A 100%); border: 1px solid #14B8A6;'>
            <div class='metric-label' style='color: #FFFFFF;'>Status</div>
            <div class='metric-value' style='color: #14B8A6; font-size: 1.1rem;'>{status_icon} {status_text}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        chat_count = len(st.session_state.get('chat_history', []))
        st.markdown(f"""
        <div class='metric-card' style='background: linear-gradient(135deg, #111827 0%, #0A0A0A 100%); border: 1px solid #FACC15;'>
            <div class='metric-label' style='color: #FFFFFF;'>Conversations</div>
            <div class='metric-value' style='color: #FACC15; font-size: 1.1rem;'>{chat_count // 2} exchanges</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        model_name = "DeepSeek" if chatbot.api_key else "Local Rules"
        st.markdown(f"""
        <div class='metric-card' style='background: linear-gradient(135deg, #111827 0%, #0A0A0A 100%); border: 1px solid #14B8A6;'>
            <div class='metric-label' style='color: #FFFFFF;'>Model</div>
            <div class='metric-value' style='color: #14B8A6; font-size: 1.1rem;'>{model_name}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        context_items = len([k for k, v in (context_data or {}).items() if v])
        st.markdown(f"""
        <div class='metric-card' style='background: linear-gradient(135deg, #111827 0%, #0A0A0A 100%); border: 1px solid #FACC15;'>
            <div class='metric-label' style='color: #FFFFFF;'>Data Sources</div>
            <div class='metric-value' style='color: #FACC15; font-size: 1.1rem;'>{context_items} active</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick action buttons with Mansa Capital branding
    st.markdown("""
    <style>
    /* Button styling with Mansa Capital teal accent */
    div[data-testid="column"] button[kind="primary"] {
        background: linear-gradient(135deg, #14B8A6 0%, #0D9488 100%) !important;
        color: #FFFFFF !important;
        border: 2px solid #14B8A6 !important;
        font-weight: 600 !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.4) !important;
    }
    div[data-testid="column"] button[kind="primary"]:hover {
        background: linear-gradient(135deg, #0D9488 0%, #14B8A6 100%) !important;
        box-shadow: 0 4px 16px rgba(20, 184, 166, 0.5) !important;
        border-color: #FACC15 !important;
        transform: translateY(-2px) !important;
        transition: all 0.2s ease !important;
    }
    /* Popover buttons with gold accent */
    button[data-testid="baseButton-secondary"] {
        background: linear-gradient(135deg, #111827 0%, #0A0A0A 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #14B8A6 !important;
    }
    button[data-testid="baseButton-secondary"]:hover {
        background: linear-gradient(135deg, #0A0A0A 0%, #111827 100%) !important;
        border-color: #FACC15 !important;
        color: #FACC15 !important;
    }
    </style>
    <br>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True, type="primary"):
            chatbot.clear_history()
            st.rerun()
    
    with col2:
        with st.popover("⚙️ Settings", use_container_width=True):
            st.markdown("<p style='color: #FFFFFF; font-weight: 600;'>API Configuration</p>", unsafe_allow_html=True)
            st.code("DEEPSEEK_API_KEY=your_key", language="bash")
            st.code("DEEPSEEK_MODEL=deepseek-chat", language="bash")
            st.markdown("<p style='color: #14B8A6; font-size: 0.85rem;'>Add to .env file</p>", unsafe_allow_html=True)
    
    with col3:
        with st.popover("💡 Examples", use_container_width=True):
            st.markdown("<p style='color: #FFFFFF; font-weight: 600;'>Try asking:</p>", unsafe_allow_html=True)
            st.markdown("<p style='color: #FACC15;'>• How is my portfolio?</p>", unsafe_allow_html=True)
            st.markdown("<p style='color: #FACC15;'>• Am I over budget?</p>", unsafe_allow_html=True)
            st.markdown("<p style='color: #FACC15;'>• What's the crypto market doing?</p>", unsafe_allow_html=True)
    
    with col4:
        with st.popover("📊 Context", use_container_width=True):
            st.markdown("<p style='color: #FFFFFF; font-weight: 600;'>Available Data:</p>", unsafe_allow_html=True)
            if context_data:
                for key, value in context_data.items():
                    if value:
                        st.markdown(f"<p style='color: #14B8A6;'>✅ {key.replace('_', ' ').title()}</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='color: #FACC15;'>No context data loaded</p>", unsafe_allow_html=True)
    
    # Greeting message placed after buttons with Mansa Capital styling
    st.markdown("""
    <div style='background: linear-gradient(135deg, #111827 0%, #0A0A0A 100%); 
                padding: 1.5rem; border-radius: 12px; margin: 1.5rem 0; 
                border-left: 4px solid #14B8A6; box-shadow: 0 4px 12px rgba(20, 184, 166, 0.2);'>
        <p style='color: #FFFFFF; font-size: 1.1rem; margin: 0;'>
            👋 <strong style='color: #FACC15;'>Hi, I'm Bentley</strong> - your AI financial assistant.
        </p>
        <p style='color: #FFFFFF; font-size: 0.95rem; margin: 0.5rem 0 0 0;'>
            Ask me anything about your portfolio, budget, or the markets!
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # User input placed right after greeting using form and text_input
    with st.form(key='chat_form', clear_on_submit=True):
        col1, col2 = st.columns([6, 1])
        with col1:
            user_input = st.text_input(
                "Your message:",
                placeholder="Ask me anything about your finances...",
                label_visibility="collapsed",
                key="chat_input_field"
            )
        with col2:
            submit_button = st.form_submit_button("Send 💬", use_container_width=True)
    
    # Process input if submitted
    if submit_button and user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input
        })
        
        # Get AI response
        response = chatbot.get_response(user_input, context_data)
        
        # Add response to history
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response
        })
        
        st.rerun()
    
    # Chat history removed per admin request - history still maintained in session state for context
    



def get_chatbot_context_data() -> Dict:
    """
    Gather context data from the application for the chatbot.
    This should be called from streamlit_app.py to provide relevant data.
    
    Returns:
        Dictionary with portfolio_summary, budget_summary, market_data, etc.
    """
    context = {}
    
    # TODO: Integrate with actual data sources
    # For now, return placeholder data
    
    context['portfolio_summary'] = "Portfolio data will be integrated here"
    context['budget_summary'] = "Budget data will be integrated here"
    context['market_data'] = "Market data will be integrated here"
    
    return context
