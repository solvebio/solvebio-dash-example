SolveBio + Dash Example App
===========================

This is an example [Dash](https://plot.ly/products/dash/) application that uses the SolveBio API to pull data.

To run it locally, you'll need Python 2.7 or 3.6 installed. You can deploy it to Heroku or to a SolveBio App Server.


## Local Development


### Install Requirements

    pip install -r requirements.txt


**Python 2 Only** If you are using Python 2, install a few additional requirements:

    pip install -r requirements-py2.txt


### Run the App

If you have a SolveBio OAuth2 client ID, set the environment variable:

    export CLIENT_ID=<your client ID>


If you do not have a client ID or would like to test the app with your personal SolveBio API key, set the following environment variable:

    export SOLVEBIO_API_KEY=<your API key>


Run the app in local development mode:

    python index.py


## Deploy the App

### Deploy to SolveBio

If you have access to a SolveBio App Server, contact SolveBio support for instructions.


### Deploy to Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)


If you want to deploy manually with the Heroku CLI, first create a new Heroku app:

    heroku create

    # Set the SECRET_KEY to random characters
    heroku config:set SECRET_KEY=somesecretkey123
    # Set your SolveBio OAuth2 client ID
    heroku config:set CLIENT_ID=<your client id>

    git push heroku master


Tip: generate a secret key using Python:

    import binascii
    import os
    binascii.hexlify(os.urandom(24))

