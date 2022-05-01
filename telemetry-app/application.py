from flask import Flask, Response, render_template, request, stream_with_context
import boto3
import logging
import time
import json
from datetime import datetime
from typing import Iterator
import sys
import random

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.static_folder = 'static'

# Config dynamodb
#session = boto3.Session(profile_name='kcolvin-ime')
session = boto3.Session()
db_resource = session.resource('dynamodb', region_name='us-west-2')
table = db_resource.Table('telemetry')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chart')
def chart():
    return render_template('chart.html')

@app.route("/chart-data")
def chart_data() -> Response:
    response = Response(stream_with_context(getChartData()), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response    

# Get data for Strip Charts
def getChartData() -> Iterator[str]:
    """
    Generates random value between 0 and 100
    :return: String containing current timestamp (YYYY-mm-dd HH:MM:SS) and randomly generated data.
    """
    if request.headers.getlist("X-Forwarded-For"):
        client_ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        client_ip = request.remote_addr or ""

    try:
        logger.info("Client %s connected", client_ip)
        while True:
            db_data = table.scan()['Items'][0]
            #print('db_data:',db_data,'\n')
            json_data = json.dumps(
                {
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    #"value": random.random() * 100,
                    "ias": db_data['ias'],
                    "pitch": db_data['pitch']
                }
            )
            yield f"data:{json_data}\n\n"
            time.sleep(1)
    except GeneratorExit:
        logger.info("Client %s disconnected", client_ip)

@app.route("/get-data")
def get_data():
    def generate_data():
        while True:
            db_data = table.scan()['Items'][0]
            #print('db_data:',db_data,'\n')
            json_data = json.dumps(
                {
                #'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'ts' : db_data['ts'],
                'palt' : db_data['palt'],
                'ias' : db_data['ias'],
                'lon' : db_data['lon'],
                'lat' : db_data['lat'],
                'vs' : db_data['vs'],
                'mh' : db_data['mh'],
                'pitch' : db_data['pitch'],
                'roll' : db_data['roll'],
                'baro' : db_data['baro']})
            #print('json_data:',json_data,'\n')
            yield f"data:{json_data}\n\n"
            time.sleep(.25) # .5 delay is a little slow, but OK.
    
    response = Response(stream_with_context(generate_data()), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response

