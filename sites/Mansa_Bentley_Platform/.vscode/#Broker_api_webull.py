from webull_python_sdk_core import WebullClient
# Initialize the client with your credentials
client = WebullClient(app_key='your_app_key', app_secret='your_app_secret')
# Authenticate and fetch account details
account_info = client.get_account_info()
print("Account Balance:", account_info['balance'])
print("Positions:", account_info['positions'])