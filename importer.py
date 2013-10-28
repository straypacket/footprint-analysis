import psycopg2
from tables import *

# PostgreSQL connection
conn = psycopg2.connect("host=127.0.0.1 user=footprint dbname=footprint_tracker_production")
cur = conn.cursor()

#  Open an HDF5 file in "w"rite mode
fp_h5file = openFile("footprint.h5", mode = "w")
# Make the HDF5 structure
fp_group = fp_h5file.createGroup("/", 'footprint', 'Footprint project group')
fp_table = fp_h5file.createTable(fp_group, 'sensors', SensorData, "Wifi sensor data")
# fp_table = fp_h5file.getNode("/footprint/sensors")

# Import data
records = 10
cur.execute("SELECT * FROM archived_wifi_requests ORDER BY client_mac_addr LIMIT %s" % (records))
cur.fetchone()

mac = fp_table.row
for i in xrange(records):
  # mac['client_mac_addr']  = 
  # mac['date'] = 
  # mac['created_at'] = 
  # mac['updated_at'] = 
  # mac['came_at_days_ago'] = 
  # mac['returning_times'] = 
  # mac['minified_data']['time'] = 
  # mac['minified_data']['mac'] = 
  # mac['minified_raw_data']['time'] = 
  # mac['minified_raw_data']['mac'] = 
  # mac['minified_raw_data']['power'] = 
  # Insert a new particle record
  mac.append()
  
# Cleaning up
cur.close()
conn.close()
fp_h5file.close()