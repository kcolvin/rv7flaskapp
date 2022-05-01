# Parse ADAHRS_raw string into a formatted string
# Start with ADAHRS string:
# !1121003810-041-01031351256+01777-002-01+0803+021+151298264+021852142184
# Results in:
# adahrs = [timestamp, pitch, roll, ....., wind_dir,wind_spd]
# May need to refer to Formatted String Literals:
# https://docs.python.org/3/whatsnew/3.6.html#whatsnew36-pep498
# Need to add the date (yyyymmdd) in front of the Dynon timestamp
import datetime 
import json
import boto3

# Parse EMS_raw string and return a list of select values 
def parse_ems(ems_raw):
    now = datetime.datetime.utcnow()
    date = str(now.year)+ str('{:02d}'.format(now.month))+str('{:02d}'.format(now.day))
    ts = date+ems_raw[3:11] # 16 chars long: YYYYMMDDHHMMSSFF, leave as string 
    oil_p = ems_raw[11:14] # 3 digit oil press (PSI)
    if 'X' in oil_p:
        oil_p = 'NULL'
    oil_t = ems_raw[14:18] # 4 digit oil temp (deg C)
    if 'X' in oil_t:
        oil_t = 'NULL'
    rpm = ems_raw[18:22] # 4 digit rpm (either left or right, they are the same)
    #rpm_r = ems_raw[22:26] #  not used in data, but the same value
    mpress = ems_raw[26:28]+'.'+ems_raw[28:29] # 3 (29.9) digit manifold pressure, inHg 
    return [ts,oil_p,oil_t,rpm,mpress]

# Combine the two lists into an SQL-formatted INSERT INTO Query
def build_query(adahrs_lst,ems_lst,lat,lon,gspd,magvar):
    # build time stamp from the data, : YYYYMMDDHHMMSS.SSSS
    ts_raw = ems_lst[0]
    ts = ts_raw[0:14]+str(float(ts_raw[14:16])/16)[1:]
    # Add paramters to include from ADAHRS
    lat = str(lat)
    lon = str(lon)
    pitch = adahrs_lst[1]
    roll = adahrs_lst[2]
    mh = adahrs_lst[3]
    ias = adahrs_lst[4]
    palt = adahrs_lst[5]
    t_rate = adahrs_lst[6]
    l_accel = adahrs_lst[7]
    v_accel = adahrs_lst[8]
    aoa = adahrs_lst[9]
    vs = adahrs_lst[10]
    oat = adahrs_lst[11]
    tas = adahrs_lst[12]
    baro = adahrs_lst[13]
    dalt = adahrs_lst[14]
    winddir = adahrs_lst[15]
    windspd = adahrs_lst[16]
    # Add parameters from EMS
    oil_p = ems_lst[1]
    oil_t = ems_lst[2]
    rpm = ems_lst[3]
    mpress = ems_lst[4]
    #return f"INSERT INTO airdata (ts,pitch,roll,mh,ias,palt,t_rate,l_accel,v_accel,aoa,vs,oat,tas,baro,dalt,winddir,windspd,oil_p,oil_t,rpm,mpress) VALUES ({ts},{pitch},{roll},{mh},{ias},{palt},{t_rate},{l_accel},{v_accel},{aoa},{vs},{oat},{tas},{baro},{dalt},{winddir},{windspd},{oil_p},{oil_t},{rpm},{mpress});"
    return f"INSERT INTO airdata (ts,lat,lon,pitch,roll,mh,ias,palt,oil_p,oil_t,rpm,mpress) VALUES ({ts},{lat},{lon},{pitch},{roll},{mh},{ias},{palt},{oil_p},{oil_t},{rpm},{mpress});"

# 
# Define function to inject into Kinesis Datastream
def inject_to_stream(kinesis_client, streamName, partitionKey, payload):
    #print(payload)

    return kinesis_client.put_record(
                        StreamName=streamName,
                        Data=json.dumps(payload),
                        PartitionKey=partitionKey)  
#
# Define function to build payload dictionary
def create_payload(adahrs_lst,lat,lon,gspd,magvar):
    # Full parameters needed from RemoteFlight UPDMAPHD
    #METHOD;lat;lon;alt;ias;gspd;vs;pitch;roll;mh;flaps;com1;com1standby;windspeed;winddir;
    keys = ['aircraft','ts','lat','lon','palt','ias','baro','gspd','vs','pitch','roll','mh','flaps','com1','com1standby','windspeed','winddir','magvar','agl']
    #print(keys)
    # The payload is a 'dict' with the keys above and values in the new list
    #values = ['N675CP',str(lat),(str)lon,adahrs_lst[5],str(gspd),adahrs_lst[10],adahrs_lst[1],adahrs_lst[2],adahrs_lst[3],'0','124.0','120.6',adahrs_lst[16],adahrs_lst[15],str(magvar),adahrs_lst[5]]
    values = ['N675CP']             # Aircraft
    values.append(adahrs_lst[0])    # timestamp from Dynon
    values.append(str(lat))         # lat
    values.append(str(lon))         # lon
    values.append(adahrs_lst[5])    # alt
    values.append(adahrs_lst[4])    # ias
    values.append(adahrs_lst[13])   # baro
    values.append(str(gspd))        # gspd
    values.append(adahrs_lst[10])   # vs   
    values.append(adahrs_lst[1])    # pitch
    values.append(adahrs_lst[2])    # roll
    values.append(adahrs_lst[3])    # mag heading
    values.append('0')              # flaps
    values.append('124.0')          # com1
    values.append('120.6')          # com1standby
    values.append(adahrs_lst[16])   # windspeed
    values.append(adahrs_lst[15])   # winddir
    values.append(str(magvar))      # mag var
    values.append(adahrs_lst[5])    # agl
    #print(values)
    # Combine the keys and values into a dict and return
    #d = {keys[i]: values[i] for i in range(len(keys))}
    #print(d)
    return {keys[i]: values[i] for i in range(len(keys))}
