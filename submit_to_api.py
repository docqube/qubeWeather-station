#!/usr/bin/python
import sys
import requests

def main():
    argv = sys.argv
    sensor = argv[1]
    value = argv[2]

    server = "https://<qubeWeather-API>/api/data"
    token = "<station-token>"

    headers = {'Authorization': token}
    data = {'sensor': sensor, 'value': value}

    r = requests.put(server, headers=headers, data=data)

if __name__=="__main__":
    main()
