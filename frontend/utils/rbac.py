"""
Role-Based Access Control (RBAC) System for Bentley Budget Bot
Manages user authentication, roles, and permissions for investment services
"""

import os
from dotenv import load_dotenv

# Load environment variables at module import
load_dotenv()

import streamlit as st
from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import hashlib
import json


class UserRole(Enum):
    """User roles in the system"""
    GUEST = "guest"
    CLIENT = "client"
    INVESTOR = "investor"
    ADMIN = "admin"


class Permission(Enum):
    """System permissions"""
    # Page Access Permissions
    VIEW_DASHBOARD = "view_dashboard"  # Page 1: Home Dashboard
    VIEW_BUDGET = "view_budget"  # Page 2: Personal Budget
    VIEW_ANALYSIS = "view_analysis"  # Page 3: Investment Analysis
    VIEW_CRYPTO = "view_crypto"  # Page 4: Live Crypto Dashboard
    VIEW_BROKER_TRADING = "view_broker_trading"  # Page 5: Broker Trading
    VIEW_TRADING_BOT = "view_trading_bot"  # Page 6: Trading Bot
    
    # Feature Permissions
    MANAGE_BUDGET = "manage_budget"
    CONNECT_BANK = "connect_bank"
    TRADE_EXECUTION = "trade_execution"
    ADMIN_PANEL = "admin_panel"
    
    # Legacy aliases for backwards compatibility
    VIEW_PORTFOLIO = "view_dashboard"
    VIEW_CONNECTIONS = "view_broker_trading"
    VIEW_FUNDS = "view_analysis"


# Role-Permission mapping
# GUEST: Pages 1-2 only (Dashboard, Budget) - NO Login required, public access
# CLIENT: Pages 1-4 (Dashboard, Budget, Investment Analysis, Crypto) - Must login to Mansacap.com
# INVESTOR: Pages 1-5 (Dashboard, Budget, Investment Analysis, Crypto, Broker Trading) - KYC + Legal docs
# ADMIN: Full RW access to ALL pages (1-8) including Trading Bot, Plaid Test, Multi-Broker
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.GUEST: {
        # Pages 1-2 ONLY: Dashboard, Budget (no login, public access)
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_BUDGET,
    },
    UserRole.CLIENT: {
        # Pages 1-4: Dashboard, Budget, Investment Analysis, Crypto
        # Requires: Mansacap.com login (asset management agreement implied)
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_BUDGET,
        Permission.VIEW_ANALYSIS,
        Permission.VIEW_CRYPTO,
        Permission.CONNECT_BANK,
    },
    UserRole.INVESTOR: {
        # Pages 1-5: Dashboard, Budget, Investment Analysis, Crypto, Broker Trading
        # Requires: KYC + Legal documents (Investor Management Agreement or PPM)
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_BUDGET,
        Permission.VIEW_ANALYSIS,
        Permission.VIEW_CRYPTO,
        Permission.VIEW_BROKER_TRADING,
        Permission.MANAGE_BUDGET,
        Permission.CONNECT_BANK,
        Permission.TRADE_EXECUTION,
    },
    UserRole.ADMIN: {
        # Full RW access to ALL pages (1-8) + Admin panel
        # Pages: Dashboard, Budget, Investment, Crypto, Broker, Trading Bot, Plaid Test, Multi-Broker
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_BUDGET,
        Permission.VIEW_ANALYSIS,
        Permission.VIEW_CRYPTO,
        Permission.VIEW_BROKER_TRADING,
        Permission.VIEW_TRADING_BOT,
        Permission.MANAGE_BUDGET,
        Permission.CONNECT_BANK,
        Permission.TRADE_EXECUTION,
        Permission.ADMIN_PANEL,
    },
}


class User:
    """User model with authentication and compliance tracking
    
    Agreement Types:
    - CLIENT: Asset Management Agreement
    - INVESTOR: Investor Management Agreement OR Private Placement Memorandum (PPM)
    """
    
    def __init__(
        self,
        username: str,
        role: UserRole,
        kyc_completed: bool = False,
        investment_agreement_signed: bool = False,
        kyc_date: Optional[datetime] = None,
        agreement_date: Optional[datetime] = None,
        email: Optional[str] = None,
        user_id: Optional[int] = None,
        agreement_type: Optional[str] = None,  # "asset_mgmt", "investor_mgmt", "ppm"
    ):
        self.username = username
        self.role = role
        self.kyc_completed = kyc_completed
        self.investment_agreement_signed = investment_agreement_signed
        self.kyc_date = kyc_date
        self.agreement_date = agreement_date
        self.email = email
        self.user_id = user_id or hash(username) % 10000
        self.agreement_type = agreement_type
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return permission in ROLE_PERMISSIONS.get(self.role, set())
    
    def can_view_connections(self) -> bool:
        """Check if user can view broker connections (requires KYC and agreement)"""
        return (
            self.has_permission(Permission.VIEW_BROKER_TRADING)
            and self.kyc_completed
            and self.investment_agreement_signed
        )
    
    def can_access_page(self, page_number: int) -> bool:
        """Check if user can access a specific page number (1-8)
        
        Page mapping:
        1: Dashboard (all roles)
        2: Budget (all roles)
        3: Investment Analysis (CLIENT+, INVESTOR, ADMIN)
        4: Live Crypto (CLIENT+, INVESTOR, ADMIN)
        5: Broker Trading (INVESTOR, ADMIN)
        6: Trading Bot (ADMIN only)
        7: Plaid Test (ADMIN only)
        8: Multi-Broker Trading (ADMIN only)
        """
        page_permissions = {
            1: Permission.VIEW_DASHBOARD,
            2: Permission.VIEW_BUDGET,
            3: Permission.VIEW_ANALYSIS,
            4: Permission.VIEW_CRYPTO,
            5: Permission.VIEW_BROKER_TRADING,
            6: Permission.VIEW_TRADING_BOT,
            # Pages 7-8 also require VIEW_TRADING_BOT (ADMIN only)
            7: Permission.VIEW_TRADING_BOT,
            8: Permission.VIEW_TRADING_BOT,
        }
        permission = page_permissions.get(page_number)
        return self.has_permission(permission) if permission else False
    
    def to_dict(self) -> dict:
        """Convert user to dictionary"""
        return {
            'username': self.username,
            'role': self.role.value,
            'kyc_completed': self.kyc_completed,
            'investment_agreement_signed': self.investment_agreement_signed,
            'kyc_date': self.kyc_date.isoformat() if self.kyc_date else None,
            'agreement_date': self.agreement_date.isoformat() if self.agreement_date else None,
            'email': self.email,
            'user_id': self.user_id,
            'agreement_type': self.agreement_type,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Create user from dictionary"""
        return cls(
            username=data['username'],
            role=UserRole(data['role']),
            kyc_completed=data.get('kyc_completed', False),
            investment_agreement_signed=data.get('investment_agreement_signed', False),
            kyc_date=datetime.fromisoformat(data['kyc_date']) if data.get('kyc_date') else None,
            agreement_date=datetime.fromisoformat(data['agreement_date']) if data.get('agreement_date') else None,
            email=data.get('email'),
            user_id=data.get('user_id'),
            agreement_type=data.get('agreement_type'),
        )


class RBACManager:
    """Manages authentication and authorization
    
    Development/Testing: guest/guest123
    Production (GCP): admin/admin123 for patches
    """
    
    # Demo users for testing (in production, use database)
    # GUEST: Public access (no login required) - Pages 1-2 only
    # CLIENT: Must login to Mansacap.com - Pages 1-4
    # INVESTOR: KYC + Legal docs - Pages 1-5
    # ADMIN: Full access - All pages (1-8)
    DEMO_USERS = {
        'guest': {
            'password_hash': hashlib.sha256('guest123'.encode()).hexdigest(),
            'role': UserRole.GUEST,
            'kyc_completed': False,  # GUEST does NOT complete KYC
            'investment_agreement_signed': False,  # GUEST does NOT sign agreement
            'kyc_date': None,
            'agreement_date': None,
            'agreement_type': None,
            'email': 'guest@mansacap.com',  # Links to Mansacap.com
        },
        'client': {
            'password_hash': hashlib.sha256('client123'.encode()).hexdigest(),
            'role': UserRole.CLIENT,
            'kyc_completed': False,  # CLIENT login only (KYC optional in this version)
            'investment_agreement_signed': False,  # Asset Mgmt agreement implied via Mansacap
            'kyc_date': None,
            'agreement_date': None,
            'agreement_type': 'asset_mgmt',  # Asset Management Agreement
            'email': 'client@mansacap.com',  # Links to Mansacap.com
        },
        'investor': {
            'password_hash': hashlib.sha256('investor123'.encode()).hexdigest(),
            'role': UserRole.INVESTOR,
            'kyc_completed': True,  # INVESTOR must complete KYC
            'investment_agreement_signed': True,  # INVESTOR must sign legal docs
            'kyc_date': datetime.now() - timedelta(days=60),
            'agreement_date': datetime.now() - timedelta(days=60),
            'agreement_type': 'investor_mgmt',  # Investor Management Agreement or PPM
            'email': 'investor@mansacap.com',
        },
        'admin': {
            'password_hash': hashlib.sha256('admin123'.encode()).hexdigest(),
            'role': UserRole.ADMIN,
            'kyc_completed': True,
            'investment_agreement_signed': True,
            'kyc_date': datetime.now() - timedelta(days=90),
            'agreement_date': datetime.now() - timedelta(days=90),
            'agreement_type': 'admin',
            'email': 'winston@bentleybot.com',
        },
    }
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def authenticate(username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user_data = RBACManager.DEMO_USERS.get(username)
        
        if not user_data:
            return None
        
        password_hash = RBACManager.hash_password(password)
        if password_hash != user_data['password_hash']:
            return None
        
        return User(
            username=username,
            role=user_data['role'],
            kyc_completed=user_data.get('kyc_completed', False),
            investment_agreement_signed=user_data.get('investment_agreement_signed', False),
            kyc_date=user_data.get('kyc_date'),
            agreement_date=user_data.get('agreement_date'),
            email=user_data.get('email'),
            agreement_type=user_data.get('agreement_type'),
        )
    
    @staticmethod
    def init_session_state():
        """Initialize authentication session state"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'current_user' not in st.session_state:
            st.session_state.current_user = None
    
    @staticmethod
    def login(username: str, password: str) -> bool:
        """Login user and store in session state"""
        user = RBACManager.authenticate(username, password)
        
        if user:
            st.session_state.authenticated = True
            st.session_state.current_user = user
            return True
        
        return False
    
    @staticmethod
    def logout():
        """Logout current user"""
        st.session_state.authenticated = False
        st.session_state.current_user = None
    
    @staticmethod
    def get_current_user() -> Optional[User]:
        """Get currently logged in user"""
        return st.session_state.get('current_user')
    
    @staticmethod
    def is_authenticated() -> bool:
        """Check if user is authenticated"""
        return st.session_state.get('authenticated', False)
    
    @staticmethod
    def has_permission(permission: Permission) -> bool:
        """Check if current user has required permission"""
        if not RBACManager.is_authenticated():
            return False
        
        user = RBACManager.get_current_user()
        return user.has_permission(permission) if user else False
    
    @staticmethod
    def require_permission(permission: Permission) -> bool:
        """Check if current user has required permission (alias for has_permission)"""
        return RBACManager.has_permission(permission)
    
    @staticmethod
    def require_connections_access() -> bool:
        """Check if current user can access broker connections"""
        if not RBACManager.is_authenticated():
            return False
        
        user = RBACManager.get_current_user()
        return user.can_view_connections() if user else False


def show_login_form():
    """Display login form in sidebar"""
    st.sidebar.markdown("### 🔐 Login")
    
    with st.sidebar.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if RBACManager.login(username, password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")
    
    # Show demo credentials
    with st.sidebar.expander("🔑 Demo Credentials"):
        st.markdown("""
        **GUEST (Public Access - Pages 1-2):**
        - Username: `guest`
        - Password: `guest123`
        - Access: Dashboard, Budget (no login via Mansacap.com)
        
        **CLIENT (Pages 1-4):**
        - Username: `client`
        - Password: `client123`
        - Login: Via Mansacap.com
        - Access: Dashboard, Budget, Investment Analysis, Crypto
        - Agreement: Asset Management
        
        **INVESTOR (Pages 1-5):**
        - Username: `investor`
        - Password: `investor123`
        - Requirements: KYC + Legal documents
        - Access: Dashboard, Budget, Investment Analysis, Crypto, Broker Trading
        - Agreement: Investor Management or PPM
        
        **ADMIN (All Pages 1-8):**
        - Username: `admin`
        - Password: `admin123`
        - Access: All pages including Trading Bot, Plaid Test, Multi-Broker
        """)
        
        st.info("""
        **Bot Performance Display:**
        - Bot info (name & performance) will be linked on Home Page (Page 1)
        - Full Bot management (Page 6), Plaid Test (Page 7), Multi-Broker (Page 8) - ADMIN only
        """)



def show_user_info():
    """Display current user info in sidebar"""
    user = RBACManager.get_current_user()
    
    if user:
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**👤 User:** {user.username}")
        st.sidebar.markdown(f"**🎭 Role:** {user.role.value.title()}")
        
        if user.email:
            st.sidebar.markdown(f"**📧 Email:** {user.email}")
        
        # Page access summary
        accessible_pages = [i for i in range(1, 7) if user.can_access_page(i)]
        st.sidebar.markdown(f"**📄 Page Access:** {len(accessible_pages)}/6")
        
        # Compliance status
        st.sidebar.markdown("**📋 Compliance:**")
        
        kyc_status = "✅" if user.kyc_completed else "❌"
        st.sidebar.markdown(f"- KYC: {kyc_status}")
        
        agreement_status = "✅" if user.investment_agreement_signed else "❌"
        agreement_type_display = {
            'asset_mgmt': 'Asset Mgmt',
            'investor_mgmt': 'Investor Mgmt',
            'ppm': 'PPM',
            'dev_testing': 'Dev/Testing',
            'admin': 'Admin',
        }.get(user.agreement_type, 'None')
        st.sidebar.markdown(f"- Agreement: {agreement_status} ({agreement_type_display})")
        
        if st.sidebar.button("Logout"):
            RBACManager.logout()
            st.rerun()


def require_authentication(func):
    """Decorator to require authentication for a function"""
    def wrapper(*args, **kwargs):
        RBACManager.init_session_state()
        
        if not RBACManager.is_authenticated():
            st.warning("⚠️ Please login to access this feature")
            show_login_form()
            return
        
        return func(*args, **kwargs)
    
    return wrapper


def require_permission_decorator(permission: Permission):
    """Decorator to require specific permission"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            RBACManager.init_session_state()
            
            if not RBACManager.is_authenticated():
                st.warning("⚠️ Please login to access this feature")
                show_login_form()
                return
            
            if not RBACManager.require_permission(permission):
                st.error(f"❌ You don't have permission to access this feature. Required: {permission.value}")
                return
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def show_permission_denied(required_permission: str):
    """Show permission denied message with requirements"""
    st.error("🚫 Access Denied")
    st.warning(f"**Required Permission:** {required_permission}")
    
    user = RBACManager.get_current_user()
    
    if user:
        st.info(f"""
        **Your Current Access Level:**
        - Role: {user.role.value.title()}
        - KYC Completed: {'Yes' if user.kyc_completed else 'No'}
        - Investment Agreement: {'Yes' if user.investment_agreement_signed else 'No'}
        """)
        
        if not user.kyc_completed or not user.investment_agreement_signed:
            st.warning("""
            **To access broker connections and fund displays, you need:**
            1. ✅ Complete KYC (Know Your Customer) verification
            2. ✅ Sign Investment Management Agreement
            
            Please contact support to complete your onboarding.
            """)
