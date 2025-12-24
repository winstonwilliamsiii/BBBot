import requests
# Define the API endpoint and parameters
api_url = "https://api.example.com/wsj/news"
params = {
   "category": "latest",
   "apiKey": "your_api_key"
}
# Make the API request
response = requests.get(api_url, params=params)
# Check if the request was successful
if response.status_code == 200:
   # Parse the JSON response
   data = response.json()
   # Print the latest news articles
   for article in data["articles"]:
       print(f"Title: {article['title']}")
       print(f"Description: {article['description']}")
       print(f"URL: {article['url']}\n")
else:
   print(f"Failed to retrieve data: {response.status_code}")