import psycopg2
import json
from tables import *

# PostgreSQL connection
conn = psycopg2.connect("host=127.0.0.1 user=footprint dbname=footprint_tracker_production")
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

#  Open an HDF5 file in "w"rite mode
fp_h5file = openFile("footprint.h5", mode = "w")
# Make the HDF5 structure
fp_group = fp_h5file.createGroup("/", 'footprint', 'Footprint project group')
fp_table = fp_h5file.createTable(fp_group, 'sensors', SensorData, "Wifi sensor data")
# If exists, read with:
# fp_table = fp_h5file.getNode("/footprint/sensors")

# Import data
records = 10
cur.execute("SELECT * FROM archived_wifi_requests ORDER BY client_mac_addr LIMIT %s" % (records))
#mac = cur.fetchone()

# For each MAC address
for m in cur:

  # Retrieve JSONs
  mac_minified_data = json.loads("{%s}" % m['minified_data'].replace("=>",":"))
  mac_minified_raw_data = json.loads("{%s}" % m['minified_raw_data'].replace("=>",":"))
  
  # Just making sure nothing's odd here
  if len(mac_minified_raw_data) != len(mac_minified_data):
    raise Exception("Unballanced PG result!")
  
  # For each request
  for r in mac_minified_raw_data.keys():

    # Rescue nested JSONs
    mac_minified_raw_data[r] = json.loads(mac_minified_raw_data[r])
    
    # For nested JSON each key
    for k in mac_minified_raw_data[r].keys():
      mac = fp_table.row

      mac['client_mac_addr'] = m['client_mac_addr']
      mac['date'] = m['date']
      mac['created_at'] = m['created_at']
      mac['updated_at'] = m['updated_at']
      mac['came_at_days_ago'] = m['came_at_days_ago']
      mac['returning_times'] = m['returning_times']
      mac['minified_data']['time'] = mac_minified_raw_data[r][k]['minified_data']['time']
      mac['minified_data']['mac'] = mac_minified_raw_data[r][k]['minified_data']['mac']
      mac['minified_raw_data']['time'] = mac_minified_raw_data[r][k]['minified_raw_data']['time']
      mac['minified_raw_data']['mac'] = mac_minified_raw_data[r][k]['minified_raw_data']['mac']
      mac['minified_raw_data']['power'] = mac_minified_raw_data[r][k]['minified_raw_data']['power']

      # Insert a new particle record
      mac.append()
  
# Create indexes
fp_table.cols.client_mac_addr.createIndex()
fp_table.cols.date.createIndex()

# Cleaning up
cur.close()
conn.close()
fp_h5file.close()