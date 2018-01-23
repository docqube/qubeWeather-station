#!/usr/bin/python
import time
from time import strftime, localtime
from decimal import Decimal
from math import log
import serial
import smbus
import sys
import subprocess
import os
import urllib2
import Adafruit_DHT
from Adafruit_BMP085 import BMP085
import SI1145.SI1145 as SI1145

def convertToList(string):
    fullDataList = string.split(",")
    data = {}
    for x in range(1, len(fullDataList)-1):
        temp = fullDataList[x].split("=")
        data[temp[0]] = temp[1]

    return data

def calculateDewPoint(temperature, humidity):
    l = log(humidity / 100.0)
    m = 17.27 * temperature
    n = 237.3 + temperature
    b = (l + (m / n)) / 17.27
    return ((237.3 * b) / (1.0 - b))

def convertToFahrenheit(temperature):
    return ((temperature * 1.8) + 32)

basedir = os.path.abspath(os.path.dirname(os.path.abspath(__file__))) + "/"
apiscript = basedir + "submit_to_api.py"

# wunderground parameters
wunderground_id = "XXXXXXXXX"
wunderground_token = "<your-wunderground-token>"

# sea level in meters for air pressure calculation
altitude = 0

# Get Data from Wind and Rain
DEVICE = '/dev/ttyACM0'
BAUD = 9600
ser = serial.Serial(DEVICE, BAUD)
time.sleep(5)
ser.readline()
time.sleep(5)

# initialize rain5m for rainrate calculation
rain5m = 0
rainrate = 0

while True:
    # Define some time variables
    hour    = int(strftime("%H", localtime()))
    minutes = int(strftime("%M", localtime()))
    
    # at midnight, reset the Arduino-Data
    if(hour == 0 and minutes <= 5 and minutes >= 0):
        ser.write("@")

    # Send wind/rain-data to database (every 5 mins) and do some calcs
    
    # Collect Arduino-Data via serial interface
    ser.write("!")
    arduino_response = ser.readline()
    # Convert Arduino-Data to Dictionary
    arduino_data = convertToList(arduino_response)
    
    # calculate rainraite (5m to 60m)
    rainrate = (Decimal(arduino_data['dailyrainin']) - rain5m) * 12

    subprocess.call([apiscript, "winddir", str(arduino_data['winddir_avg2m']) ])
    subprocess.call([apiscript, "windspeed", str(arduino_data['windspdmph_avg2m']) ])
    subprocess.call([apiscript, "windgust", str(arduino_data['windgustmph_10m']) ])
    subprocess.call([apiscript, "rainin", str(rainrate) ])
    subprocess.call([apiscript, "dailyrainin", str(arduino_data['dailyrainin']) ])

    # save current rainrate for rainrate calculation
    rain5m = Decimal(arduino_data['dailyrainin'])

    # Get I2C bus
    bus = smbus.SMBus(1)

    # Temperature: DHT22
    humidity_dht22, temperature_dht22 = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 22)
    temperature = float('{0:0.1f}'.format(temperature_dht22))
    subprocess.call([apiscript, "temperature", str(temperature) ])
    
    # Humidity: SI7021
    bus.write_byte(0x40, 0xF5)
    time.sleep(0.1)
    # SI7021 address, 0x40(64)
    # Read data back, 2 bytes, Humidity MSB first
    humidity_raw1 = bus.read_byte(0x40)
    humidity_raw2 = bus.read_byte(0x40)
    # Convert humidity
    humidity = ((humidity_raw1 * 256 + humidity_raw2) * 125 / 65536.0) - 6
    if (humidity > 100):
        humidity = 100
    subprocess.call([apiscript, "humidity", str(humidity) ])

    # Air Pressure: BMP180
    bmp = BMP085(0x77)
    nn_pressure = bmp.readPressure() / 100.0
    # accelerate the pressure-data to 0 over NN
    pressure = nn_pressure / pow(1.0 - altitude/44330.0, 5.255)
    subprocess.call([apiscript, "pressure", str(pressure) ])

    # Lightsensors SI1145
    si1145 = SI1145.SI1145()
    ir = si1145.readIR()
    uvindex = si1145.readUV() / 100.0
    visible = si1145.readVisible()
    subprocess.call([apiscript, "infrared", str(ir) ])
    subprocess.call([apiscript, "uvindex", str(uvindex) ])
    subprocess.call([apiscript, "visible", str(visible) ])

    # Lightlevel BH1750
    bh1750_data = bus.read_i2c_block_data(0x23,0x20) # Device 0x23 + measurement at 1lx resolution
    lightlevel = ((bh1750_data[1] + (256 * bh1750_data[0])) / 1.2)
    subprocess.call([apiscript, "lightlevel", str(lightlevel)])
    
    # Call Wunderground API
    pws_request = "https://rtupdate.wunderground.com/weatherstation/updateweatherstation.php"
    pws_request += "?ID=" + wunderground_id + "&PASSWORD=" + wunderground_token + "&dateutc=now"
    pws_request += "&tempf="
    pws_request += str(convertToFahrenheit(temperature))
    pws_request += "&dewptf="
    pws_request += str(convertToFahrenheit(calculateDewPoint(temperature, humidity)))
    pws_request += "&baromin="
    pws_request += str((pressure * (1 / 33.8638816)))
    pws_request += "&humidity="
    pws_request += str(humidity)
    pws_request += "&visibility="
    pws_request += str(visible)
    pws_request += "&solarradiation="
    pws_request += str(lightlevel)
    pws_request += "&UV="
    pws_request += str(uvindex)
    pws_request += '&winddir='
    pws_request += arduino_data['winddir']
    pws_request += '&windspeedmph='
    pws_request += arduino_data['windspeedmph']
    pws_request += '&windgustmph='
    pws_request += arduino_data['windgustmph_10m']
    pws_request += '&windgustdir='
    pws_request += arduino_data['windgustdir']
    pws_request += '&windspdmph_avg2m='
    pws_request += arduino_data['windspdmph_avg2m']
    pws_request += '&winddir_avg2m='
    pws_request += arduino_data['winddir_avg2m']
    pws_request += '&windgustmph_10m='
    pws_request += arduino_data['windgustmph_10m']
    pws_request += '&windgustdir_10m='
    pws_request += arduino_data['windgustdir_10m']
    pws_request += '&rainin='
    pws_request += str(rainrate)
    pws_request += '&dailyrainin='
    pws_request += arduino_data['dailyrainin']
    pws_request += '&softwaretype=docqube/qubeWeather-station'
    pws_request += '&realtime=1&rtfreq=300'
    
    # Send request to weatherunderground
    try:
        urllib2.urlopen(pws_request)
    except:
        time.sleep(10)

    # timeout for 5 minutes
    time.sleep(300)
