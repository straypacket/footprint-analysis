import psycopg2
from tables import *

# PostgreSQL connection
conn = psycopg2.connect("host=127.0.0.1 user=footprint dbname=footprint_tracker_production")
cur = conn.cursor()

#  Open an HDF5 file in "w"rite mode
h5file = openFile("footprint.h5", mode = "w")
# Make the HDF5 structure
group = h5file.createGroup("/", 'footprint', 'Footprint project group')
table = root.createTable(group, 'sensors', SensorData, "Wifi sensor data")
# table = h5f.getNode("/footprint/sensors")

# Import data
cur.execute("select * from archived_wifi_requests order by client_mac_addr limit 10;")
cur.fetchone()

cur.close()
conn.close()