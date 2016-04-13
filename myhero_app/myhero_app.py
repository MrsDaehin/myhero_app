#! /usr/bin/python
'''
    App Service for Simple Superhero Voting Application

    This is the App Service for a basic microservice demo application.
    The application was designed to provide a simple demo for Cisco Mantl
'''

__author__ = 'hapresto'

from flask import Flask, make_response, request, jsonify
import datetime
import urllib
import json
import os

app = Flask(__name__)

@app.route("/hero_list")
def hero_list():
    u = urllib.urlopen(data_server + "/hero_list")
    page = u.read()
    hero_list = json.loads(page)["heros"]

    resp = make_response(jsonify(heros=hero_list))
    return resp

@app.route("/vote/<hero>")
def vote(hero):
    u = urllib.urlopen(data_server + "/vote/" + hero)
    page = u.read()
    result = json.loads(page)['result']
    if (result == "1"):
        resp = make_response(jsonify(result="vote accepted"))
    else:
        resp = make_response(jsonify(result="vote rejected"))
    return resp

@app.route("/results")
def results():
    u = urllib.urlopen(data_server + "/results")
    page = u.read()
    tally = json.loads(page)

    resp = make_response(jsonify(tally))
    return resp


if __name__=='__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser("MyHero Application Service")
    parser.add_argument(
        "-d", "--data", help="Address of data server", required=False
    )
    args = parser.parse_args()

    data_server = args.data
    # print "Arg Data: " + str(data_server)
    if (data_server == None):
        data_server = os.getenv("myhero_data_server")
        # print "Env Data: " + str(data_server)
        if (data_server == None):
            get_data_server = raw_input("What is the data server address? ")
            # print "Input Data: " + str(get_data_server)
            data_server = get_data_server

    print "Data Server: " + data_server

    app.run(debug=True, host='0.0.0.0', port=int("5000"))

