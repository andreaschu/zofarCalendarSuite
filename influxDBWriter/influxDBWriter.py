#!/usr/bin/env python3

from influxdb import InfluxDBClient
import uuid
import random
import time
import os

influxdb_host = os.getenv('INFLUXDBHOST')
if influxdb_host is None:
    influxdb_host = 'influxdb'


def writeDataToInflux(# measurement_name: str,
        data_input: list,
        host: str = influxdb_host,
        port: int = 8086,
        database_name: str = 'zofartestsuite'):
    client = InfluxDBClient(host=host, port=port, database=database_name)
    # client.create_database(dbname=database_name)

    # data = [f'{measurement_name},location=bakery,fruit=tangerine,id=b5b24f30-2844-4a68-8906-3149569679da x=0.4463,y=0.9813,z=39i 1644872568591']
    # client_write_start_time = time.perf_counter()
    # client.write_points(tmp_str, database=database_name, time_precision='s', batch_size=1, protocol='line')
    # client.write(data=data)

    # client_write_end_time = time.perf_counter()

    # print("Client Library Write: {time}s".format(time=client_write_end_time - client_write_start_time))


    # client_write_start_time = time.perf_counter()
    client.write_points(data_input, database=database_name, time_precision='ms', protocol='json')

#writeDataToInflux(host='localhost')