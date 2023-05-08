import requests
import datetime

url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
params = {
    "vs_currency": "usd",
    "days": "1"
}
response = requests.get(url, params=params)

# the response contains a dictionary with two lists, one for prices and one for timestamps
json_data = response.json()["prices"]
# timestamps = response.json()["timestamps"]

# print the prices and timestamps
for data in json_data:
    timestamp = data[0] / 1000  # convert milliseconds to seconds
    dt_object = datetime.datetime.fromtimestamp(timestamp)
    formatted_date = dt_object.strftime("%Y-%m-%d %H:%M:%S")
    print(f"Timestamp: {formatted_date}, Price: {data[1]}")
