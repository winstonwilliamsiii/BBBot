# service users
from services.appwrite_client import call_function

def get_user_profile(user_id):
    return call_function("get_user_profile_streamlit", {
        "userId": user_id
    })