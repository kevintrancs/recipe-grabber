import json
import requests
import re
import smtplib
from flask import Flask, Response
from bs4 import BeautifulSoup
from flask import json
from flask import request
from flask.logging import default_handler
from flask_cors import CORS


# Some constants used globally
with open('./CONSTANTS.json') as f:
    CONSTANTS = json.load(f)


SERVER = smtplib.SMTP("smtp.gmail.com", 587)
SERVER.starttls()
SERVER.login(CONSTANTS['smtp_email'], CONSTANTS['smtp_pass'])

FOOD_SET = set(line.strip().lower().decode('utf-8')
               for line in open('food.txt'))
app = Flask(__name__)
CORS(app)


@app.route("/api/scrape", methods=['GET'])
def api_scrape():
    """
    Scraping the link/add the custom item, and returns a list of what is entered.
    Parameters
    ----------
    arg1 : String
        Link or single item value

    Returns
    -------
    Response
        Response and data found as a json
    """
    resp = None
    if request.method == 'GET':
        link = request.args.get('url').strip()
        if link is not None and len(link) > 0:
            if "www" in link or "//" in link:
                data = json.dumps(get_recipe(link))
                if data is None:
                    resp = Response(json.dumps(
                        {'error': "Link was broken"}), status=400, mimetype='application/json')
            else:  # Manual item input
                data = json.dumps({'data': str(link).title()})
            resp = Response(data, status=200, mimetype='application/json')
        else:
            resp = Response(json.dumps(
                {'error': "Data sent is empty"}), status=400, mimetype='application/json')
    return resp


@app.route("/api/sendtext", methods=['POST'])
def api_sendtext():
    """
    Sends a text message to your phone
    Parameters
    ----------
    arg1 : String
        phone number
    arg2 : list
        list of items 
    arg3 : String
        carrier value of phone

    Returns
    -------
    Response
        Message sent as a json, or error message
    """
    if request.method == 'POST':
        req_data = request.get_json()
        phone = cleanse_inputs(req_data['phone'])
        items = req_data['items']
        carrier = cleanse_inputs(req_data['carrier'])
        sendable = verify_data(phone, items, carrier)

        if sendable:
            dest = "{}@{}".format(phone, carrier)
            message = "Ingredients: " + ', '.join(items)
            builder = json.dumps(message)
            SERVER.sendmail(CONSTANTS['smtp_email'], dest, message)
            resp = Response(builder, status=200, mimetype='application/json')
        else:
            resp = Response(
                "There was an error in reference to the data being sent.",
                status=400,
                mimetype='application/json')
    return resp


def get_recipe(link):
    """
    Grabs and parses the link found
    Parameters
    ----------
    arg1 : String
        link/url

    Returns
    -------
    Json
        Json with the data with the items parsed out as a list.
    """
    recipe = set()
    html_page = get_html(link)
    if html_page is None:
        return None
    soup = BeautifulSoup(html_page.content, 'html.parser')
    body = soup.find('body')
    li = body.find_all(
        True, {"class": re.compile(r'ingredient', re.IGNORECASE)})

    for i in li:
        value = " ".join(i.getText().strip().split())
        if value not in ['\r', '\n', ' ', '']:
            item = parse_ingredient(value)
            if item is not None:
                recipe.add(item.title())
    return {"data": list(recipe)}


def parse_ingredient(line):
    """ Checks if the item is found in our food set"""
    s = line.lower()
    iterable = re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "", s)
    for i in FOOD_SET:
        if i in iterable:
            return i
    return None


def get_html(link):
    """ Attempts to get html of the page"""
    try:
        page = requests.get(link)
    except Exception:
        print "Failed with trying to find link: {}".format(link)
        return None
    return page


def verify_data(phone, items, carrier):
    """ Verifies if the phone is 11 digits and carrier is there"""
    return True if len(phone) == 11 and len(items) > 0 and carrier is not None else False


def cleanse_inputs(input):
    """ Returns the string without the weird characters and etc. """
    returnable = re.sub(r"[-()\"#/@;:<>{}`+=~|!?,]", "", input)
    return returnable


if __name__ == "__main__":
    # host='0.0.0.0' make public and available
    app.run(host='0.0.0.0')
