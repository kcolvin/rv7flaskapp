# This is a RV-7 data radio simulator.
# It reads a source data file and sends each line via UDP to a computer running the 'receive.py' file.
#
import socket
import time
# Setup UDP destination IP address:
UDP_IP = "44.239.172.205"  # This is the Elastic IP of the IoT Server in the IME AWS acct.
#UDP_IP = "localhost"   # Run this on the local computer
#
#    Setup 'data' port for ems and adahrs lines in the file (port 20003)
DATA_UDP_PORT = 20003
data_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
#
#    Setup 'gps' port for gps lines in the file (port 20004)
GPS_UDP_PORT = 20004
gps_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
#
# This is the send command, use it in the loop below
#sock.sendto(MESSAGE, (UDP_IP, UDP_PORT)) 
#
# To test the function of the receive.py file, 
# open a test data file and send byte arrarys to port
with open('testdata2.txt', 'r') as f:
    # Iterate though the file, line by line, sending each line in a UDP message to the receive.py program
    # There are three types of lines:
      # adahrs lines: begin with a '!1'
      # ems lines: begin with a '!3'
      # gps lines: begin with a '$'
    for line in f:
        # Look for GPS line
        if line[0] == '$':
            print(line)
            # Send GPS lines over port 20004
            gps_sock.sendto(str.encode(line), (UDP_IP, GPS_UDP_PORT)) # Send as a byte array
        else:
            # Otherwise, this is an adahrs or ems line
            print(str.encode(line))
            # Send these lines over port 20003
            data_sock.sendto(str.encode(line), (UDP_IP, DATA_UDP_PORT)) # Send as a byte array instead of string
        time.sleep(.5) # Slow down if you want to see what is happening
        #time.sleep(.0625) # This is real time speed from the radio
f.close() 
