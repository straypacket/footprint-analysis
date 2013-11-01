###
# Run this last, if you need to export results
###
import psycopg2, psycopg2.extras
import json
from tables import *

# Enable PostgreSQL's hstore support
psycopg2.extras.register_hstore()
 
# PostgreSQL connection
conn = psycopg2.connect("host=127.0.0.1 user=footprint dbname=footprint_tracker_production")
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

# Create table
cur.execute("CREATE TABLE IF NOT EXISTS footprint_stats (day integer, mac_address varchar(18), avg_daily_power integer, avg_visit_duration integer, nreqs integer, nvisits integer, total_minutes integer, timeslots hstore);")
 
# Export data
for day_key in days.keys():
	for mac_key in days[day_key].keys():
	  cur.execute("INSERT INTO footprint_stats (day, mac_address, avg_daily_power, avg_visit_duration, nreqs, nvisits, total_minutes, timeslots) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
	  	 (days[day_key][mac_key]['day'],
	  	 days[day_key][mac_key]['mac_address'],
	  	 days[day_key][mac_key]['avg_daily_power'],
	  	 days[day_key][mac_key]['avg_visit_duration'],
	  	 days[day_key][mac_key]['nreqs'],
	  	 days[day_key][mac_key]['nvisits'],
	  	 days[day_key][mac_key]['total_minutes'],
	  	 days[day_key][mac_key]['timeslots']))
