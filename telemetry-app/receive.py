# Main infinite loop program to receive and ingest UDP messages from data radio.
# The data messages arrive via a UDP message on ports 20003 and 20004
# It receives 3 seprate messages:
# On port 20003, AAHRS and EMS, alternating every .0625 seconds
# On port 20004, GPS every 1 second
# This program records the data in 2 different locations:
#   - Raw data into a local .txt file with a filename built from the datetime stamp when it starts
#   - Updates a single row in an AWS DynamoDB table to be used by the webapp
# 
import socket
import datetime
import time
import boto3
import select
# import my own functions from myFunctions.py
from parse_adahrs import parse_adahrs
from myFunctions import parse_ems, create_payload

# Setup Data UDP socket to listen to port 20003 from anyhost
UDP_PORT = 20003
data_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # UDP
data_sock.bind(('',UDP_PORT))
# Setup GPS UDP socket to listen to port 20004 from anyhost
UDP_PORT = 20004
gps_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # UDP
gps_sock.bind(('',UDP_PORT))

# Create an empty adahrs_lst, will be updated shortly
adahrs_lst = []
# Initialize Global Variables for DynamoDB table
aircraft = 'N675CP'
agl = 0.0
com1 = 124.0
com1standby = 120.6
flaps = 0.0
gspd = 0.0
ias = 0.0
lat = 35.0
lon = -120.0
magvar = 14.4
mh = 290
palt = 220
pitch = -3.6
roll = -4.2
vs = 80
winddir = 270
windspeed = 10

# Initialize file to record raw data
filename = time.strftime("%Y-%m-%d-%H%M%S"+".txt")
#f = open(filename, "x")
f = open('/home/ec2-user/data/'+filename, "x")
#print('Created file:','/home/ec2-user/data/'+filename)
#
# Configure AWS using the right profile
#session = boto3.Session(profile_name='kcolvin-ime')
session = boto3.Session()
# Setup  DynamoDB connection
db_resource = session.resource('dynamodb', region_name='us-west-2')
table = db_resource.Table('telemetry')
# Initialize timekeeper
t1 = datetime.datetime.now()
# For terminal window:
#print('Init complete, listening....')

# infinite loop to process incoming UDP messages
while True:
    # Wait for next Dynon message, then process it
    data, addr = data_sock.recvfrom(1024) # buffer size is 1024 bytes
    msg_raw = bytes.decode(data)
    # Check for valid ADAHRS message ('!1')
    if (msg_raw[1] == '1'):
        # This is ADAHRS data, process it first
        # Write raw data to file
        f.write(msg_raw)
        # Call parse function for ADAHRS to create a list of variables
        adahrs_lst = parse_adahrs(msg_raw)
        # Print to screen
        #print('adahrs:', adahrs_lst)
        #
        # Now get the next msg, should be an EMS msg
        data, addr = data_sock.recvfrom(1024) # buffer size is 1024 bytes
        msg_raw = bytes.decode(data)
        # This is an EMS message, process it next
        # Write raw data to file
        f.write(msg_raw)
        # Call parse fuction for EMS (Will we use this?)
        ems_lst = parse_ems(msg_raw)
        # Print to screen
        #print('ems:',ems_lst)
    # This code quickly checks the GPS socket for data 
    new_gps_data, _, _ = select.select([gps_sock],[],[],.025) #.025 is the timeout (time to wait)
    # If there is data , then process it
    if new_gps_data:
        data = gps_sock.recv(1024)
        gps_raw = bytes.decode(data)
        # write the byte array to the data file
        f.write(gps_raw)
        # Convert the raw data into a list of values
        gps_lst = gps_raw.split(",")
        # This is the NMEA RMC sentence: https://www.trimble.com/OEM_ReceiverHelp/V4.44/en/NMEA-0183messages_RMC.html 
        # Need to reformat NMEA to decimal degrees
        try:
            # Capture error if this doesn't work
            lat = float(gps_lst[3][0:2])+(float(gps_lst[3][2:])/60) # 3514.123093 ddmm.mmmmmm
            lon = -1*(float(gps_lst[5][0:3])+(float(gps_lst[5][3:])/60)) # 12038.044681 dddmm.mmmmmm
            # Truncate to 6 decmial places
            lat = float(f"{lat:.6f}")
            lon = float(f"{lon:.6f}")
            # get other GPS parameters
            gspd = float(gps_lst[7]) # ground track in kts
            #gtrk = float(gps_lst[8]) # ground track in degrees (not needed)
            magvar = float(gps_lst[10]) # magnetic variation in degrees
            # Print GPS data to terminal screen
            #print('GPS lat:',lat,'lon:',lon,'gspd',gspd,'magvar',magvar)        
        except:
            # Just put in default values
            lat = 35.237600 # KSBP lat/lon
            lon = -120.642000
            gspd = 0.0
            magvar = 14.4
    # This code will update the row in the DynamoDB table
    # Build the payload, which is a Python dict
    #
    # Attempt to only update dynamodb every 250 ms
    t2 = datetime.datetime.now()
    delta = t2 - t1
    elapsed_time = delta.total_seconds() * 1000
    if elapsed_time > 250:
        #print('Time since last DynamoDB update:',elapsed_time)        
        try:
            payload = create_payload(adahrs_lst,lat,lon,gspd,magvar)
            #print('baro:',payload['baro'])            
        except:
            print('Did not get valid return from create_payload() function.')
        # Insert into DynamoDB
        try:
            #print('Update dynamodb')
            dynamo_response = table.put_item(Item = payload)
                            #ReturnConsumedCapacity = 'TOTAL')
            t1 = datetime.datetime.now()        
        except:
            print('Something went wrong with DynamoDB')
            #print('DynamoDB Failure: ',dynamo_response)
    

