import requests
import json

# Test the detailed HR reports endpoint
try:
    response = requests.get('http://localhost:8002/api/hr-reports/detailed', 
                          params={'period': 'monthly'},
                          headers={'accept': 'application/json'})
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Response Data:")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error Response: {response.text}")
except Exception as e:
    print(f"Request failed with exception: {e}")
