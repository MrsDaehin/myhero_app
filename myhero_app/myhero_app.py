#! /usr/bin/python
'''
    App Service for Simple Superhero Voting Application

    This is the App Service for a basic microservice demo application.
    The application was designed to provide a simple demo for Cisco Mantl
'''

__author__ = 'hapresto'

from flask import Flask, make_response, request, jsonify, Response
import datetime
import urllib
import json
import os, sys
import requests

app = Flask(__name__)

# TODO - Decide if this will be maintaned going forward
@app.route("/hero_list")
def hero_list():
    u = urllib.urlopen(data_server + "/hero_list")
    page = u.read()
    hero_list = json.loads(page)["heros"]

    resp = make_response(jsonify(heros=hero_list))
    return resp

# TODO - Remove GET version once Web Service is Updated
@app.route("/vote/<hero>", methods=["GET", "POST"])
def vote(hero):
    if request.method == "GET":
        u = urllib.urlopen(data_server + "/vote/" + hero)
        page = u.read()
        result = json.loads(page)['result']
        if (result == "1"):
            resp = make_response(jsonify(result="vote accepted"))
        else:
            resp = make_response(jsonify(result="vote rejected"))
        return resp
    if request.method == "POST":
        # Verify that the request is propery authorized
        authz = valid_request_check(request)
        if not authz[0]:
            return authz[1]
        u = data_server + "/vote/" + hero
        data_requests_headers = {"key": data_key}
        page = requests.post(u, headers = data_requests_headers)
        result = page.json()["result"]
        print result
        if (result == "1"):
            msg = {"result":"vote accepted"}
        else:
            msg = {"result":"vote rejected"}
        status = 200
        resp = Response(
            json.dumps(msg, sort_keys=True, indent=4, separators=(',', ': ')),
            content_type='application/json',
            status=status)
        return resp

# TODO - Add Authentication
@app.route("/results")
def results():
    u = urllib.urlopen(data_server + "/results")
    page = u.read()
    tally = json.loads(page)

    resp = make_response(jsonify(tally))
    return resp

@app.route("/options", methods=["GET", "PUT", "POST"])
def options_route():
    '''
    Methods used to view options, add new option, and replace options.
    '''
    # Verify that the request is propery authorized
    authz = valid_request_check(request)
    if not authz[0]:
        return authz[1]

    u = data_server + "/options"
    if request.method == "GET":
        data_requests_headers = {"key": data_key}
        page = requests.get(u, headers=data_requests_headers)
        options = page.json()
        status = 200
    if request.method == "PUT":
        try:
            data = request.get_json(force=True)
            # Verify data is of good format
            # { "option" : "Deadpool" }
            data_requests_headers = {"key": data_key}
            print("New Option: " + data["option"])
            page = requests.put(u,json = data, headers= data_requests_headers)
            options = page.json()
            status = 201
        except KeyError:
            error = {"Error":"API expects dictionary object with single element and key of 'option'"}
            status = 400
            resp = Response(json.dumps(error), content_type='application/json', status = status)
            return resp
    if request.method == "POST":
        try:
            data = request.get_json(force=True)
            # Verify that data is of good format
            # {
            # "options": [
            #     "Spider-Man",
            #     "Captain America",
            #     "Batman",
            #     "Robin",
            #     "Superman",
            #     "Hulk",
            #     "Thor",
            #     "Green Lantern",
            #     "Star Lord",
            #     "Ironman"
            # ]
            # }
            data_requests_headers = {"key": data_key}
            page = requests.post(u, json = data, headers = data_requests_headers)
            options = page.json()
            print("New Options: " + options)
            status = 201
        except KeyError:
            error = {"Error": "API expects dictionary object with single element with key 'option' and value a list of options"}
            status = 400
            resp = Response(json.dumps(error), content_type='application/json', status=status)
            return resp

    resp = Response(
        json.dumps(options, sort_keys=True, indent = 4, separators = (',', ': ')),
        content_type='application/json',
        status=status)
    return resp

@app.route("/options/<option>", methods=["DELETE"])
def option_delete_route(option):
    '''
    Delete an option from the the option_list.
    '''
    # Verify that the request is propery authorized
    authz = valid_request_check(request)
    if not authz[0]:
        return authz[1]

    u = data_server + "/options/" + option
    if request.method == "DELETE":
        print("Delete Option:" + option)
        data_requests_headers = {"key": data_key}
        page = requests.delete(u, headers = data_requests_headers)
        options = page.json()
        status = 202
        resp = Response(
            json.dumps(options, sort_keys=True, indent=4, separators=(',', ': ')),
            content_type='application/json',
            status=status)
        return resp
    else:
        error = {"Error": "Route only acceptes a DELETE method"}
        status = 400
        resp = Response(json.dumps(error), content_type='application/json', status=status)
        return resp

def valid_request_check(request):
    try:
        if request.headers["key"] == app_key:
            return (True, "")
        else:
            error = {"Error": "Invalid Key Provided."}
            print error
            status = 401
            resp = Response(json.dumps(error), content_type='application/json', status=status)
            return (False, resp)
    except KeyError:
        error = {"Error": "Method requires authorization key."}
        print error
        status = 400
        resp = Response(json.dumps(error), content_type='application/json', status=status)
        return (False, resp)


if __name__=='__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser("MyHero Application Service")
    parser.add_argument(
        "-d", "--dataserver", help="Address of data server", required=False
    )
    parser.add_argument(
        "-k", "--datakey", help="Data Server Authentication Key Used in API Calls", required=False
    )
    parser.add_argument(
        "-s", "--appsecret", help="App Server Key Expected in API Calls", required=False
    )

    args = parser.parse_args()

    data_server = args.dataserver
    # print "Arg Data: " + str(data_server)
    if (data_server == None):
        data_server = os.getenv("myhero_data_server")
        # print "Env Data: " + str(data_server)
        if (data_server == None):
            get_data_server = raw_input("What is the data server address? ")
            # print "Input Data: " + str(get_data_server)
            data_server = get_data_server
    print "Data Server: " + data_server
    sys.stderr.write("Data Server: " + data_server + "\n")

    data_key = args.datakey
    # print "Arg Data Key: " + str(data_key)
    if (data_key == None):
        data_key = os.getenv("myhero_data_key")
        # print "Env Data Key: " + str(data_key)
        if (data_key == None):
            get_data_key = raw_input("What is the data server authentication key? ")
            # print "Input Data Key: " + str(get_data_key)
            data_key = get_data_key
    print "Data Server Key: " + data_key
    sys.stderr.write("Data Server Key: " + data_key + "\n")

    app_key = args.appsecret
    # print "Arg App Key: " + str(app_key)
    if (app_key == None):
        app_key = os.getenv("myhero_app_key")
        # print "Env Data Key: " + str(app_key)
        if (app_key == None):
            get_app_key = raw_input("What is the app server authentication key? ")
            # print "Input Data Key: " + str(get_app_key)
            app_key = get_app_key
    print "App Server Key: " + app_key
    sys.stderr.write("App Server Key: " + app_key + "\n")

    app.run(debug=True, host='0.0.0.0', port=int("5000"))

