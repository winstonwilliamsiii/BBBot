#!/usr/bin/env python3
"""
Quick Appwrite RBAC Verification Script
Checks current teams and permissions in your Appwrite project
"""

import os
from appwrite.client import Client
from appwrite.services.teams import Teams
from appwrite.services.databases import Databases
from appwrite.exception import AppwriteException
import json

def check_appwrite_rbac():
    """Check current Appwrite RBAC setup"""
    
    # Load environment variables
    endpoint = os.getenv('APPWRITE_ENDPOINT', 'https://cloud.appwrite.io/v1')
    project_id = os.getenv('APPWRITE_PROJECT_ID')
    api_key = os.getenv('APPWRITE_API_KEY')
    
    if not project_id or not api_key:
        print("❌ Missing APPWRITE_PROJECT_ID or APPWRITE_API_KEY")
        print("Please check your .env file or environment variables")
        return False
    
    try:
        # Initialize client
        client = Client()
        client.set_endpoint(endpoint)
        client.set_project(project_id)  
        client.set_key(api_key)
        
        teams_service = Teams(client)
        databases_service = Databases(client)
        
        print("🔍 MANSA CAPITAL APPWRITE RBAC STATUS")
        print("=" * 50)
        
        # Check teams
        print("\n📋 TEAMS:")
        try:
            teams_response = teams_service.list()
            teams = teams_response.get('teams', [])
            
            expected_teams = {
                'admin_team': 'Admin',
                'investor_team': 'Investor', 
                'client_team': 'Client',
                'analyst_team': 'Analyst',
                'devops_team': 'DevOps'
            }
            
            found_teams = {}
            for team in teams:
                team_id = team.get('$id', '')
                team_name = team.get('name', '')
                print(f"  ✅ {team_name} (ID: {team_id})")
                found_teams[team_id] = team_name
            
            # Check for missing teams
            missing_teams = []
            for expected_id, expected_name in expected_teams.items():
                if expected_id not in found_teams:
                    missing_teams.append(f"{expected_name} ({expected_id})")
            
            if missing_teams:
                print(f"\n  ⚠️  Missing teams: {', '.join(missing_teams)}")
            else:
                print("\n  ✅ All required teams found!")
                
        except AppwriteException as e:
            print(f"  ❌ Error fetching teams: {e}")
        
        # Check databases
        print("\n🗄️  DATABASES:")
        try:
            databases_response = databases_service.list()
            databases = databases_response.get('databases', [])
            
            if databases:
                for db in databases:
                    db_id = db.get('$id', '')
                    db_name = db.get('name', '')
                    print(f"  ✅ {db_name} (ID: {db_id})")
            else:
                print("  ⚠️  No databases found")
                
        except AppwriteException as e:
            print(f"  ❌ Error fetching databases: {e}")
        
        # Instructions
        print("\n🚀 NEXT STEPS:")
        print("1. If teams are missing, run: python setup_appwrite_rbac.py")
        print("2. Create your collections in the Appwrite console")
        print("3. Apply the permission arrays from the setup script")
        print("4. Add users to appropriate teams")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("Please check your Appwrite credentials and network connection")
        return False

if __name__ == "__main__":
    # Try to load from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("📁 Loaded .env configuration")
    except ImportError:
        print("💡 Install python-dotenv for automatic .env loading: pip install python-dotenv")
    except:
        pass
    
    check_appwrite_rbac()