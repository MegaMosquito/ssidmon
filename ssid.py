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


# Import the GPIO library so python can work with the GPIO pins
import RPi.GPIO as GPIO


# These values need to be provided from the host
SSID_NAME = os.environ['SSID_NAME']
SSID_FREQ = os.environ['SSID_FREQ']
LOCAL_ROUTER_ADDRESS  = os.environ['LOCAL_ROUTER_ADDRESS']
LOCAL_IP_ADDRESS      = os.environ['LOCAL_IP_ADDRESS']

# External probing target
EXTERNAL_PROBE_TARGET = 'https://www.google.com/'

# Probe timeout
PROBE_TIMEOUT_SEC = 5

# Setup the GPIO's that the RGB LED is attached to
PIN_GREEN_LED = 14
PIN_RED_LED = 15
GPIO.setwarnings(True)
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_GREEN_LED, GPIO.OUT)
GPIO.setup(PIN_RED_LED, GPIO.OUT)
GPIO.output(PIN_GREEN_LED, GPIO.LOW)
GPIO.output(PIN_RED_LED, GPIO.LOW)
SECS_LED = 1


# Setup Flask web server
from flask import Flask
from flask import send_file
FLASK_BIND_ADDRESS = '0.0.0.0'
FLASK_PORT = 6006
webapp = Flask('ssidmon')


# Global for the cached data
SLEEP_BETWEEN_CHECKS_SEC = 5
MAX_CACHE = (24 * 60 * 60 / SLEEP_BETWEEN_CHECKS_SEC)  # Approx one day of samples
cache = deque([])
last_lan = "false"
last_wan = "false"


# Loop forever checking LAN and WAN connectivity
class MonThread(threading.Thread):
  def run(self):
    global cache
    global last_lan
    global last_wan
    # print("\nMonitor thread started!")
    LAN_COMMAND = 'curl -sS ' + LOCAL_ROUTER_ADDRESS + ' 2>/dev/null | wc -l'
    WAN_COMMAND = 'curl -sS ' + EXTERNAL_PROBE_TARGET + ' 2>/dev/null | wc -l'
    while True:
      # print("Checking...")
      # LAN
      yes_no = 'X'
      try:
        yes_no = (subprocess.check_output(LAN_COMMAND, timeout=PROBE_TIMEOUT_SEC, shell=True)).decode('UTF-8').strip()
      except:
        pass
      # print("LAN check = " + yes_no)
      last_lan = "false"
      if (yes_no != "0"):
        last_lan = "true"
      # print(str(last_lan))
      # WAN
      yes_no = 'X'
      try:
        yes_no = (subprocess.check_output(WAN_COMMAND, timeout=PROBE_TIMEOUT_SEC, shell=True)).decode('UTF-8').strip()
      except:
        pass
      # print("WAN check = " + yes_no)
      last_wan = "false"
      if (yes_no != "0"):
        last_wan = "true"
      # print(str(last_wan))
      # Cache
      if (len(cache) > MAX_CACHE):
        trash = cache.popleft()
      utc_secs_since_epoch = int(time.mktime(datetime.utcnow().timetuple()))
      rec = '{"date":' + str(utc_secs_since_epoch) + ',"lan":' + last_lan + ',"wan":' + last_wan + '}'
      cache.append(rec)
      # Turn off both red and green "filaments" in the RGB LED
      GPIO.output(PIN_RED_LED, GPIO.LOW)
      GPIO.output(PIN_GREEN_LED, GPIO.LOW)
      # Wait for 1/10 second before turning one of them back on
      time.sleep(0.1)
      if "true" == last_lan and "true" == last_wan:
        GPIO.output(PIN_GREEN_LED, GPIO.HIGH)
      else:
        GPIO.output(PIN_RED_LED, GPIO.HIGH)
      # print("\nSleeping for " + str(SLEEP_BETWEEN_CHECKS_SEC) + " seconds...\n")
      time.sleep(SLEEP_BETWEEN_CHECKS_SEC)

@webapp.route("/")
def get_page():
  prefix = '{' + \
    '"SSID":"' + SSID_NAME + '",' + \
    '"freq":"' + SSID_FREQ + '",' + \
    '"LAN-target":"' + LOCAL_ROUTER_ADDRESS + '",' + \
    '"WAN-target":"' + EXTERNAL_PROBE_TARGET + '",' + \
    '"results":['
  suffix = ']}'
  rec = prefix
  while (len(cache) > 0):
    rec += cache.popleft()
    if (len(cache) > 0):
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
if __name__ == '__main__':

  mon = MonThread()
  mon.start()
  webapp.run(host=FLASK_BIND_ADDRESS, port=FLASK_PORT)


