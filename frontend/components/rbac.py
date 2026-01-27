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
    """User roles in the system with database-level access"""
    CLIENT = "client"          # Budgets + transactions (mydb)
    INVESTOR = "investor"      # Read-only: bbbot1 prices, fundamentals, technicals
    ANALYST = "analyst"        # mansa_quant + mlflow_db (experiments, sentiment)
    ADMIN = "admin"            # Full CRUD across all schemas
    PARTNER = "partner"        # Supabase Stripe/KYC + Lovable Cloud functions


class Permission(Enum):
    """Database-level and feature permissions"""
    # CLIENT: mydb (Budgets + Transactions)
    CLIENT_READ_BUDGETS = "client_read_budgets"
    CLIENT_READ_TRANSACTIONS = "client_read_transactions"
    CLIENT_WRITE_BUDGETS = "client_write_budgets"
    CLIENT_WRITE_TRANSACTIONS = "client_write_transactions"
    
    # INVESTOR: bbbot1 read-only (Prices, Fundamentals, Technicals)
    INVESTOR_READ_PRICES = "investor_read_prices"  # bbbot1.prices_daily
    INVESTOR_READ_FUNDAMENTALS = "investor_read_fundamentals"  # bbbot1.fundamentals_raw
    INVESTOR_READ_TECHNICALS = "investor_read_technicals"  # bbbot1.technicals_raw
    INVESTOR_READ_PERFORMANCE = "investor_read_performance"  # Bot performance metrics
    
    # ANALYST: mansa_quant + mlflow_db (Trading signals, experiments, sentiment)
    ANALYST_READ_MANSA_QUANT = "analyst_read_mansa_quant"
    ANALYST_WRITE_MANSA_QUANT = "analyst_write_mansa_quant"
    ANALYST_READ_MLFLOW = "analyst_read_mlflow"  # ML experiments, metrics
    ANALYST_WRITE_MLFLOW = "analyst_write_mlflow"
    ANALYST_READ_SENTIMENT = "analyst_read_sentiment"  # Sentiment pipeline data
    ANALYST_WRITE_SENTIMENT = "analyst_write_sentiment"
    
    # ADMIN: All databases - Full CRUD
    ADMIN_READ_MANSA_BOT = "admin_read_mansa_bot"  # Airflow metadata
    ADMIN_WRITE_MANSA_BOT = "admin_write_mansa_bot"
    ADMIN_READ_BBBOT1 = "admin_read_bbbot1"  # Stock data, fundamental data
    ADMIN_WRITE_BBBOT1 = "admin_write_bbbot1"
    ADMIN_READ_MLFLOW = "admin_read_mlflow"  # ML experiments
    ADMIN_WRITE_MLFLOW = "admin_write_mlflow"
    ADMIN_READ_MANSA_QUANT = "admin_read_mansa_quant"  # Trading signals
    ADMIN_WRITE_MANSA_QUANT = "admin_write_mansa_quant"
    ADMIN_READ_MYDB = "admin_read_mydb"  # Budgets, transactions
    ADMIN_WRITE_MYDB = "admin_write_mydb"
    
    # PARTNER: External integrations
    PARTNER_STRIPE = "partner_stripe"  # Stripe integration for payments
    PARTNER_KYC = "partner_kyc"  # KYC verification
    PARTNER_LOVABLE = "partner_lovable"  # Lovable Cloud functions
    
    # Page access (maintained for UI navigation)
    VIEW_DASHBOARD = "view_dashboard"
    VIEW_BUDGET = "view_budget"
    VIEW_ANALYSIS = "view_analysis"
    VIEW_CRYPTO = "view_crypto"
    VIEW_BROKER_TRADING = "view_broker_trading"
    VIEW_TRADING_BOT = "view_trading_bot"


# Role-Permission mapping based on database and feature access
# GUEST removed: All users now have defined roles with database-level access
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.CLIENT: {
        # mydb: Budgets + Transactions
        Permission.CLIENT_READ_BUDGETS,
        Permission.CLIENT_READ_TRANSACTIONS,
        Permission.CLIENT_WRITE_BUDGETS,
        Permission.CLIENT_WRITE_TRANSACTIONS,
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_BUDGET,
    },
    UserRole.INVESTOR: {
        # bbbot1 read-only: prices, fundamentals, technicals + performance metrics
        Permission.INVESTOR_READ_PRICES,
        Permission.INVESTOR_READ_FUNDAMENTALS,
        Permission.INVESTOR_READ_TECHNICALS,
        Permission.INVESTOR_READ_PERFORMANCE,
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_ANALYSIS,
        Permission.VIEW_BROKER_TRADING,
    },
    UserRole.ANALYST: {
        # mansa_quant (trading signals) + mlflow_db (experiments, sentiment)
        Permission.ANALYST_READ_MANSA_QUANT,
        Permission.ANALYST_WRITE_MANSA_QUANT,
        Permission.ANALYST_READ_MLFLOW,
        Permission.ANALYST_WRITE_MLFLOW,
        Permission.ANALYST_READ_SENTIMENT,
        Permission.ANALYST_WRITE_SENTIMENT,
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_ANALYSIS,
    },
    UserRole.ADMIN: {
        # Full CRUD access to all databases: mansa_bot, bbbot1, mlflow_db, mansa_quant, mydb
        # mansa_bot (Airflow metadata)
        Permission.ADMIN_READ_MANSA_BOT,
        Permission.ADMIN_WRITE_MANSA_BOT,
        # bbbot1 (Stock data, fundamentals)
        Permission.ADMIN_READ_BBBOT1,
        Permission.ADMIN_WRITE_BBBOT1,
        # mlflow_db (ML experiments)
        Permission.ADMIN_READ_MLFLOW,
        Permission.ADMIN_WRITE_MLFLOW,
        # mansa_quant (Trading signals)
        Permission.ADMIN_READ_MANSA_QUANT,
        Permission.ADMIN_WRITE_MANSA_QUANT,
        # mydb (Budgets, transactions)
        Permission.ADMIN_READ_MYDB,
        Permission.ADMIN_WRITE_MYDB,
        # All page access
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_BUDGET,
        Permission.VIEW_ANALYSIS,
        Permission.VIEW_CRYPTO,
        Permission.VIEW_BROKER_TRADING,
        Permission.VIEW_TRADING_BOT,
    },
    UserRole.PARTNER: {
        # External integrations: Stripe, KYC, Lovable Cloud functions
        Permission.PARTNER_STRIPE,
        Permission.PARTNER_KYC,
        Permission.PARTNER_LOVABLE,
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
        """Check if user can access a specific page number (1-6)"""
        page_permissions = {
            1: Permission.VIEW_DASHBOARD,
            2: Permission.VIEW_BUDGET,
            3: Permission.VIEW_ANALYSIS,
            4: Permission.VIEW_CRYPTO,
            5: Permission.VIEW_BROKER_TRADING,
            6: Permission.VIEW_TRADING_BOT,
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
    DEMO_USERS = {
        'guest': {
            'password_hash': hashlib.sha256('guest123'.encode()).hexdigest(),
            'role': UserRole.GUEST,
            'kyc_completed': True,  # Dev/testing has KYC
            'investment_agreement_signed': True,  # Dev/testing has agreement
            'kyc_date': datetime.now() - timedelta(days=1),
            'agreement_date': datetime.now() - timedelta(days=1),
            'agreement_type': 'dev_testing',
            'email': 'dev@bentleybot.com',
        },
        'client': {
            'password_hash': hashlib.sha256('client123'.encode()).hexdigest(),
            'role': UserRole.CLIENT,
            'kyc_completed': True,
            'investment_agreement_signed': True,
            'kyc_date': datetime.now() - timedelta(days=30),
            'agreement_date': datetime.now() - timedelta(days=30),
            'agreement_type': 'asset_mgmt',  # Asset Management Agreement
            'email': 'client@bentleybot.com',
        },
        'investor': {
            'password_hash': hashlib.sha256('investor123'.encode()).hexdigest(),
            'role': UserRole.INVESTOR,
            'kyc_completed': True,
            'investment_agreement_signed': True,
            'kyc_date': datetime.now() - timedelta(days=60),
            'agreement_date': datetime.now() - timedelta(days=60),
            'agreement_type': 'investor_mgmt',  # Investor Management Agreement
            'email': 'investor@bentleybot.com',
        },
        'admin': {
            'password_hash': hashlib.sha256('admin123'.encode()).hexdigest(),
            'role': UserRole.ADMIN,
            'kyc_completed': True,
            'investment_agreement_signed': True,
            'kyc_date': datetime.now() - timedelta(days=90),
            'agreement_date': datetime.now() - timedelta(days=90),
            'agreement_type': 'admin',
            'email': 'admin@bentleybot.com',
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
        **Development/Testing:**
        - Username: `guest`
        - Password: `guest123`
        - Access: All pages (1-6)
        
        **Client User (Pages 1-4):**
        - Username: `client`
        - Password: `client123`
        - Agreement: Asset Management
        
        **Investor User (Pages 1-5):**
        - Username: `investor`
        - Password: `investor123`
        - Agreement: Investor Management
        
        **Admin (Production - GCP):**
        - Username: `admin`
        - Password: `admin123`
        - Access: Full RW (All pages + patches)
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
