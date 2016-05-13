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
import json, random
import os, sys, socket, dns.resolver
import requests
import paho.mqtt.publish as publish

app = Flask(__name__)

mqtt_host = ""
mqtt_port = 0
mode = "direct"

# Setup MQTT Topic Info
lhost = socket.gethostname()


# TODO - Decide if this will be maintaned going forward
@app.route("/hero_list")
def hero_list():
    u = urllib.urlopen(data_server + "/hero_list")
    page = u.read()
    hero_list = json.loads(page)["heros"]

    resp = make_response(jsonify(heros=hero_list))
    return resp

@app.route("/vote/<hero>", methods=["POST"])
def vote(hero):
    if request.method == "POST":
        # Verify that the request is propery authorized
        authz = valid_request_check(request)
        if not authz[0]:
            return authz[1]

        # Depending on mode, either send direct to data server or publish
        if mode == "direct":
            # print("Vote direct")
            u = data_server + "/vote/" + hero
            data_requests_headers = {"key": data_key}
            page = requests.post(u, headers = data_requests_headers)
            result = page.json()["result"]
        elif mode == "queue":
            # print("Vote Q")
            # Publish Message
            publish_vote(hero)
            result = "1"
        if (result == "1"):
            msg = {"result":"vote submitted"}
        else:
            msg = {"result":"vote submission failed"}
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
            sys.stderr.write("New Option: " + data["option"] + "\n")
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
            sys.stderr.write("New Options: " + options + "\n")
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
        sys.stderr.write("Delete Option:" + option + "\n")
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
            sys.stderr.write(error + "\n")
            status = 401
            resp = Response(json.dumps(error), content_type='application/json', status=status)
            return (False, resp)
    except KeyError:
        error = {"Error": "Method requires authorization key."}
        sys.stderr.write(error + "\n")
        status = 400
        resp = Response(json.dumps(error), content_type='application/json', status=status)
        return (False, resp)

def publish_vote(vote):
    # Basic Publish to a MQTT Queue
    # print("Publishing vote.")
    t = lhost + "-" + str(random.randint(0,9))
    publish.single("MyHero-Votes/" + t, payload=vote, hostname=mqtt_host, port=mqtt_port, retain=True)
    return ""

# Get SRV Lookup Details for Queueing Server
# The MQTT Server details are expected to be found by processing an SRV Lookup
# The target will be consul for deploments utilizing Mantl.io
# The underlying host running the service must have DNS servers configured to
# Resolve the lookup
def srv_lookup(name):
    resolver = dns.resolver.Resolver()
    results = []
    try:
        for rdata in resolver.query(name, 'SRV'):
            results.append((str(rdata.target), rdata.port))
        # print ("Resolved Service Location as {}".format(results))
    except:
        raise ValueError("Can't find SRV Record")
    return results

# Get IP for Host
def ip_lookup(name):
    resolver = dns.resolver.Resolver()
    results = ""
    try:
        for rdata in resolver.query(name, 'A'):
            results = str(rdata)
        # print ("Resolved Service Location as {}".format(results))
    except:
        raise ValueError("Can't find A Record")
    return results



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
    parser.add_argument(
        "-q", "--mqttserver", help="MQTT Server FQDN for SRV Lookup", required=False
    )
    parser.add_argument(
        "-i", "--mqtthost", help="MQTT Server Host IP Address", required=False
    )
    parser.add_argument(
        "-p", "--mqttport", help="MQTT Server Port", required=False
    )
    parser.add_argument(
        "--mode", help="Voting Processing Mode - direct or queue", required=False
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
    # print "Data Server: " + data_server
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
    # print "Data Server Key: " + data_key
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
    # print "App Server Key: " + app_key
    sys.stderr.write("App Server Key: " + app_key + "\n")

    # The API Service can run in two modes, direct or queue
    # In direct mode votes are sent direct to the data server
    # In queue mode votes are published to an MQTT server
    # Default mode is direct
    mode = args.mode
    if mode == None:
        mode = os.getenv("myhero_app_mode")
        if mode == None: mode = "direct"
    sys.stderr.write("App Server Server Mode is: " + mode + "\n")
    if mode == "queue":
        # To find the MQTT Server, two options are possible
        # In order of priority
        # 1.  Explicitly Set mqtthost and mqttport details from Arguments or Environment Variables
        # 2.  Leveraging DNS to lookup an SRV Record to get HOST IP and PORT information
        # Try #1 Option for Explicitly Set Options
        mqtt_host = args.mqtthost
        mqtt_port = args.mqttport
        if (mqtt_host == None and mqtt_port == None):
            mqtt_host = os.getenv("myhero_mqtt_host")
            mqtt_port = os.getenv("myhero_mqtt_port")
            if (mqtt_host == None and mqtt_port == None):
                # Move onto #2 and Try DNS Lookup
                mqtt_server = args.mqttserver
                if (mqtt_server == None):
                    mqtt_server = os.getenv("myhero_mqtt_server")
                    if (mqtt_server == None):
                        mqtt_server = raw_input("What is the MQTT Server FQDN for an SRV Lookup? ")
                sys.stderr.write("MQTT Server: " + mqtt_server + "\n")
                # Lookup and resolve the IP and Port for the MQTT Server
                try:
                    records = srv_lookup(mqtt_server)
                    if len(records) != 1: raise Exception("More than 1 SRV Record Returned")
                    # To find the HOST IP address need to take the returned hostname from the
                    # SRV check and do an IP lookup on it
                    mqtt_host = str(ip_lookup(records[0][0]))
                    mqtt_port = records[0][1]
                except ValueError:
                    raise ValueError("Message Queue Not Found")
        sys.stderr.write("MQTT Host: %s \nMQTT Port: %s\n" % (mqtt_host, mqtt_port))

    app.run(debug=True, host='0.0.0.0', port=int("5000"))

