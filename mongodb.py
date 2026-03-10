# mongodb.py - MongoDB connection handler for LINKPULSE Analytics
import streamlit as st
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from pymongo.database import Database
from pymongo.collection import Collection
from datetime import datetime, timedelta
from bson.objectid import ObjectId
import certifi
import urllib.parse
from typing import Optional, Dict, Any, List
import time

class MongoDB:
    """MongoDB connection handler for LINKPULSE Analytics"""
    
    def __init__(self):
        """Initialize MongoDB connection"""
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.connect()
    
    def connect(self) -> None:
        """Establish connection to MongoDB Atlas with proper SSL settings"""
        try:
            # Get connection string from Streamlit secrets
            try:
                uri = st.secrets["mongo"]["uri"]
                print("✅ Found MongoDB URI in secrets")
            except Exception as e:
                print(f"❌ Failed to get MongoDB URI from secrets: {e}")
                st.error("MongoDB URI not found in secrets. Please check your Streamlit Cloud secrets configuration.")
                self.client = None
                self.db = None
                return
            
            print("🔄 Attempting to connect to MongoDB...")
            
            # Parse and encode password if needed
            if '@' in uri:
                parts = uri.split('@')
                credentials_part = parts[0].replace('mongodb+srv://', '')
                if ':' in credentials_part:
                    username, password = credentials_part.split(':', 1)
                    # Only encode if password contains special characters
                    if any(c in password for c in ['@', '#', '$', '%', '^', '&', '+', '=', '/', '?']):
                        encoded_password = urllib.parse.quote_plus(password)
                        uri = f"mongodb+srv://{username}:{encoded_password}@{parts[1]}"
                        print("✅ Password encoded for special characters")
            
            # Ensure SSL parameters
            if '?' in uri:
                base_uri = uri.split('?')[0]
                uri = f"{base_uri}?ssl=true&tls=true&tlsAllowInvalidCertificates=true&retryWrites=true&w=majority"
            else:
                uri = f"{uri}?ssl=true&tls=true&tlsAllowInvalidCertificates=true&retryWrites=true&w=majority"
            
            print("🔄 Connecting with SSL enabled...")
            
            # Connect with extended timeouts and SSL options
            self.client = MongoClient(
                uri,
                serverSelectionTimeoutMS=30000,
                connectTimeoutMS=30000,
                socketTimeoutMS=30000,
                tls=True,
                tlsAllowInvalidCertificates=True,
                retryWrites=True,
                retryReads=True
            )
            
            # Force connection to verify
            self.client.admin.command('ping')
            print("✅ Connected to MongoDB Atlas successfully!")
            
            # Get database
            self.db = self.client["linkpulse_db"]
            
            # Test database connection
            if self.db is not None:
                collections = self.db.list_collection_names()
                print(f"📋 Available collections: {collections}")
                self.create_indexes()
                self.ensure_demo_user()
                print("✅ Database setup complete!")
            
        except ConnectionFailure as e:
            error_msg = f"❌ MongoDB Connection Failure: {e}"
            st.error(error_msg)
            print(error_msg)
            print("💡 Check if your IP is whitelisted in MongoDB Atlas")
            self.client = None
            self.db = None
        except Exception as e:
            error_msg = f"❌ MongoDB Connection Error: {e}"
            st.error(error_msg)
            print(error_msg)
            self.client = None
            self.db = None
    
    def is_connected(self) -> bool:
        """Check if MongoDB is connected"""
        return self.db is not None
    
    def ensure_demo_user(self) -> None:
        """Ensure demo user exists in database"""
        users = self.get_users_collection()
        if users is None:
            return
        
        # Check if demo user exists
        demo_user = users.find_one({"username": "demo"})
        
        if not demo_user:
            # Create demo user
            demo_data = {
                "username": "demo",
                "email": "demo@linkpulse.com",
                "password_hash": self.hash_password("demo123"),
                "created_at": datetime.now(),
                "last_login": None
            }
            
            result = users.insert_one(demo_data)
            print(f"✅ Demo user created with ID: {result.inserted_id}")
        else:
            print("✅ Demo user already exists")
    
    def get_users_collection(self) -> Optional[Collection]:
        """Get users collection safely"""
        if self.is_connected() and self.db is not None:
            return self.db["users"]
        return None
    
    def get_sessions_collection(self) -> Optional[Collection]:
        """Get sessions collection safely"""
        if self.is_connected() and self.db is not None:
            return self.db["sessions"]
        return None
    
    def get_analyses_collection(self) -> Optional[Collection]:
        """Get analyses collection safely"""
        if self.is_connected() and self.db is not None:
            return self.db["analyses"]
        return None
    
    def create_indexes(self) -> None:
        """Create indexes for better query performance"""
        if not self.is_connected() or self.db is None:
            return
        
        try:
            # Check if collections exist
            existing_collections = self.db.list_collection_names()
            
            # Users collection
            if "users" not in existing_collections:
                self.db.create_collection("users")
                print("✅ Created 'users' collection")
            
            users = self.get_users_collection()
            if users is not None:
                users.create_index("username", unique=True)
                users.create_index("email", unique=True)
                print("✅ Created indexes for 'users' collection")
            
            # Sessions collection
            if "sessions" not in existing_collections:
                self.db.create_collection("sessions")
                print("✅ Created 'sessions' collection")
            
            sessions = self.get_sessions_collection()
            if sessions is not None:
                sessions.create_index("token", unique=True)
                sessions.create_index("user_id")
                sessions.create_index("expires_at")
                print("✅ Created indexes for 'sessions' collection")
            
            # Analyses collection
            if "analyses" not in existing_collections:
                self.db.create_collection("analyses")
                print("✅ Created 'analyses' collection")
            
            analyses = self.get_analyses_collection()
            if analyses is not None:
                analyses.create_index("user_id")
                analyses.create_index("analysis_date")
                print("✅ Created indexes for 'analyses' collection")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not create indexes: {e}")
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256"""
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return MongoDB.hash_password(password) == password_hash
    
    @staticmethod
    def generate_token() -> str:
        """Generate a secure session token"""
        import secrets
        return secrets.token_urlsafe(32)
    
    # User Management Functions
    def create_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """Create a new user in MongoDB"""
        users = self.get_users_collection()
        if users is None:
            return {'success': False, 'message': 'Database not connected'}
        
        try:
            # Check if user exists
            existing = users.find_one({"$or": [{"username": username}, {"email": email}]})
            if existing:
                return {'success': False, 'message': 'Username or email already exists'}
            
            password_hash = self.hash_password(password)
            
            user_data = {
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "created_at": datetime.now(),
                "last_login": None
            }
            
            result = users.insert_one(user_data)
            return {
                'success': True,
                'user_id': str(result.inserted_id),
                'message': 'User created successfully'
            }
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Find user by username"""
        users = self.get_users_collection()
        if users is None:
            return None
        
        try:
            user = users.find_one({"username": username})
            if user:
                user['_id'] = str(user['_id'])
                return dict(user)
            return None
        except Exception:
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Find user by ID"""
        users = self.get_users_collection()
        if users is None:
            return None
        
        try:
            user = users.find_one({"_id": ObjectId(user_id)})
            if user:
                user['_id'] = str(user['_id'])
                return dict(user)
            return None
        except Exception:
            return None
    
    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user"""
        user = self.get_user_by_username(username)
        
        if not user:
            return {'success': False, 'message': 'User not found'}
        
        if self.verify_password(password, user['password_hash']):
            # Update last login
            users = self.get_users_collection()
            if users is not None:
                users.update_one(
                    {"_id": ObjectId(user['_id'])},
                    {"$set": {"last_login": datetime.now()}}
                )
            
            return {
                'success': True,
                'user': {
                    'id': user['_id'],
                    'username': user['username'],
                    'email': user['email']
                }
            }
        
        return {'success': False, 'message': 'Invalid password'}
    
    def update_user(self, user_id: str, email: Optional[str] = None, new_password: Optional[str] = None) -> Dict[str, Any]:
        """Update user information"""
        users = self.get_users_collection()
        if users is None:
            return {'success': False, 'message': 'Database not connected'}
        
        try:
            update_data = {}
            if email:
                update_data["email"] = email
            if new_password:
                update_data["password_hash"] = self.hash_password(new_password)
            
            if not update_data:
                return {'success': False, 'message': 'No updates provided'}
            
            result = users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return {'success': True, 'message': 'User updated'}
            return {'success': False, 'message': 'No changes made'}
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    # Session Management
    def create_session(self, user_id: str, days_valid: int = 30) -> Dict[str, Any]:
        """Create a new session for remember me"""
        sessions = self.get_sessions_collection()
        if sessions is None:
            return {'success': False, 'message': 'Database not connected'}
        
        try:
            token = self.generate_token()
            expires_at = datetime.now() + timedelta(days=days_valid)
            
            # Delete old sessions
            sessions.delete_many({"user_id": user_id})
            
            session_data = {
                "user_id": user_id,
                "token": token,
                "expires_at": expires_at,
                "created_at": datetime.now()
            }
            
            sessions.insert_one(session_data)
            return {'success': True, 'token': token}
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def validate_session(self, token: str) -> Dict[str, Any]:
        """Validate session token"""
        sessions = self.get_sessions_collection()
        if sessions is None:
            return {'success': False, 'message': 'Database not connected'}
        
        try:
            session = sessions.find_one({"token": token})
            
            if session and session['expires_at'] > datetime.now():
                user = self.get_user_by_id(session['user_id'])
                if user:
                    return {
                        'success': True,
                        'user_id': session['user_id'],
                        'username': user['username'],
                        'email': user['email']
                    }
            
            # Delete expired session
            if session:
                sessions.delete_one({"token": token})
            
            return {'success': False, 'message': 'Invalid or expired session'}
        except Exception:
            return {'success': False, 'message': 'Session validation failed'}
    
    def delete_session(self, token: str) -> None:
        """Delete a session"""
        sessions = self.get_sessions_collection()
        if sessions is not None:
            try:
                sessions.delete_one({"token": token})
            except Exception:
                pass
    
    # Analysis History
    def save_analysis(self, user_id: str, filename: str, rows_analyzed: int, 
                      detected_metrics: Dict[str, Any], file_data: Optional[bytes] = None) -> Dict[str, Any]:
        """Save analysis to history"""
        analyses = self.get_analyses_collection()
        if analyses is None:
            return {'success': False, 'message': 'Database not connected'}
        
        try:
            analysis_data = {
                "user_id": user_id,
                "filename": filename,
                "analysis_date": datetime.now(),
                "rows_analyzed": rows_analyzed,
                "detected_metrics": detected_metrics,
            }
            
            if file_data:
                analysis_data["file_data"] = file_data
            
            result = analyses.insert_one(analysis_data)
            return {
                'success': True,
                'analysis_id': str(result.inserted_id)
            }
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def get_user_analyses(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all analyses for a user"""
        analyses = self.get_analyses_collection()
        if analyses is None:
            return []
        
        try:
            cursor = analyses.find(
                {"user_id": user_id}
            ).sort("analysis_date", -1).limit(limit)
            
            results = []
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                if 'analysis_date' in doc and doc['analysis_date']:
                    doc['analysis_date'] = doc['analysis_date'].isoformat()
                results.append(doc)
            
            return results
        except Exception:
            return []
    
    def close(self) -> None:
        """Close MongoDB connection"""
        if self.client:
            self.client.close()

# Create global instance
print("🔄 Initializing MongoDB connection...")
mongo_db = MongoDB()
time.sleep(2)
