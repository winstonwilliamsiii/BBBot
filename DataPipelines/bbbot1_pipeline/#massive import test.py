#massive import test
# Test basic imports
from massive import RESTClient, WebSocketClient
from massive.rest import models

# Verify version (optional)
import massive
print(massive.__version__)  # Should print version number
print("All imports successful!")

    # For pip installations
pip show massive
pip list | grep -E "massive|urllib3|websockets|certifi"

# For Poetry installations
poetry show massive
poetry show --tree  # Shows full dependency tree
