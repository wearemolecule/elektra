import json
import os
import flask
from flask import Flask, request, jsonify
from flask.logging import create_logger
from dotenv import load_dotenv, find_dotenv
from werkzeug.exceptions import HTTPException
from elektra import elektra
from pandas import DataFrame as df
import jsonschema
import datetime as dt
import elektra_schema

# flask app configuration
app = Flask(__name__)
log = create_logger(app)
log.setLevel(os.environ.get('LOG_LEVEL', 'DEBUG'))

## get environment variables from the .env file, if one exists
ENV_FILE = find_dotenv()
if ENV_FILE:
  load_dotenv(ENV_FILE)

@app.route('/create', methods=['POST'])
def create_prices():
  # get the request JSON data
  request_data = request.get_json(force=True)

  # verify the required information is in the request
  jsonschema.validate(instance=request_data,schema=elektra_schema.create_prices)

  # get the attributes from the request_data object
  flow_date = dt.datetime.strptime(request_data['flow_date'],'%Y-%m-%d')
  ticker = request_data['ticker']
  node = request_data['node']
  iso = request_data['iso']
  block = request_data['block']
  frequency = request_data['frequency']

  # convert prices into a panda dataframe
  prices = df(request_data['data'])

  # call elektra to get price
  elektra_response = elektra.create_prices(flow_date,ticker,node,iso,block,frequency,prices)
  response = {
    "price": elektra_response
  }
  return jsonify(response), 200

@app.route('/scrub', methods=['POST'])
def scrub_hourly_prices():
  # get the request JSON data
  request_data = request.get_json(force=True)

  # verify the required information is in the request
  jsonschema.validate(instance=request_data,schema=elektra_schema.scrub_prices)

  # get the attributes from the request_data object
  flow_date = dt.datetime.strptime(request_data['flow_date'],'%Y-%m-%d')
  ticker = request_data['ticker']
  node = request_data['node']
  iso = request_data['iso']

  # convert prices into a panda dataframe
  prices = df(request_data['data'])

  # call elektra to get price
  elektra_response = elektra.scrub_hourly_prices(flow_date,ticker,node,iso,prices)
  response = elektra_response.to_json(orient='table', indent=2, index=False)
  return json.loads(response), 200

## Exception Handling ##
@app.errorhandler(HTTPException)
def handle_http_exception(e):
    log.error('HTTP Exception: %s', (e))
    response = {
        'success': False,
        'error': {
            'type': e.name,
            'message': e.description,
        }
    }
    # replace the body with JSON
    return jsonify(response), e.code

@app.errorhandler(jsonschema.exceptions.ValidationError)
def handle_validation_error(error):
    message = str(error)
    log.error(message)
    response = message

    return response, 400

@app.errorhandler(elektra.InsufficientDataError)
def handle_elektra_insufficientdata_error(error):
    message = str(error)
    log.error(message)
    response = {
        'success': False,
        'error': {
            'type': error.__class__.__name__,
            'message': message
        }
    }

    return jsonify(response), 400

@app.errorhandler(elektra.ElektraConfigError)
def handle_elektra_config_error(error):
    message = str(error)
    log.error(message)
    response = {
        'success': False,
        'error': {
            'type': error.__class__.__name__,
            'message': message
        }
    }

    return jsonify(response), 400

@app.errorhandler(elektra.NoRelevantHoursTodayError)
def handle_elektra_relevant_error(error):
    message = str(error)
    log.error(message)
    response = {
        'success': False,
        'error': {
            'type': error.__class__.__name__,
            'message': message
        }
    }

    return jsonify(response), 400

@app.errorhandler(RuntimeError)
def handle_runtime_error(error):
    message = [str(x) for x in error.args]
    log.error(message)
    response = {
        'success': False,
        'error': {
            'type': error.__class__.__name__,
            'message': message
        }
    }

    return jsonify(response), 400

@app.errorhandler(Exception)
def unhandled_exception(error):
    log.error('Unhandled Exception: %s', (error))
    response = {
        'success': False,
        'error': {
            'type': error.__class__.__name__,
            'message': 'An unexpected error has occurred.',
        }
    }

    return jsonify(response), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))