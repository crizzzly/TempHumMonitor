import requests
import pprint

SENSOR_IP = "192.168.2.79"
COMMAND = "cmnd/tasmota/status%208"
ENDPOINT = f"http://{SENSOR_IP}/cm?cmnd={COMMAND}"

res = requests.get(ENDPOINT)
pprint.pprint(res.json())
