#
# Simple SSID Monitor
#
# Written by Glen Darling, November 2019.
#


import json
import os
import subprocess
import threading
import time
from datetime import datetime
from collections import deque


# These values need to be provided from the host
SSID_NAME = os.environ['SSID_NAME']
SSID_FREQ = os.environ['SSID_FREQ']
LOCAL_ROUTER_ADDRESS  = os.environ['LOCAL_ROUTER_ADDRESS']
LOCAL_IP_ADDRESS      = os.environ['LOCAL_IP_ADDRESS']

# External probing target
EXTERNAL_PROBE_TARGET = 'https://www.google.com/'

# Constants
FLASK_BIND_ADDRESS = '0.0.0.0'
FLASK_PORT = 6006


# Global for the cached data
SECS_BETWEEN_SAMPLES = 5
MAX_CACHE = (24 * 60 * 60 / SECS_BETWEEN_SAMPLES)  # Approx one day of samples
lan_cache = deque([])
wan_cache = deque([])


if __name__ == '__main__':

  from flask import Flask
  from flask import send_file
  webapp = Flask('ssidmon')

  # Loop forever checking LAN connectivity
  class LanThread(threading.Thread):
    def run(self):
      global lan_cache
      # print("\nWAN monitor thread started!")
      LAN_COMMAND = 'curl -sS ' + LOCAL_ROUTER_ADDRESS + ' 2>/dev/null | wc -l'
      while True:
        yes_no = str(subprocess.check_output(LAN_COMMAND, shell=True)).strip()
        # print("\n\nWAN check = " + yes_no)
        last_lan = "false"
        if (yes_no != "0"):
          last_lan = "true"
        # print(str(last_lan))
        if (len(lan_cache) > MAX_CACHE):
          trash = lan_cache.popleft()
        utc_secs_since_epoch = int(time.mktime(datetime.utcnow().timetuple()))
        rec = '{"date":' + str(utc_secs_since_epoch) + ',"target":"' + LOCAL_ROUTER_ADDRESS + '","result":' + last_lan + '}'
        lan_cache.append(rec)
        # print("\nSleeping for " + str(SECS_BETWEEN_SAMPLES) + " seconds...\n")
        time.sleep(SECS_BETWEEN_SAMPLES)

  # Loop forever checking WAN connectivity
  class WanThread(threading.Thread):
    def run(self):
      global wan_cache
      # print("\nWAN monitor thread started!")
      WAN_COMMAND = 'curl -sS ' + EXTERNAL_PROBE_TARGET + ' 2>/dev/null | wc -l'
      while True:
        yes_no = str(subprocess.check_output(WAN_COMMAND, shell=True)).strip()
        # print("\n\nWAN check = " + yes_no)
        last_wan = "false"
        if (yes_no != "0"):
          last_wan = "true"
        # print(str(last_wan))
        if (len(wan_cache) > MAX_CACHE):
          trash = wan_cache.popleft()
        utc_secs_since_epoch = int(time.mktime(datetime.utcnow().timetuple()))
        rec = '{"date":' + str(utc_secs_since_epoch) + ',"target":"' + EXTERNAL_PROBE_TARGET + '","result":' + last_wan + '}'
        wan_cache.append(rec)
        # print("\nSleeping for " + str(SECS_BETWEEN_SAMPLES) + " seconds...\n")
        time.sleep(SECS_BETWEEN_SAMPLES)

  @webapp.route("/")
  def get_page():
    prefix = '{"SSID":"' + SSID_NAME + '","freq":"' + SSID_FREQ + '","LAN":['
    infix = '],"WAN":['
    suffix = ']}'
    rec = prefix
    while (len(lan_cache) > 0):
      rec += lan_cache.popleft()
      if (len(lan_cache) > 0):
        rec += ','
    rec += infix
    while (len(wan_cache) > 0):
      rec += wan_cache.popleft()
      if (len(wan_cache) > 0):
        rec += ','
    rec += suffix
    return rec

  # Prevent caching everywhere
  @webapp.after_request
  def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

  # Main program (instantiates and starts polling threads and then web server)
  lanmon = LanThread()
  lanmon.start()
  wanmon = WanThread()
  wanmon.start()
  webapp.run(host=FLASK_BIND_ADDRESS, port=FLASK_PORT)

