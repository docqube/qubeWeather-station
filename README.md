# qubeWeather station client

## Requirements

- [Python Requests](http://docs.python-requests.org/en/master/)
- [Adafruit BMP085](https://github.com/adafruit/Adafruit_Python_BMP)
- [Adafruit DHT](https://github.com/adafruit/Adafruit_Python_DHT)
- [Python SI1145](https://github.com/THP-JOE/Python_SI1145)

## Installation

Clone this repository to `/opt/qubeweather-station` and install all python dependencies. Please follow the instructions from the library creators.

Copy the `qubeweather_station.service` to `/etc/systemd/system` and run `systemctl daemon-reload`. Now you can start (`systemctl start qubeweather_station`) and enable (`systemctl enable qubeweather_station`) the new service.
