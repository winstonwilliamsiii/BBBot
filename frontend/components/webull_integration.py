"""
Webull API Integration Module for Bentley Budget Bot
Handles authentication, positions, orders, and market data from Webull

NOTE: Webull authentication is SEPARATE from Appwrite.
- Appwrite: Handles YOUR app's user authentication (login to BBBot)
- Webull: Handles broker-level authentication (access to trading account)

The MFA flow happens at runtime when user connects their Webull account.
This is NOT an Appwrite Function - it runs client-side in Streamlit.
"""

import os
import json
import streamlit as st
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Try to import webull SDK
try:
    from webull import webull, paper_webull
    WEBULL_AVAILABLE = True
except ImportError:
    WEBULL_AVAILABLE = False


class WebullAuthState:
    """Manages Webull authentication state in Streamlit session"""
    
    # Session state keys
    STATE_KEY = "webull_auth_state"
    MFA_PENDING_KEY = "webull_mfa_pending"
    DEVICE_ID_KEY = "webull_device_id"
    ACCESS_TOKEN_KEY = "webull_access_token"
    
    @staticmethod
    def is_logged_in() -> bool:
        """Check if user is logged into Webull"""
        return st.session_state.get(WebullAuthState.STATE_KEY) == "logged_in"
    
    @staticmethod
    def is_mfa_pending() -> bool:
        """Check if MFA verification is pending"""
        return st.session_state.get(WebullAuthState.MFA_PENDING_KEY, False)
    
    @staticmethod
    def set_logged_in(device_id: str, access_token: str = None):
        """Mark user as logged in"""
        st.session_state[WebullAuthState.STATE_KEY] = "logged_in"
        st.session_state[WebullAuthState.DEVICE_ID_KEY] = device_id
        st.session_state[WebullAuthState.MFA_PENDING_KEY] = False
        if access_token:
            st.session_state[WebullAuthState.ACCESS_TOKEN_KEY] = access_token
    
    @staticmethod
    def set_mfa_pending(pending: bool = True):
        """Set MFA pending status"""
        st.session_state[WebullAuthState.MFA_PENDING_KEY] = pending
    
    @staticmethod
    def logout():
        """Clear all Webull auth state"""
        for key in [WebullAuthState.STATE_KEY, WebullAuthState.MFA_PENDING_KEY,
                    WebullAuthState.DEVICE_ID_KEY, WebullAuthState.ACCESS_TOKEN_KEY]:
            if key in st.session_state:
                del st.session_state[key]


class WebullClient:
    """
    Webull API Client with MFA support
    
    Authentication Flow:
    1. User enters phone/email + password
    2. Call get_mfa_code() - Webull sends verification code
    3. User enters MFA code
    4. Call login_with_mfa() - Complete authentication
    5. Access positions, orders, market data
    """
    
    def __init__(self, paper_trading: bool = False):
        """
        Initialize Webull client
        
        Args:
            paper_trading: If True, use paper trading API
        """
        if not WEBULL_AVAILABLE:
            raise ImportError("Webull SDK not installed. Run: pip install webull")
        
        self.paper_trading = paper_trading
        self._wb = paper_webull() if paper_trading else webull()
        self._logged_in = False
        
        # Load credentials from environment
        self.username = os.getenv("WEBULL_USERNAME")
        self.password = os.getenv("WEBULL_PASSWORD")
        self.phone = os.getenv("WEBULL_PHONE")
        self.trade_pin = os.getenv("WEBULL_TRADE_PIN")
        self.device_id = os.getenv("WEBULL_DEVICE_ID")
        
        # Restore device ID if saved
        if self.device_id:
            self._wb.set_did(self.device_id)
    
    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated"""
        return self._logged_in or WebullAuthState.is_logged_in()
    
    # =========================================
    # AUTHENTICATION METHODS
    # =========================================
    
    def request_mfa_code(self, method: str = "phone") -> Tuple[bool, str]:
        """
        Request MFA verification code from Webull
        
        Args:
            method: "phone" or "email"
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if method == "phone":
                # For phone, username should be the phone number with country code
                phone = self.phone or self.username
                result = self._wb.get_mfa(phone)
            else:
                # For email
                result = self._wb.get_mfa(self.username)
            
            WebullAuthState.set_mfa_pending(True)
            return True, "Verification code sent! Check your phone/email."
            
        except Exception as e:
            return False, f"Failed to send MFA code: {str(e)}"
    
    def login_with_mfa(self, mfa_code: str) -> Tuple[bool, str]:
        """
        Complete login with MFA verification code
        
        Args:
            mfa_code: 6-digit verification code
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            result = self._wb.login(
                username=self.phone or self.username,
                password=self.password,
                device_name="BentleyBudgetBot",
                mfa=mfa_code
            )
            
            if result and 'accessToken' in result:
                self._logged_in = True
                device_id = self._wb.get_did()
                WebullAuthState.set_logged_in(device_id, result.get('accessToken'))
                
                # Save device ID for future logins
                return True, "Successfully logged into Webull!"
            else:
                return False, "Login failed. Please check your credentials."
                
        except Exception as e:
            error_msg = str(e)
            if "too many" in error_msg.lower():
                return False, "Too many login attempts. Please wait and try again."
            return False, f"Login error: {error_msg}"
    
    def login_with_saved_credentials(self) -> Tuple[bool, str]:
        """
        Attempt login using saved device ID (no MFA required if device is remembered)
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if not self.device_id:
                return False, "No saved device ID. MFA login required."
            
            self._wb.set_did(self.device_id)
            result = self._wb.login(
                username=self.phone or self.username,
                password=self.password,
                device_name="BentleyBudgetBot"
            )
            
            if result and 'accessToken' in result:
                self._logged_in = True
                WebullAuthState.set_logged_in(self.device_id, result.get('accessToken'))
                return True, "Logged in with saved credentials!"
            else:
                return False, "Saved login failed. MFA may be required."
                
        except Exception as e:
            return False, f"Auto-login failed: {str(e)}"
    
    def logout(self):
        """Logout from Webull"""
        try:
            self._wb.logout()
        except:
            pass
        self._logged_in = False
        WebullAuthState.logout()
    
    # =========================================
    # ACCOUNT & POSITIONS
    # =========================================
    
    def get_account_info(self) -> Optional[Dict]:
        """Get account information"""
        if not self.is_authenticated:
            return None
        try:
            return self._wb.get_account()
        except Exception as e:
            st.error(f"Failed to get account info: {e}")
            return None
    
    def get_positions(self) -> List[Dict]:
        """Get current positions"""
        if not self.is_authenticated:
            return []
        try:
            positions = self._wb.get_positions()
            return positions if positions else []
        except Exception as e:
            st.error(f"Failed to get positions: {e}")
            return []
    
    def get_portfolio_value(self) -> Optional[float]:
        """Get total portfolio value"""
        account = self.get_account_info()
        if account:
            return float(account.get('netLiquidation', 0))
        return None
    
    def get_cash_balance(self) -> Optional[float]:
        """Get available cash balance"""
        account = self.get_account_info()
        if account:
            return float(account.get('cashBalance', 0))
        return None
    
    # =========================================
    # ORDERS
    # =========================================
    
    def get_orders(self, status: str = "all") -> List[Dict]:
        """
        Get orders
        
        Args:
            status: "all", "open", "filled", "cancelled"
        """
        if not self.is_authenticated:
            return []
        try:
            if status == "open":
                return self._wb.get_current_orders() or []
            elif status == "filled":
                return self._wb.get_history_orders(status="Filled") or []
            else:
                return self._wb.get_history_orders() or []
        except Exception as e:
            st.error(f"Failed to get orders: {e}")
            return []
    
    def place_order(
        self,
        symbol: str,
        action: str,  # "BUY" or "SELL"
        quantity: int,
        order_type: str = "MKT",  # "MKT", "LMT", "STP", "STP LMT"
        price: float = None,
        time_in_force: str = "GTC"  # "GTC", "DAY", "IOC"
    ) -> Tuple[bool, str]:
        """
        Place an order (requires trade PIN)
        
        Returns:
            Tuple of (success: bool, order_id or error message)
        """
        if not self.is_authenticated:
            return False, "Not authenticated"
        
        if not self.trade_pin:
            return False, "Trade PIN not set. Add WEBULL_TRADE_PIN to .env"
        
        try:
            # Get stock ID for symbol
            stock = self._wb.get_ticker(symbol)
            if not stock:
                return False, f"Symbol {symbol} not found"
            
            ticker_id = stock.get('tickerId')
            
            if order_type == "MKT":
                result = self._wb.place_order(
                    stock=ticker_id,
                    tId=ticker_id,
                    price=0,
                    action=action,
                    orderType='MKT',
                    enforce=time_in_force,
                    quant=quantity
                )
            else:
                if price is None:
                    return False, "Price required for limit orders"
                result = self._wb.place_order(
                    stock=ticker_id,
                    tId=ticker_id,
                    price=price,
                    action=action,
                    orderType=order_type,
                    enforce=time_in_force,
                    quant=quantity
                )
            
            if result and 'orderId' in result:
                return True, result['orderId']
            else:
                return False, "Order placement failed"
                
        except Exception as e:
            return False, f"Order error: {str(e)}"
    
    # =========================================
    # MARKET DATA (No auth required)
    # =========================================
    
    def get_quote(self, symbol: str) -> Optional[Dict]:
        """Get real-time quote for a symbol (no auth required)"""
        try:
            return self._wb.get_quote(symbol)
        except Exception as e:
            return None
    
    def get_analysis(self, symbol: str) -> Optional[Dict]:
        """Get analyst ratings and price targets"""
        try:
            return self._wb.get_analysis(symbol)
        except Exception as e:
            return None
    
    def get_options_chain(self, symbol: str, expiration: str = None) -> Optional[Dict]:
        """Get options chain for a symbol"""
        try:
            return self._wb.get_options(symbol, expireDate=expiration)
        except Exception as e:
            return None
    
    def get_bars(
        self,
        symbol: str,
        interval: str = "d",  # m1, m5, m15, m30, h1, h2, h4, d, w, m
        count: int = 100
    ) -> Optional[Dict]:
        """Get historical bars/candles"""
        try:
            return self._wb.get_bars(symbol, interval=interval, count=count)
        except Exception as e:
            return None


# =========================================
# STREAMLIT UI COMPONENTS
# =========================================

def render_webull_login_widget():
    """
    Render Webull login widget in Streamlit
    
    Usage in your Streamlit app:
        from frontend.utils.webull_integration import render_webull_login_widget
        render_webull_login_widget()
    """
    if not WEBULL_AVAILABLE:
        st.error("⚠️ Webull SDK not installed. Run: `pip install webull`")
        return
    
    st.subheader("🔐 Webull Connection")
    
    # Check if already logged in
    if WebullAuthState.is_logged_in():
        st.success("✅ Connected to Webull")
        if st.button("Disconnect Webull"):
            client = WebullClient()
            client.logout()
            st.rerun()
        return
    
    client = WebullClient()
    
    # Try auto-login with saved device
    if client.device_id and not WebullAuthState.is_mfa_pending():
        with st.spinner("Attempting auto-login..."):
            success, msg = client.login_with_saved_credentials()
            if success:
                st.success(msg)
                st.rerun()
            # If auto-login fails, show manual login
    
    # MFA Flow
    if WebullAuthState.is_mfa_pending():
        st.info("📱 Enter the verification code sent to your phone/email")
        mfa_code = st.text_input("Verification Code", max_chars=6, key="webull_mfa_input")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Verify Code", type="primary"):
                if mfa_code and len(mfa_code) == 6:
                    with st.spinner("Verifying..."):
                        success, msg = client.login_with_mfa(mfa_code)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                else:
                    st.warning("Please enter a 6-digit code")
        with col2:
            if st.button("Cancel"):
                WebullAuthState.set_mfa_pending(False)
                st.rerun()
    else:
        # Initial login - request MFA
        st.write(f"**Account:** {client.username or 'Not configured'}")
        
        if not client.username or not client.password:
            st.warning("⚠️ Webull credentials not found in .env file")
            st.code("""
# Add to your .env file:
WEBULL_USERNAME=your_phone_or_email
WEBULL_PASSWORD=your_password
WEBULL_PHONE=+1XXXXXXXXXX
WEBULL_TRADE_PIN=XXXXXX
            """)
            return
        
        mfa_method = st.radio("Send verification code via:", ["Phone", "Email"], horizontal=True)
        
        if st.button("🔑 Connect Webull Account", type="primary"):
            with st.spinner("Requesting verification code..."):
                success, msg = client.request_mfa_code(mfa_method.lower())
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)


def render_webull_positions_widget():
    """
    Render Webull positions in Streamlit
    """
    if not WebullAuthState.is_logged_in():
        st.info("Connect your Webull account to view positions")
        return
    
    client = WebullClient()
    
    st.subheader("📊 Webull Positions")
    
    with st.spinner("Loading positions..."):
        positions = client.get_positions()
        
        if not positions:
            st.info("No positions found")
            return
        
        # Convert to DataFrame
        import pandas as pd
        df = pd.DataFrame(positions)
        
        # Format columns
        if 'ticker' in df.columns:
            df = df[['ticker', 'position', 'cost', 'lastPrice', 'marketValue', 'unrealizedProfitLoss']]
            df.columns = ['Symbol', 'Shares', 'Cost Basis', 'Price', 'Value', 'P&L']
        
        st.dataframe(df, use_container_width=True)
        
        # Summary metrics
        total_value = client.get_portfolio_value()
        cash = client.get_cash_balance()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Portfolio Value", f"${total_value:,.2f}" if total_value else "N/A")
        with col2:
            st.metric("Cash Balance", f"${cash:,.2f}" if cash else "N/A")
        with col3:
            st.metric("Positions", len(positions))


def render_webull_quote_widget(symbol: str = None):
    """
    Render real-time quote widget (works without login)
    """
    client = WebullClient()
    
    if not symbol:
        symbol = st.text_input("Enter Symbol", value="AAPL", key="webull_quote_symbol")
    
    if symbol:
        quote = client.get_quote(symbol)
        
        if quote:
            col1, col2, col3, col4 = st.columns(4)
            
            price = float(quote.get('close', 0))
            change = float(quote.get('change', 0))
            change_pct = float(quote.get('changeRatio', 0)) * 100
            volume = int(quote.get('volume', 0))
            
            with col1:
                st.metric("Price", f"${price:.2f}")
            with col2:
                st.metric("Change", f"${change:+.2f}", f"{change_pct:+.2f}%")
            with col3:
                st.metric("Volume", f"{volume:,}")
            with col4:
                st.metric("Symbol", symbol.upper())
        else:
            st.error(f"Could not fetch quote for {symbol}")


# =========================================
# HELPER FUNCTIONS
# =========================================

def test_webull_connection() -> Tuple[bool, str]:
    """
    Test Webull SDK installation and basic connectivity
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    if not WEBULL_AVAILABLE:
        return False, "Webull SDK not installed"
    
    try:
        client = WebullClient()
        
        # Test public API (no auth required)
        quote = client.get_quote("AAPL")
        
        if quote and 'close' in quote:
            price = quote.get('close', 'N/A')
            return True, f"SDK working! AAPL price: ${price}"
        else:
            return False, "SDK loaded but quote fetch failed"
            
    except Exception as e:
        return False, f"Connection test failed: {str(e)}"


if __name__ == "__main__":
    # Quick test
    success, msg = test_webull_connection()
    print(f"Webull Test: {'✅' if success else '❌'} {msg}")
