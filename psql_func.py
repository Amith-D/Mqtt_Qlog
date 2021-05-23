# SSH and PSQL Library
from sshtunnel import SSHTunnelForwarder
import psycopg2

# Misc Libraries
import json
from datetime import datetime
import pytz

# Custom Modules
import settings
import math

# Global settings
DEVICE_SETTINGS_TABLE = settings.PSQL_DEVICE_SETTINGS_TABLE
DEVICE_READINGS = settings.DEVICE_READINGS
TIMEZONE = pytz.timezone(settings.TIMEZONE)


def create_dictionary(keys, values):
    """Creates a dictionary of sensor names and its respective sensor values
    {
        '<sensor_key>': <sensor_value>,
        '810nm': '42.52'
    }
    Sensor value in the dictionary will be a string.

    Args:
        keys (list): list of sensor names
        values (list): list of sensor values

    Returns:
        json: dictionary of sensor name and respective sensor values
    """
    return json.dumps({key: value for key, value in zip(keys, values)})


def write_data(warehouse_id, device_id,device_readings):
    """ Writes the data passed to the main table

    Parameters
    ----------
    warehouse_id: str
        Warehouse ID of the device
    device_id: str
        Device ID of the device
    device_readings: list of float values
        List of data collected by the device
    brix: float
        The brix predicted by the model for the current reading
    status: float
        The status of the fruit for the current reading
    """
    print("Psql write")
    print(device_readings)
    # Time related data
    now = datetime.now(tz=TIMEZONE)
    date_stamp = str(now.date())
    time_stamp = str(now.time())

    # Unique Key
    device_info = f"{warehouse_id}/{device_id}/{date_stamp}/{time_stamp}"
    # ID (Primary Key)
    id_pk = read_most_recent_id()[0] + 1
    for reading in range(len(device_readings)):
        if math.isnan(device_readings[reading]):
            device_readings[reading]=0.0
    
    # Device readings
    sensor_dict = create_dictionary(DEVICE_READINGS, device_readings)
    print(device_readings)

    # SQL insert query
    insert_query = """INSERT INTO public."QLog_data"(
                          VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s))"""
    # Data to be inserted
    print(sensor_dict)
    #params = (id_pk, warehouse_id, device_id, sensor_dict, fruit, variety,
    #          batch_number, vendor_code, brix, status, date_stamp, time_stamp, device_info,
    #          device_readings[0],device_readings[1],device_readings[2],device_readings[3],
    #          device_readings[4],device_readings[5],device_readings[6])

    # Data to be inserted
    #default gas1 and gas2 
    g2 = 0
    params = (id_pk,warehouse_id,time_stamp,date_stamp,device_readings[0],device_readings[1],device_readings[2],device_readings[3],device_id,device_readings[4],g2)
    # Executing and commiting
    try:
        conn = psycopg2.connect(database=settings.PSQL_DB_NAME,
                                user=settings.PSQL_USER,
                                password=settings.PSQL_PASSWORD,
                                host=settings.PSQL_HOST,
                                port=settings.PSQL_PORT)

        cur = conn.cursor()
        x  = cur.execute(insert_query, params)
    except Exception as e:
        print("Exception", e)
        conn = psycopg2.connect(database=settings.PSQL_DB_NAME,
                                user=settings.PSQL_USER,
                                password=settings.PSQL_PASSWORD,
                                host=settings.PSQL_HOST,
                                port=settings.PSQL_PORT)
        cur = conn.cursor()
        x  = cur.execute(insert_query, params)
    #print(cur.fetch())
    print("done with write")
    conn.commit()



def get_device_data(warehouse_id: str, device_id: str):
    """ Returns a device's settings

    Parameters
    ----------
    warehouse_id: str
        Warehouse ID of the device
    device_id: str
        Device ID of the device

    Returns
    -------
    The fruit name, fruit variety, batch number and vendor code
    associated with the device
    """

    fetch_query = """SELECT fruit_name AS fruit, variety, white_standard, batch_number, vendor_code, device_type FROM devices D, fruit_varieties V, fruits F, device_types T WHERE D.device_id=%s AND D.FRUIT_VARIETY_ID = V.ID AND V.FRUIT_ID = F.ID AND D.device_type_id = T.id"""
    #print(fetch_query)
    try:
        cur.execute(fetch_query, (device_id,))
    except Exception as e:
        conn = psycopg2.connect(database=settings.PSQL_DB_NAME,
                                user=settings.PSQL_USER,
                                password=settings.PSQL_PASSWORD,
                                host=settings.PSQL_HOST,port=settings.PSQL_PORT)
        cur = conn.cursor()
        cur.execute(fetch_query, (device_id,))
    response = cur.fetchall()
    return response


def read_most_recent_id():
    """
    Returns the most recent ID from the warehouse data table
    """
    query = """SELECT ID FROM public."QLog_data"
                ORDER BY id DESC LIMIT 1;"""

    try:
        cur.execute(query)
        return cur.fetchall()[0]
    except Exception:
        return -1


def read_most_recent_item(warehouse_id, device_id):
    """
    params: warehouse_id, device_id: To uniquely identify the device
    return: Latest status value and device info for specific device
    """
    query = """SELECT status, device_info from warehouse_data WHERE warehouse_id=%s AND device_id=%s
                ORDER BY id DESC limit 1"""

    try:
        cur.execute(query, (warehouse_id, device_id))
        return cur.fetchall()[0]
    except:
        return (-1, -1)


def update_item(status, device_info):
    """
    params: fruit_status: The flipped fruit status to be updated
            device_info: To uniquely identify the device
    return: The updated status
    """
    status = 1 if status == 0 else status

    if device_info != -1:
        query = """UPDATE warehouse_data SET status=%s WHERE device_info=%s"""
        cur.execute(query, (str(status), device_info))
        conn.commit()

    return status


def flip_status(warehouse_id, device_id):
    """
    params: warehouse_id, device_id: To uniquely identify the device
    return: The updated status value
    """

    status, device_info = read_most_recent_item(warehouse_id, device_id)
    status = update_item(status, device_info)
    return status


def get_fruit_variety_list():
    fetch_query = """SELECT fruit_name AS fruit, variety from fruits, fruit_varieties"""
    cur.execute(fetch_query)
    response = cur.fetchall()
    return response


conn = psycopg2.connect(database=settings.PSQL_DB_NAME,
                        user=settings.PSQL_USER,
                        password=settings.PSQL_PASSWORD,
                        host=settings.PSQL_HOST,
                        port=settings.PSQL_PORT)

cur = conn.cursor()

if __name__ == '__main__':

    warehouse_id, device_id = 'BLR_1', 'DEV_1'

    r = get_device_data(warehouse_id, device_id)
    f, v, w, b, vc, t = r[0]

    device_readings = [5733.02, 1181.52, 284.845, 184.935, 229.075, 158.735, 81.2] 
    brix = 120
    status = 1

    write_data(warehouse_id, device_id, device_readings, brix, status, f, v, b, vc)
