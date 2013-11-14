###
# Run this once, between first and second
###
import psycopg2, psycopg2.extras
import json
import calendar, pytz
from tables import *

# PostgreSQL connection
conn = psycopg2.connect("host=127.0.0.1 user=postgres dbname=footprint_tracker_production")
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

#  Open an HDF5 file in "w"rite mode
fp_h5file = openFile("footprint.h5", mode = "a")
# Make the HDF5 structure
#fp_group = fp_h5file.createGroup("/", 'footprint', 'Footprint project group')
#fp_table = fp_h5file.createTable(fp_group, 'sensors', SensorData, "Wifi sensor data")

# Remake the HDF5 structure
fp_table = fp_h5file.getNode('/footprint/sensors')
fp_table.remove()
fp_table = fp_h5file.createTable('/footprint/', 'sensors', SensorData, "Wifi sensor data")

# Import data
#records = 10
#cur.execute("SELECT * FROM archived_wifi_requests ORDER BY client_mac_addr LIMIT %s" % (records))
#mac = cur.fetchone()
cur.execute("SELECT * FROM archived_wifi_requests ORDER BY client_mac_addr")

# For each MAC address
for m in cur:

  # Retrieve JSONs
  mac_minified_data = json.loads("{%s}" % m['minified_data'].replace("=>",":"))
  mac_minified_raw_data = json.loads("{%s}" % m['minified_raw_data'].replace("=>",":"))
  
  # Just making sure nothing's odd here
  if len(mac_minified_raw_data) != len(mac_minified_data):
    raise Exception("Unbalanced PG result!")
  
  # For each request
  for r in mac_minified_raw_data.keys():

    # Rescue nested JSONs
    mac_minified_raw_data[r] = json.loads(mac_minified_raw_data[r])
    
    # For nested JSON each key
    for k in mac_minified_raw_data[r].keys():
      mac = fp_table.row

      mac['client_mac_addr'] = m['client_mac_addr']
      mac['date'] = calendar.timegm(m['date'].timetuple())
      mac['created_at'] = calendar.timegm(m['created_at'].replace(tzinfo=pytz.UTC).timetuple())
      mac['updated_at'] = calendar.timegm(m['updated_at'].replace(tzinfo=pytz.UTC).timetuple())
      mac['came_at_days_ago'] = m['came_at_days_ago']
      mac['returning_times'] = m['returning_times']
      mac['minified_data/time'] = r
      mac['minified_data/mac'] = k
      mac['minified_raw_data/time'] = r
      mac['minified_raw_data/mac'] = k
      mac['minified_raw_data/power'] = mac_minified_raw_data[r][k]

      # Insert a new particle record
      mac.append()
  
# Create indexes
#fp_table.cols.client_mac_addr.createIndex()
#fp_table.cols.date.createIndex()
# Or update indexes
fp_table.cols.client_mac_addr.reIndex()
fp_table.cols.date.reIndex()

# Test
fp_table.nrows

# Cleaning up
fp_table.flush()
cur.close()
conn.close()
fp_h5file.close()