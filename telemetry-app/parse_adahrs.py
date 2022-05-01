# Parse ADAHRS_raw string into a formatted string
# Start with ADAHRS string:
# !1121003810-041-01031351256+01777-002-01+0803+021+151298264+021852142184
# Results in 17 parameters:
# adahrs = [timestamp, pitch, roll, ....., wind_dir,wind_spd]
# May need to refer to Formatted String Literals:
# https://docs.python.org/3/whatsnew/3.6.html#whatsnew36-pep498
# Need to add the date (yyyymmdd) in front of the Dynon timestamp
import datetime 
import json
import boto3

# Define function to parse ADAHRS_raw string and return a list of select values
def parse_adahrs(adahrs_raw):
    now = datetime.datetime.utcnow()
    date = str(now.year)+ str('{:02d}'.format(now.month))+str('{:02d}'.format(now.day))
    ts = date+adahrs_raw[3:11] # 16 chars long: YYYYMMDDHHMMSSFF, leave as string 
    pitch = adahrs_raw[11:14]+'.'+adahrs_raw[14:15] # float, pitch, degrees from level flight
    if 'X' in pitch:
        pitch = 'NULL'
    roll = adahrs_raw[15:19]+'.'+adahrs_raw[19:20] # float, roll left(-) or rt(+) from level
    if 'X' in roll:
        roll = 'NULL'
    mh = adahrs_raw[20:23] # smallint, magnetic heading in degrees
    if 'X' in mh:
        mh = 'NULL'
    ias = adahrs_raw[23:26]+'.'+adahrs_raw[26:27] # float, indicated airspeed in knots
    if 'X' in ias:
        ias = 'NULL'
    palt = adahrs_raw[27:33] #small int, pressure altitute in feet
    if 'X' in palt:
        palt = 'NULL'
    t_rate = adahrs_raw[33:36]+'.'+adahrs_raw[36:37] #float, turn rate, degs/sec
    if 'X' in t_rate:
        t_rate = 'NULL'
    l_accel = adahrs_raw[37:39]+'.'+adahrs_raw[39:40] #float, lateral acell, Gs
    if 'X' in l_accel:
        l_accel = 'NULL'
    v_accel = adahrs_raw[40:42]+'.'+adahrs_raw[42:43] #float, vert acell, Gs
    if 'X' in v_accel:
        v_accel = 'NULL'
    aoa = adahrs_raw[43:45] #int, aoa, % of critical aoa
    if 'X' in aoa:
        aoa = 'NULL'
    vs = adahrs_raw[45:49]+'0' #int, vert speed, ft/min
    if 'X' in vs:
        vs = 'NULL'
    oat = adahrs_raw[49:52] #int, OAT, degrees C
    if 'X' in oat:
        oat = 'NULL'
    tas = adahrs_raw[52:55]+'.'+adahrs_raw[55:56] #float, tas, knots
    if 'X' in tas:
        tas = 'NULL'
    # This is not right.
    #baro = adahrs_raw[56:57]+'.'+adahrs_raw[57:59] #float, barometric pressure, inHg
    # Get 3 digits
    baro = adahrs_raw[56:59] #float, barometric pressure, inHg
    if 'X' in baro:
        baro = 'NULL'
    if '-' in baro:
        baro = 'NULL'
    else:
        if baro == '.':
            baro = str(0.0)
        baro = str(float(baro)/100 + 27.5) # divide by 100 and add 27.5 from docs.
    dalt = adahrs_raw[59:65] #int, density alititude, ft above MSL
    if 'X' in dalt:
        dalt = 'NULL'
    winddir = adahrs_raw[65:68] #int, wind direction in degrees
    if 'X' in winddir:
        winddir = 'NULL'
    windspd = adahrs_raw[68:70] #int, wind speed in knots
    if 'X' in windspd:
        windspd = 'NULL'
    # should be 17 parameters
    return [ts,pitch,roll,mh,ias,palt,t_rate,l_accel,v_accel,aoa,vs,oat,tas,baro,dalt,winddir,windspd]
