from tables import *

class SensorData(IsDescription):
  id = Int64Col(pos=0)
  client_mac_addr = StringCol(itemsize=16, pos=1)
  date = Time32Col(pos=2)
  created_at = Time32Col(pos=3)
  updated_at = Time32Col(pos=4)
  came_at_days_ago = Int64Col(pos=5)
  returning_times = Int64Col(pos=6)
  minified_data = StringCol(shape=(2), pos=7)
  minified_data_raw = StringCol(shape=(3), pos=8)
