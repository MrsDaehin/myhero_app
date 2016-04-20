# MyHero App Service

This is the App Service for a basic microservice demo application.
This provides a logic layer for a voting system where users can vote for their favorite movie superhero.

Details on deploying the entire demo to a Mantl cluster can be found at
* MyHero Demo - [hpreston/myhero_demo](https://github.com/hpreston/myhero_demo)

The application was designed to provide a simple demo for Cisco Mantl.  It is written as a simple Python Flask application and deployed as a docker container.

Other services are:
* Data - [hpreston/myhero_data](https://github.com/hpreston/myhero_data)
* App - [hpreston/myhero_app](https://github.com/hpreston/myhero_app)
* Web - [hpreston/myhero_web](https://github.com/hpreston/myhero_web)

The docker containers are available at
* Data - [hpreston/myhero_data](https://hub.docker.com/r/hpreston/myhero_data)
* App - [hpreston/myhero_app](https://hub.docker.com/r/hpreston/myhero_app)
* Web - [hpreston/myhero_web](https://hub.docker.com/r/hpreston/myhero_web)

## Basic Application Details

Required

* flask
* ArgumentParser
* requests

# Environment Installation

    pip install -r requirements.txt

# Basic Usage

In order to run, the service needs 3 pieces of information to be provided:
1. Data Server Address
2. Data Server Authentication Key to Use
3. Application Server Authentication Key to Require

These details can be provided in one of three ways.
1. As a command line argument
    - `python myhero_app/myhero_app.py --dataserver "http://myhero-data.server.com" --datakey "DATA AUTH KEY" --appsecret "APP AUTH KEY" `
2. As environment variables
    - `export myhero_data_server="http://myhero-data.server.com"`
    - `export myhero_data_key="DATA AUTH KEY"`
    - `export myhero_app_key="APP AUTH KEY"`
    - `python myhero_app/myhero_app.py`
3. As raw input when the application is run
    - `python myhero_app/myhero_app.py`
    - `What is the data server address? http://myhero-data.server.com`
    - `Data Server Key: DATA AUTH KEY`
    - `App Server Key: APP AUTH KEY`

A command line argument overrides an environment variable, and raw input is only used if neither of the other two options provide needed details.

# Accessing

Initial and Basic APIs.
These are v1 APIs that require no authentication and will eventually be removed
* Basic List of Hero Choices
  * `curl http://localhost:5000/hero_list`
* Current results calculations
  * `curl http://localhost:5000/results`
* Place a vote for an option
  * `curl http://localhost:5000/vote/<HERO>`

New v2 APIs
These newer APIs require authentication as well as support more features
* Get the current list of options for voting
  * `curl -X GET -H "key: APP AUTH KEY" http://localhost:5000/options`
* Add a new option to the list
  * `curl -X PUT -H "key: APP AUTH KEY" http://localhost:5000/options -d '{"option":"Deadpool"}'`
* Replace the entire options list
  * `curl-X POST -H "key: APP AUTH KEY" http://localhost:5000/options -d @sample_post.json`
  * Data should be of same format as a GET request
* Delete a single option from the list
  * `curl -X DELETE -H "key: APP AUTH KEY" http://localhost:5000/options/Deadpool`
* Place a Vote for an option
  * `curl -X POST -H "key: APP AUTH KEY" http://localhost:5000/vote/Deadpool`
* Get current results
  * `curl -X GET -H "key: APP AUTH KEY" http://localhost:5000/results`

# Local Development with Vagrant

I've included the configuration files needed to do local development with Vagrant in the repo.  Vagrant will still use Docker for local development and is configured to spin up a CentOS7 host VM for running the container.

To start local development run:
1.  `vagrant up`
    - You may need to run this twice.  The first time to start the docker host, and the second to start the container.
2.  Now you can interact with the API or interface at localhost:15001 (configured in Vagrantfile and Vagrantfile.host)
    - example:  from your local machine `curl -H "key: DevApp" http://localhost:15001/options`
    - Environment Variables are configured in Vagrantfile for development

Each of the services in the application (i.e. myhero_web, myhero_app, and myhero_data) include Vagrant support to allow working locally on all three simultaneously.
