
# Expose key utilities from frontend_package_initializer
from .frontend_package_initializer import get_version, is_appwrite_connected
try:
	from .frontend_package_initializer import database
except ImportError:
	database = None
