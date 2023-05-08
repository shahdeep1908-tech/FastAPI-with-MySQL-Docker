import json
from fastapi.templating import Jinja2Templates
from typing import List

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import requests
from pydantic import BaseModel
import mysql.connector
import datetime

import plotly.graph_objs as go
from plotly.subplots import make_subplots

templates = Jinja2Templates(directory="templates")

app = FastAPI(title="FastAPI Test",
              docs_url="/docs",
              redoc_url="/redoc")


class ResponseMessage(BaseModel):
    message: str


class Lead(BaseModel):
    phone_work: str
    first_name: str
    last_name: str


class FetchedLeads(BaseModel):
    id: int
    phone: str
    first_name: str
    last_name: str


class LeadResponse(ResponseMessage):
    data: List[FetchedLeads]


class Bitcoin(BaseModel):
    timestamp: datetime.datetime
    price: float


class BitcoinResponse(ResponseMessage):
    data: List[Bitcoin]


@app.get('/')
def initialization():
    """
    Initialization Endpoint.
    """
    return "The server is running."


def show_leads():
    cnx = mysql.connector.connect(user='root', password='mysql', host='localhost', database='mydatabase')
    cursor = cnx.cursor()

    show_lead = ("SELECT * FROM leads")
    cursor.execute(show_lead)
    results = cursor.fetchall()  # fetch all rows
    cursor.close()
    cnx.close()
    fetched_leads = []
    for item in results:
        fetched_leads.append(
            FetchedLeads(id=item[0], phone=item[1], first_name=item[2], last_name=item[3]))
    return fetched_leads


def insert_leads_and_price(leads: List):
    # response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
    # data = response.json()
    # price = Price(price=data['bitcoin']['usd'])

    cnx = mysql.connector.connect(user='root', password='mysql', host='localhost', database='mydatabase')
    cursor = cnx.cursor()

    add_lead = ("INSERT INTO leads "
                "(phone_work, first_name, last_name) "
                "VALUES (%s, %s, %s)")
    for lead in leads:
        data_lead = (lead.phone_work, lead.first_name, lead.last_name)
        cursor.execute(add_lead, data_lead)
        cnx.commit()
    cursor.close()
    cnx.close()


def get_leads():
    url = "https://suitecrmdemo.dtbc.eu/service/v4/rest.php"
    module_name = "Leads"
    user_auth = {
        'user_name': 'Demo',
        'password': 'f0258b6685684c113bad94d91b8fa02a',
    }
    name_value_list = {
        'language': 'en_us',
        'notifyonsave': True
    }

    params = {
        "method": "login",
        "input_type": "JSON",
        "response_type": "JSON",
        "rest_data": json.dumps({
            'user_auth': user_auth,
            'application': '',
            'name_value_list': name_value_list
        })
    }

    # make the GET request
    response = requests.post(url, params=params)

    session_id = response.json()["id"]

    # define the request parameters
    leads = []
    max_result = 20
    offset = 0

    while True:
        # define the request parameters
        params = {
            "method": "get_entry_list",
            "input_type": "JSON",
            "response_type": "JSON",
            "rest_data": '{"session":"' + session_id + '","module_name":"' + module_name + '","query":"","order_by":"","offset":"' + str(
                offset) + '","select_fields":["phone_work","first_name","last_name"],"max_results":"' + str(
                max_result) + '"}'
        }

        response = requests.get(url, params=params)

        for lead_data in response.json()['entry_list']:
            lead = Lead(
                phone_work=lead_data['name_value_list']['phone_work']['value'],
                first_name=lead_data['name_value_list']['first_name']['value'],
                last_name=lead_data['name_value_list']['last_name']['value'],
            )
            leads.append(lead)

        # check if all records have been fetched
        if len(response.json()['entry_list']) < max_result:
            break

        # increment the offset for the next request
        offset += max_result
    return leads


@app.get('/collect_leads')
def collect_leads():
    leads = get_leads()
    insert_leads_and_price(leads)
    fetched_leads = show_leads()
    return {'message': f'Successfully collected and inserted {len(leads)} Leads.', 'data': fetched_leads}


@app.get('/bitcoin_price', response_model=BitcoinResponse, response_class=HTMLResponse)
def get_bitcoins(request: Request, days: int, interval: str):
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": interval
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return {"message": "ERROR", "data": []}
    bitcoins = []
    for bitcoin_data in response.json()["prices"]:
        timestamp = bitcoin_data[0] / 1000  # convert milliseconds to seconds
        dt_object = datetime.datetime.fromtimestamp(timestamp)
        formatted_date = dt_object.strftime("%Y-%m-%d %H:%M:%S")

        bitcoin = Bitcoin(
            price=bitcoin_data[1],
            timestamp=formatted_date
        )
        bitcoins.append(bitcoin)
    bitcoins = sorted(bitcoins, key=lambda b: b.timestamp)

    # Create a subplot with 1 row and 1 column
    fig = make_subplots(rows=1, cols=1)

    # Add a scatter plot to the subplot
    fig.add_trace(go.Scatter(x=[bitcoin.timestamp for bitcoin in bitcoins], y=[bitcoin.price for bitcoin in bitcoins],
                             mode='lines+markers', name='Bitcoin Price'))

    # Update the layout of the chart
    fig.update_layout(title='Bitcoin Prices over the Last 7 Days', xaxis_title='Timestamp', yaxis_title='Price (USD)')

    # Render the chart in the HTML template using Jinja2
    chart = fig.to_html(full_html=False)
    return templates.TemplateResponse("index.html", {"request": request, "chart": chart})
    # return templates.TemplateResponse("index.html", {"request": request, "bitcoins": bitcoins})
    # return {'message': 'SUCCESS', 'data': bitcoins}


if __name__ == "__main__":
    uvicorn.run("main:app",
                host="0.0.0.0",
                port=8080,
                log_level="info",
                reload=True)
