#!/usr/bin/env python3
"""
Appwrite RBAC Setup Script for Mansa Capital
Sets up teams, roles, and permissions in Appwrite to match MySQL schema
"""

import os
import json
from appwrite.client import Client
from appwrite.services.teams import Teams
from appwrite.services.users import Users
from appwrite.services.databases import Databases
from appwrite.exception import AppwriteException
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AppwriteRBACManager:
    def __init__(self):
        # Initialize Appwrite client
        self.client = Client()
        self.client.set_endpoint(os.getenv('APPWRITE_ENDPOINT', 'https://cloud.appwrite.io/v1'))
        self.client.set_project(os.getenv('APPWRITE_PROJECT_ID'))
        self.client.set_key(os.getenv('APPWRITE_API_KEY'))
        
        self.teams = Teams(self.client)
        self.users = Users(self.client)
        self.databases = Databases(self.client)
        
        # Mansa Capital team configuration
        self.mansa_teams = {
            'admin_team': {
                'name': 'Admin',
                'roles': ['owner']  # Appwrite owner role
            },
            'investor_team': {
                'name': 'Investor',
                'roles': ['guest']  # Read-only access
            },
            'client_team': {
                'name': 'Client', 
                'roles': ['guest']  # Read own data only
            },
            'analyst_team': {
                'name': 'Analyst',
                'roles': ['developer']  # Read/write analytics
            },
            'devops_team': {
                'name': 'DevOps',
                'roles': ['developer']  # System management
            }
        }
        
        # Collection permissions mapping
        self.collection_permissions = {
            'portfolios': {
                'read': ['role:admin', 'team:investor_team'],
                'write': ['role:admin'],
                'create': ['role:admin'],
                'update': ['role:admin'],
                'delete': ['role:admin']
            },
            'transactions': {
                'read': ['role:admin', 'team:investor_team', 'team:client_team'],
                'write': ['role:admin'],
                'create': ['role:admin'],
                'update': ['role:admin'],
                'delete': ['role:admin']
            },
            'bot_metrics': {
                'read': ['role:admin', 'team:investor_team'],
                'write': ['role:admin'],
                'create': ['role:admin'],
                'update': ['role:admin'],
                'delete': ['role:admin']
            },
            'budgets': {
                'read': ['role:admin', 'team:client_team'],
                'write': ['role:admin', 'user:self'],
                'create': ['role:admin', 'user:self'],
                'update': ['role:admin', 'user:self'],
                'delete': ['role:admin']
            },
            'auditlogs': {
                'read': ['role:admin', 'user:self'],
                'write': ['role:admin'],
                'create': ['role:admin'],
                'update': ['role:admin'],
                'delete': ['role:admin']
            },
            'fundamentals': {
                'read': ['role:admin', 'team:analyst_team'],
                'write': ['role:admin', 'team:analyst_team'],
                'create': ['role:admin', 'team:analyst_team'],
                'update': ['role:admin', 'team:analyst_team'],
                'delete': ['role:admin']
            },
            'technicals': {
                'read': ['role:admin', 'team:analyst_team'],
                'write': ['role:admin', 'team:analyst_team'],
                'create': ['role:admin', 'team:analyst_team'],
                'update': ['role:admin', 'team:analyst_team'],
                'delete': ['role:admin']
            },
            'sentiment': {
                'read': ['role:admin', 'team:analyst_team'],
                'write': ['role:admin', 'team:analyst_team'],
                'create': ['role:admin', 'team:analyst_team'],
                'update': ['role:admin', 'team:analyst_team'],
                'delete': ['role:admin']
            },
            'experiments': {
                'read': ['role:admin', 'team:analyst_team'],
                'write': ['role:admin', 'team:analyst_team'],
                'create': ['role:admin', 'team:analyst_team'],
                'update': ['role:admin', 'team:analyst_team'],
                'delete': ['role:admin']
            },
            'mlflow_db': {
                'read': ['role:admin', 'team:devops_team'],
                'write': ['role:admin', 'team:devops_team'],
                'create': ['role:admin', 'team:devops_team'],
                'update': ['role:admin', 'team:devops_team'],
                'delete': ['role:admin', 'team:devops_team']
            },
            'airflow_dags': {
                'read': ['role:admin', 'team:devops_team'],
                'write': ['role:admin', 'team:devops_team'],
                'create': ['role:admin', 'team:devops_team'],
                'update': ['role:admin', 'team:devops_team'],
                'delete': ['role:admin', 'team:devops_team']
            },
            'staging_trades': {
                'read': ['role:admin', 'team:devops_team'],
                'write': ['role:admin', 'team:devops_team'],
                'create': ['role:admin', 'team:devops_team'],
                'update': ['role:admin', 'team:devops_team'],
                'delete': ['role:admin', 'team:devops_team']
            }
        }

    def create_teams(self):
        """Create Mansa Capital teams in Appwrite"""
        created_teams = {}
        
        for team_id, team_config in self.mansa_teams.items():
            try:
                # Check if team already exists
                try:
                    team = self.teams.get(team_id)
                    logger.info(f"Team {team_config['name']} already exists")
                    created_teams[team_id] = team
                except AppwriteException:
                    # Team doesn't exist, create it
                    team = self.teams.create(
                        team_id=team_id,
                        name=team_config['name'],
                        roles=team_config['roles']
                    )
                    logger.info(f"Created team: {team_config['name']} ({team_id})")
                    created_teams[team_id] = team
                    
            except Exception as e:
                logger.error(f"Error creating team {team_config['name']}: {e}")
        
        return created_teams

    def list_teams(self):
        """List all teams in Appwrite"""
        try:
            teams = self.teams.list()
            logger.info("Current Appwrite teams:")
            for team in teams['teams']:
                logger.info(f"- {team['name']} (ID: {team['$id']})")
            return teams
        except Exception as e:
            logger.error(f"Error listing teams: {e}")
            return None

    def get_collection_permissions_string(self, collection_name):
        """Generate Appwrite permission strings for a collection"""
        if collection_name not in self.collection_permissions:
            return None
            
        perms = self.collection_permissions[collection_name]
        permission_strings = []
        
        for operation, roles in perms.items():
            for role in roles:
                permission_strings.append(f"{operation}(\"{role}\")")
        
        return permission_strings

    def print_permission_guide(self):
        """Print collection permission configuration guide"""
        logger.info("\n" + "="*60)
        logger.info("APPWRITE COLLECTION PERMISSIONS GUIDE")
        logger.info("="*60)
        logger.info("Copy these permission arrays into your Appwrite collection settings:\n")
        
        for collection_name in self.collection_permissions.keys():
            perms = self.get_collection_permissions_string(collection_name)
            if perms:
                logger.info(f"{collection_name}:")
                logger.info(f"  {json.dumps(perms, indent=2)}")
                logger.info("")

    def verify_setup(self):
        """Verify RBAC setup in Appwrite"""
        logger.info("\n" + "="*50)
        logger.info("MANSA CAPITAL RBAC VERIFICATION")
        logger.info("="*50)
        
        # List teams
        teams = self.list_teams()
        
        # Check if all required teams exist
        if teams:
            existing_team_ids = [team['$id'] for team in teams['teams']]
            missing_teams = []
            
            for team_id in self.mansa_teams.keys():
                if team_id not in existing_team_ids:
                    missing_teams.append(team_id)
            
            if missing_teams:
                logger.warning(f"Missing teams: {missing_teams}")
            else:
                logger.info("✅ All required teams are present")
        
        return teams

def main():
    """Main function to set up Mansa Capital RBAC in Appwrite"""
    
    # Check environment variables
    required_env_vars = ['APPWRITE_ENDPOINT', 'APPWRITE_PROJECT_ID', 'APPWRITE_API_KEY']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("Please set these in your .env file or environment:")
        for var in missing_vars:
            logger.error(f"  export {var}=your_value_here")
        return False
    
    try:
        # Initialize RBAC manager
        rbac_manager = AppwriteRBACManager()
        
        # Create teams
        logger.info("Setting up Mansa Capital teams...")
        teams = rbac_manager.create_teams()
        
        # Verify setup
        rbac_manager.verify_setup()
        
        # Print permission configuration guide
        rbac_manager.print_permission_guide()
        
        logger.info("\n✅ Appwrite RBAC setup completed!")
        logger.info("Next steps:")
        logger.info("1. Create collections in Appwrite console")
        logger.info("2. Apply the permission arrays shown above to each collection")
        logger.info("3. Add users to appropriate teams")
        logger.info("4. Test access with different user roles")
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting up RBAC: {e}")
        return False

if __name__ == "__main__":
    main()