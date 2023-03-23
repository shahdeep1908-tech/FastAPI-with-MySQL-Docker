import json
from decimal import Decimal
from typing import List

import uvicorn
from fastapi import FastAPI
import requests
from pydantic import BaseModel
import mysql.connector

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
    value: float


class LeadResponse(ResponseMessage):
    data: List[FetchedLeads]


class Price(BaseModel):
    price: float


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
            FetchedLeads(id=item[0], phone=item[1], first_name=item[2], last_name=item[3], value=Decimal(item[4])))
    return fetched_leads


def insert_leads_and_price(leads: List):
    response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
    data = response.json()
    price = Price(price=data['bitcoin']['usd'])

    cnx = mysql.connector.connect(user='root', password='mysql', host='localhost', database='mydatabase')
    cursor = cnx.cursor()

    add_lead = ("INSERT INTO leads "
                "(phone_work, first_name, last_name, bitcoin_price) "
                "VALUES (%s, %s, %s, %s)")
    for lead in leads:
        data_lead = (lead.phone_work, lead.first_name, lead.last_name, price.price)
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


if __name__ == "__main__":
    uvicorn.run("main:app",
                host="0.0.0.0",
                port=8080,
                log_level="info",
                reload=True)
