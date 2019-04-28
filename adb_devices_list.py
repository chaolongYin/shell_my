#!/usr/bin/env python3

import os
import glob
import sys
import socket
import threadpool

#add more device here
#please add all device with port:5555
LAN_IP_PRE = '10.235.'
LAN_PORT = 5555
#TODO: consider cpu core and fd limits
SCAN_THREADPOOL_SIZE = 128 * 4
scan_find_device = False
config_devices = {
        '10.235.68.92:5555':'sdm660_dangzhiyong',
        '10.235.69.178:5555':'qcom710_liyuzhong',
        '10.235.69.73:5555':'car_8665_android32',
        'all':'try connect/disconnect all device'
        }

action = ['connect', 'disconnect']
#remap adb command to adb -P $UID for group user
#detail check /etc/bash.bashrc: alias adb="adb -P `expr $UID \* 10`"
#pytho os.system can not get the alias from /etc/bash.bashrc
adb = ''

def err_print(msg):
    print("ERR: " + msg)
    help()

def check_devices_status(ip_with_port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #TODO: choose a opt time
    s.settimeout(0.5)
    ip = ip_with_port.split(':')[0]
    port = int(ip_with_port.split(':')[1])
    try:
        s.connect((ip, port))
        s.shutdown(2)
        s.close()
        return "available"
    except:
        s.close()
        return "unavailable"
def devices_status_result_f(key):
    print('| %-20s description: %-20s status: %-13s|' %
            (key, config_devices[key], check_devices_status(key)))

def help():
    print("config devices list:")
    #E5 with 32 core
    print("------------------------------------------------------------------------------")
    data = []
    for key in config_devices:
        if key != 'all':
            data.append(key)
    pool = threadpool.ThreadPool(32)
    requests = threadpool.makeRequests(devices_status_result_f, data)
    [pool.putRequest(req) for req in requests]
    pool.wait()
    print("------------------------------------------------------------------------------")

    print("Usage:")
    print("1: connect/disconnect one device:")
    print("adb_devices_list.py ip:port" + " connect/disconnect")
    print("[sdm660] adb_devices_list 10.235.68.92:5555" + " connect")
    print("")
    print("2: connect/disconnect all config devices:")
    print("adb_devices_list.py all connect")
    print("adb_devices_list.py all disconnect")
    print("")
    print("3: scan LAN available devices [only for 5555 port]")
    print("after get scan result, u may need update device to: config_devices")
    print("adb_devices_list.py lan_scan")
    exit()

def lan_scan_result_f(key):
    global scan_find_device
    if 'available' == check_devices_status(key):
        print('| %-20s status: available|' % key)
        scan_find_device = True

def lan_scan():
    data = []
    for a in range(256):
        for b in range(256):
            key = LAN_IP_PRE + str(a) + '.' + str(b) + ':' + str(LAN_PORT)
            data.append(key)
    pool = threadpool.ThreadPool(SCAN_THREADPOOL_SIZE)
    requests = threadpool.makeRequests(lan_scan_result_f, data)
    [pool.putRequest(req) for req in requests]
    pool.wait()
    if not scan_find_device:
        print('ERR: can not find any device!')

def run():
    if len(sys.argv) == 2 and sys.argv[1] == 'lan_scan':
        print('Warning: will scan LAN %d port,may take some time!' % LAN_PORT)
        print('scan with %d threads' % SCAN_THREADPOOL_SIZE)
        print('scan range: %s0.0 - %s255.255, will take about one minute' % (LAN_IP_PRE, LAN_IP_PRE))
        print("Scan result:")
        lan_scan()
        return

    if len(sys.argv) != 3:
        err_print("need two args")
        help()
    
    '''
    if sys.argv[1] not in config_devices.keys():
        err_print("can not find key: " + sys.argv[1])
    '''

    if sys.argv[2] not in action:
        err_print("error args!")

    if sys.argv[1] != 'all':
        status = check_devices_status(sys.argv[1])
        if status == 'unavailable':
            err_print("input device: %s unavailable, please try devices owner: %s" % (sys.argv[1], config_devices[sys.argv[1]]))
        exec_args = '%s %s %s' % (adb, sys.argv[2], sys.argv[1])
        print(exec_args)
        print("command: " + exec_args)
        os.system(exec_args)
        os.system('%s devices' % adb)
    else:
        if sys.argv[2] == 'connect':
            for key in config_devices:
                if key != 'all':
                    exec_args = '%s %s %s' % (adb, sys.argv[2], key)
                    print("command: " + exec_args)
                    os.system(exec_args)
        else:
            #fast disconnect all devices
            exec_args = '%s %s' % (adb, sys.argv[2])
            os.system(exec_args)
        os.system('%s devices' % adb)

if __name__ == '__main__':
    adb = 'adb -P %s' % (os.getuid()*10)
    run()
