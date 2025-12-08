"""
Role-Based Access Control (RBAC) System for Bentley Budget Bot
Manages user authentication, roles, and permissions for investment services
"""

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
    VIEW_PORTFOLIO = "view_portfolio"
    VIEW_ANALYSIS = "view_analysis"
    VIEW_CONNECTIONS = "view_connections"
    TRADE_EXECUTION = "trade_execution"
    VIEW_FUNDS = "view_funds"
    ADMIN_PANEL = "admin_panel"


# Role-Permission mapping
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.GUEST: {
        Permission.VIEW_PORTFOLIO,
    },
    UserRole.CLIENT: {
        Permission.VIEW_PORTFOLIO,
        Permission.VIEW_ANALYSIS,
        Permission.VIEW_CONNECTIONS,
        Permission.VIEW_FUNDS,
    },
    UserRole.INVESTOR: {
        Permission.VIEW_PORTFOLIO,
        Permission.VIEW_ANALYSIS,
        Permission.VIEW_CONNECTIONS,
        Permission.VIEW_FUNDS,
        Permission.TRADE_EXECUTION,
    },
    UserRole.ADMIN: {
        Permission.VIEW_PORTFOLIO,
        Permission.VIEW_ANALYSIS,
        Permission.VIEW_CONNECTIONS,
        Permission.VIEW_FUNDS,
        Permission.TRADE_EXECUTION,
        Permission.ADMIN_PANEL,
    },
}


class User:
    """User model with authentication and compliance tracking"""
    
    def __init__(
        self,
        username: str,
        role: UserRole,
        kyc_completed: bool = False,
        investment_agreement_signed: bool = False,
        kyc_date: Optional[datetime] = None,
        agreement_date: Optional[datetime] = None,
        email: Optional[str] = None,
    ):
        self.username = username
        self.role = role
        self.kyc_completed = kyc_completed
        self.investment_agreement_signed = investment_agreement_signed
        self.kyc_date = kyc_date
        self.agreement_date = agreement_date
        self.email = email
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return permission in ROLE_PERMISSIONS.get(self.role, set())
    
    def can_view_connections(self) -> bool:
        """Check if user can view broker connections (requires KYC and agreement)"""
        return (
            self.has_permission(Permission.VIEW_CONNECTIONS)
            and self.kyc_completed
            and self.investment_agreement_signed
        )
    
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
        )


class RBACManager:
    """Manages authentication and authorization"""
    
    # Demo users for testing (in production, use database)
    DEMO_USERS = {
        'guest': {
            'password_hash': hashlib.sha256('guest123'.encode()).hexdigest(),
            'role': UserRole.GUEST,
            'kyc_completed': False,
            'investment_agreement_signed': False,
        },
        'client': {
            'password_hash': hashlib.sha256('client123'.encode()).hexdigest(),
            'role': UserRole.CLIENT,
            'kyc_completed': True,
            'investment_agreement_signed': True,
            'kyc_date': datetime.now() - timedelta(days=30),
            'agreement_date': datetime.now() - timedelta(days=30),
            'email': 'client@bentleybot.com',
        },
        'investor': {
            'password_hash': hashlib.sha256('investor123'.encode()).hexdigest(),
            'role': UserRole.INVESTOR,
            'kyc_completed': True,
            'investment_agreement_signed': True,
            'kyc_date': datetime.now() - timedelta(days=60),
            'agreement_date': datetime.now() - timedelta(days=60),
            'email': 'investor@bentleybot.com',
        },
        'admin': {
            'password_hash': hashlib.sha256('admin123'.encode()).hexdigest(),
            'role': UserRole.ADMIN,
            'kyc_completed': True,
            'investment_agreement_signed': True,
            'kyc_date': datetime.now() - timedelta(days=90),
            'agreement_date': datetime.now() - timedelta(days=90),
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
    def require_permission(permission: Permission) -> bool:
        """Check if current user has required permission"""
        if not RBACManager.is_authenticated():
            return False
        
        user = RBACManager.get_current_user()
        return user.has_permission(permission) if user else False
    
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
        **Guest User:**
        - Username: `guest`
        - Password: `guest123`
        
        **Client User:**
        - Username: `client`
        - Password: `client123`
        
        **Investor User:**
        - Username: `investor`
        - Password: `investor123`
        
        **Admin User:**
        - Username: `admin`
        - Password: `admin123`
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
        
        # Compliance status
        st.sidebar.markdown("**📋 Compliance:**")
        
        kyc_status = "✅" if user.kyc_completed else "❌"
        st.sidebar.markdown(f"- KYC: {kyc_status}")
        
        agreement_status = "✅" if user.investment_agreement_signed else "❌"
        st.sidebar.markdown(f"- Agreement: {agreement_status}")
        
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
