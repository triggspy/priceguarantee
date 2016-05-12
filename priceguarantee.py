import json
import requests
from re import sub
from decimal import Decimal
import smtplib
from secrets import loginname, loginpw, API_KEY
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def callApi(date):
    """Queries the Google API for all the flights on a specified DATE between LAX & SEA. That data can be searched through to find the price and compare it to our pricePaid."""
    URL = "https://www.googleapis.com/qpxExpress/v1/trips/search?key=" + API_KEY
    HEADERS = {'content-type': 'application/json'}

    searchParam = {
        "request": {
            "passengers": {
                "kind": "qpxexpress#passengerCounts",
                "adultCount": 1,
            },
            "slice": [
                {
                    "kind": "qpxexpress#sliceInput",
                    "origin": "SEA",
                    "destination": "LAX",
                    "date": date,
                    "maxStops": 1,
                    "preferredCabin": "COACH",
                    "permittedCrrier": [
                        "AS"
                    ]
                }
            ],
            "solutions": 500,
        }
    }
    response = requests.post(URL, data=json.dumps(searchParam), headers=HEADERS)
    data = response.json()
    return data

def getFlightInfo():
    '''
    Iterate through the google sheet provided and grab the necessary information to compare against. I.E. Grab flight #s, prices paid and dates flown.

    Sample output from flight_info: ['5/11/2016 16:13:44', '450', '477', '2016-05-12', '2016-05-16', '180.2', 'jordontriggs@gmail.com', 'Los Angeles2']
    '''
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('secret2.json', scope)
    gc = gspread.authorize(credentials)
    spreadsheet = gc.open("Alaska Air Price Guarantee").sheet1
    allTheThings = spreadsheet.get_all_values()
    for flightInfo in allTheThings[1:]:
        firstLeg, secondLeg, dateDepart, dateReturn, pricePaid, email, nickName = flightInfo[1], flightInfo[2], flightInfo[3], flightInfo[4], float(flightInfo[5]), flightInfo[6], flightInfo[7]
        firstLegCurrentPrice = checkPrice(firstLeg, dateDepart)
        secondLegCurrentPrice = checkPrice(secondLeg, dateReturn)
        comparePriceAndIfCheaperSendEmail(firstLegCurrentPrice, secondLegCurrentPrice, pricePaid, nickName)


def checkPrice(leg, date):
    """Check the first leg of the flight and grab the sale total for that flight."""
    data = callApi(date)
    print("The leg is " + leg)
    for trip in data["trips"]["tripOption"]:
        nestedNumber = trip["slice"][0]["segment"][0]["flight"]["number"]
        print("The nested number is " + nestedNumber)
        if leg == nestedNumber:
            LegCurrentPrice = trip["saleTotal"]
            LegCurrentPrice = Decimal(sub(r'[^\d.]', '', LegCurrentPrice))
            print(LegCurrentPrice)
            return LegCurrentPrice
        if leg != nestedNumber:
            print("Flight not found.")

def  comparePriceAndIfCheaperSendEmail(firstLegCurrentPrice, secondLegCurrentPrice, pricePaid, nickName):
    """#compare current price of both legs combined (total price) vs price paid. If the current price is cheaper than the pricePaid send an email advising that the price has dropped."""
    try:
        currentTotalPrice = firstLegCurrentPrice + secondLegCurrentPrice
    except TypeError:
        return    
        if currentTotalPrice < pricePaid:
        smtpObj.sendmail(loginname, "jordontriggs@gmail.com",
                         'Subject: Cheaper Flight!\nThe price of your flight to ' + nickName + ' has gotten cheaper! Login to alaskaair.com to claim your credit!')
        print("Savings!")

if __name__ == "__main__":
    smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
    smtpObj.ehlo()
    smtpObj.starttls()
    smtpObj.login(loginname, loginpw)


    getFlightInfo()
