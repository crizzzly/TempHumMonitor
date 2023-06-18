#!/usr/bin/env python3.11
import csv
import requests
from datetime import datetime
import sched, time
from pytz import timezone
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

import atexit


COL_HUMIDITY = "mediumblue"
COL_TEMP = "yellow"


TIME_ZONE = 'Europe/Berlin'

SENSOR_IP = "192.168.2.79"
COMMAND = "cmnd/tasmota/status%208"
ENDPOINT = f"http://{SENSOR_IP}/cm?cmnd={COMMAND}"

# update every 60000*5 seconds
INTERVAL = 60000 * 5

values_df =  pd.DataFrame()

with open("data.csv") as file:
    values_df = pd.read_csv(file)
    if "Unnamed: 0" in values_df.columns:
        try:
            values_df.drop(columns=["Unnamed: 0"], inplace=True)
        except KeyError:
            pass
    print(f"read values_df from file. columns: {values_df.columns}\ntypes:{values_df.dtypes}")
    values_df.dt = pd.to_datetime(values_df.dt, yearfirst=True, format="%Y-%m-%d %H:%M")
    # values_df.set_index("dt", inplace=True)


def draw_plot():
    global values_df
    plt.close()
    plt.style.use("dark_background")

    fig, ax = plt.subplots()
    fig.suptitle("Temperature and Humidity")

    # ------ Humidity ----- #

    ax.set_ylim(0, 100)
    ax.tick_params(
        axis="y",
        color=COL_HUMIDITY,
        labelsize="x-small",
    )

    ax.plot(
        values_df.dt,
        values_df.humidity,
        alpha=0.5,
        # align="center",
        color=COL_HUMIDITY,
        # width=50
    )

    # ------ TEMP ----- #
    ax1 = ax.twinx()
    ax1.set_ylim(0, 30)
    ax1.tick_params(
        axis="y",
        color=COL_TEMP,
        labelsize="x-small",
    )

    ax1.plot(
        values_df.dt,
        values_df.temperature,
        color=COL_TEMP,
        linewidth=1,
    )

    ax.grid(True)
    ax.tick_params(
        axis="x",
        which="major",
        labelsize="small",
        # pad=8,
        grid_color="white",
        grid_alpha=0.5,
    )
    ax.tick_params(
        axis="x",
        which="minor",
        labelsize="xx-small",
        # pad=2,
        grid_color="white",
        grid_alpha=0.5,
    )

    ax.grid(visible=True, which='major', axis='x',  color='#DDDDDD', linewidth=0.8)
    ax.grid(visible=True, which='minor', axis='x', color='#DDDDDD', linestyle=':', linewidth=0.8)
    ax.minorticks_on()
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%A'))
    ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=[6, 12, 18]))  # byhour=[6, 12, 18]
    ax.xaxis.set_minor_formatter(mdates.DateFormatter('%H:00'))

    plt.savefig("temp_humidity.png")
    plt.close()



def get_values_http(scheduler=None):
    '''
    requests temperature and humidity from ESP-Webserver and returns it as tuple
    '''
    global values_df

    if scheduler is not None:
        scheduler.enter(60, 1, get_values_http, (scheduler,))
    try:
        res = requests.get(ENDPOINT)
        res.raise_for_status()
    except OSError as e:
        print("Host offline")
    else:
        vals_json = res.json()
        print(vals_json["StatusSNS"]["Time"])
        print(vals_json["StatusSNS"]["AM2301"]["Temperature"])
        print(vals_json["StatusSNS"]["AM2301"]["Humidity"])
        temp = vals_json["StatusSNS"]["AM2301"]["Temperature"]
        hmdt = vals_json["StatusSNS"]["AM2301"]["Humidity"]



        vals = pd.DataFrame({
            "dt": [datetime.now(tz=timezone(TIME_ZONE))],
            "temperature": [temp],
            "humidity": [hmdt],
            })
        # vals.set_index('dt', inplace=True)

        values_df = pd.concat([vals, values_df])
        print(f"concat. columns: {values_df.columns}")

        values_df.sort_values(by=['dt'], axis=0, inplace=True)


        with open("data.csv", "w") as file:
            values_df.to_csv(file)
        print(f"dt: {datetime.now(tz=timezone(TIME_ZONE)).strftime('%Y-%m-%d %H:%M')}\nTemperature: {temp}°\nHumidity: {hmdt}%")

        draw_plot()
        # return float(temp), float(hmdt)

get_values_http()
my_scheduler = sched.scheduler(time.time, time.sleep)
my_scheduler.enter(60, 1, get_values_http, (my_scheduler,))
my_scheduler.run()

    
