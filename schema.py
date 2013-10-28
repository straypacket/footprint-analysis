from tables import *

class minified_raw_data(IsDescription):
    id = Int64Col(pos=0)
    time = StringCol(itemsize=5, pos=1)
    mac = StringCol(itemsize=16, pos=2)
    power = Int32Col(pos=3)
    
class minified_data(IsDescription):
    id = Int64Col(pos=0)
    time = StringCol(itemsize=5, pos=1)
    mac = StringCol(itemsize=16, pos=2)
    
class SensorData(IsDescription):
  id = Int64Col(pos=0)
  client_mac_addr = StringCol(itemsize=16, pos=1)
  date = Time64Col(pos=2)
  created_at = Time32Col(pos=3)
  updated_at = Time32Col(pos=4)
  came_at_days_ago = Int64Col(pos=5)
  returning_times = Int64Col(pos=6)
  minified_data = minified_data
  minified_raw_data = minified_raw_data
  