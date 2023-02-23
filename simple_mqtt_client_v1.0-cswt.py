# This is a modified Sequans example and may be copyrighted by Sequans.

import serial
import argparse, os
import time
import sys

#====================================================================================================================
#	Configurable parameters
#====================================================================================================================
uart0_at = "COM44"				# section for AT0 channel configuration
uart0_at_speed = 115200
channel0_at = serial.Serial(uart0_at, uart0_at_speed, timeout=0.5, parity=serial.PARITY_NONE, rtscts=True)  # open serial port

topic = "iot/1070310003/gm02s"
publish_data = '{"msg": "hello from gm02s device"}'

r = '\r'
#====================================================================================================================

parser = argparse.ArgumentParser(description='Script to test MQTT')
parser.add_argument('-s', '--server',
        help='server ip addr or domain name',
        default='192.168.13.1'
        )
parser.add_argument('-p', '--port',
        help='server port',
        default='1883'
        )
parser.add_argument('-e', '--encrypted',
        help='Test mode: none, one-way, two-way',
        default='none',
        )
parser.add_argument('-a', '--caCert',
        help='path to ca certificate',
        default='',
        )
parser.add_argument('-c', '--clientCert',
        help='path to client certificate',
        default='',
        )
parser.add_argument('-k', '--clientKey',
        help='path to client private key',
        default='',
        )

def reading_resp():
	time.sleep(2)
	tmp_line = channel0_at.readlines()
	for line in tmp_line:
		print(line)
	#return tmp_line
	return 

def waiting_response(resp):
	print('Waiting for ' + resp + '...')
	found = 0
	maxtimeout = 20
	for timeout in range(0, maxtimeout):
		tmp_line = channel0_at.readlines()
		for line in tmp_line:
			line = line.decode("utf-8")		# byte array to string
			line = line.replace('\r', '').replace('\n', '')
			print(line+'\n')
			if line == resp:
				print('... found.')
				found = 1
				return True
		time.sleep(1)
	if found == 0:
		print('... not found. Exit.')
		sys.exit()
		
def waiting_response_noexit(resp):
	print('Waiting for ' + resp + '...')
	found = 0
	maxtimeout = 5
	for timeout in range(0, maxtimeout):
		tmp_line = channel0_at.readlines()
		for line in tmp_line:
			line = line.decode("utf-8")		# byte array to string
			line = line.replace('\r', '').replace('\n', '')
			if line == resp:
				print('... found.')
				found = 1
				return True
		time.sleep(1)
	if found == 0:
		print('... not found.')
		#sys.exit()

def get_line_include(word):
	maxtimeout = 20
	for timeout in range(0, maxtimeout):
		tmp_line = channel0_at.readlines()
		for line in tmp_line:
			line = line.decode("utf-8")		# byte array to string
			print(line+r)
			if line.find(word) != -1:
				return line
		time.sleep(1)
	return ''

def checking_at():
	channel0_at.readlines()
	print('Sending AT ')
	channel0_at.write('AT\r'.encode('utf-8'))
	waiting_response('OK')

def set_cert_key(mode, index, path):
	#delete cert/key first
	cmd = 'AT+SQNSNVW="' + mode + '",' + str(index) + ',0' + r
	print('Sending CMD: ' + cmd)
	channel0_at.write(cmd.encode('utf-8'))
	reading_resp()
	#set cert/key
	try:
		file_fd = open(path, 'r')
		file_fd.seek(0, os.SEEK_END)
		size = file_fd.tell()
		file_fd.seek(0)
		buffer = file_fd.read()
		cmd = 'AT+SQNSNVW="' + mode + '",' + str(index) + ',' + str(size) + r
		print('Sending CMD: ' + cmd)
		channel0_at.write(cmd.encode('utf-8'))
		waiting_response('> ')
		buffer = buffer + '\n'
		channel0_at.write(buffer.encode('utf-8'))
		reading_resp()
	finally:
		file_fd.close()

def set_sp(index):
	#for one-way mode, use profile index 1; for two-way mode, use profile index 2
	if index == 1:
		cmd = 'AT+SQNSPCFG=' + str(index) + ',2,"0x3D;0x2F;0x8C",1,0,,,""' + r
	elif index == 2:
		cmd = 'AT+SQNSPCFG=' + str(index) + ',2,"0x3D;0x2F;0x8C",1,0,1,2,""' + r
	print('Sending CMD: ' + cmd)
	channel0_at.write(cmd.encode('utf-8'))
	reading_resp()
        
def test_mqtt(server, port, mode, caCert, clientCert, clientKey):
	print("test_mqtt")
	try:
		time.sleep(.5)
		channel0_at.readlines()
		channel0_at.write(r.encode('utf-8'))
		checking_at()

		# Check the functionality level.  It needs to be 1 but will be 0 after reset.
		cfun_cmd = 'AT+CFUN?\r'
		print('Sending CMD: ' + cfun_cmd)
		channel0_at.write(cfun_cmd.encode('utf-8'))
		cfun = get_line_include('+CFUN:')

		if cfun.strip('\r\n').endswith(' 0'):
			print("Not ready.")
			cfun_cmd = 'AT+CFUN=1\r'
			print('Sending CMD: ' + cfun_cmd)
			channel0_at.write(cfun_cmd.encode('utf-8'))
			cfun = get_line_include('+CFUN: 1')

			if cfun.strip('\r\n').endswith(' 1') or cfun.strip('\r\n').endswith(' 5'):
				print("Module ready: " + cfun + r)
			else:
				# Note: IF the status is 2 we could wait longer for the result.
				print("Module not ready: " + cfun + r)
				sys.exit(1)
		else:
			print("Previously configured.")

		# Do a ping test to confirm that the network is connected.
		ping_cmd = 'AT+PING="www.sequans.com",2\r'
		print('Sending CMD: ' + ping_cmd)
		channel0_at.write(ping_cmd.encode('utf-8'))
		get_line_include('+PING: 2')
		

		if mode == 'one-way':
			set_cert_key("certificate", 0, caCert)
			set_sp(1)
			mqtt_cfg = 'AT+SQNSMQTTCFG=0,"sqn/gm01q",,,1' + r
		elif mode == 'two-way':
			set_cert_key("certificate", 0, caCert)
			set_cert_key("certificate", 1, clientCert)
			set_cert_key("privatekey",  2, clientKey)
			set_sp(2)
			mqtt_cfg = 'AT+SQNSMQTTCFG=0,"sqn/gm01q",,,2' + r
		elif mode == 'none':
			mqtt_cfg = 'AT+SQNSMQTTCFG=0,"sqn/gm01q"' + r
		print('Sending CMD: ' + mqtt_cfg)
		channel0_at.write(mqtt_cfg.encode('utf-8'))
		reading_resp()
		
		mqtt_conn = 'AT+SQNSMQTTCONNECT=0,"' + server + '",' + port + r
		print('Sending CMD: ' + mqtt_conn)
		channel0_at.write(mqtt_conn.encode('utf-8'))
		waiting_response('+SQNSMQTTONCONNECT:0,0')
		
		mqtt_sub = 'AT+SQNSMQTTSUBSCRIBE=0,"' + topic + '",1' + r
		print('Sending CMD: ' + mqtt_sub)
		channel0_at.write(mqtt_sub.encode('utf-8'))
		waiting_response('+SQNSMQTTONSUBSCRIBE:0,"' + topic + '",0')
			
		mqtt_pub = 'AT+SQNSMQTTPUBLISH=0,"' + topic + '",1,' + str(len(publish_data)) + r
		print('Sending CMD: ' + mqtt_pub)
		channel0_at.write(mqtt_pub.encode('utf-8'))
		waiting_response('> ')
		channel0_at.write(publish_data.encode('utf-8'))
		print('data published: ' + publish_data)
		waiting_response('OK')
		time.sleep(1)
		
		mid = -1
		resp = get_line_include('+SQNSMQTTONMESSAGE')
		print('URC: ' + resp)
		if resp != '':
			resp = resp.replace('\r', '').replace('\n', '')
			mid = resp[-1:]
		
		print('receive mid: ' + str(mid))
		if mid == -1:
			mqtt_disconn = 'AT+SQNSMQTTDISCONNECT=0' + r
			print('Sending CMD: ' + mqtt_disconn)
			channel0_at.write(mqtt_disconn.encode('utf-8'))
			return
		
		mqtt_recv = 'AT+SQNSMQTTRCVMESSAGE=0,"' + topic + '",' + str(mid) + r
		print('Sending CMD: ' + mqtt_recv)
		channel0_at.write(mqtt_recv.encode('utf-8'))
		reading_resp()
		
		mqtt_disconn = 'AT+SQNSMQTTDISCONNECT=0' + r
		print('Sending CMD: ' + mqtt_disconn)
		channel0_at.write(mqtt_disconn.encode('utf-8'))
		reading_resp()
		print('Test done!')
	finally:
		print('Exit programm.')
		channel0_at.close()

if __name__ == '__main__':
    args = parser.parse_args()
    #test_mqtt(args.server, args.port, args.encrypted, args.caCert, args.clientCert, args.clientKey)
    
    # Skip command line arguments for debugging in Visual Studio Code.
    test_mqtt('endpoint.iot.us-east-1.amazonaws.com', '8883', 'two-way', '1070310003/AmazonRootCA1.pem', 'things/device-certificate.pem.crt', 'things/device-private.pem.key')	
    
