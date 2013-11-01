###
# Run this last, if you need to export results
###
import psycopg2, psycopg2.extras

# PostgreSQL connection
conn = psycopg2.connect("host=127.0.0.1 user=footprint dbname=footprint_tracker_production")
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

# Enable PostgreSQL's hstore support
#psycopg2.extras.register_hstore(cur)

# Create table
cur.execute("CREATE TABLE IF NOT EXISTS footprint_stats (day integer, mac_address varchar(18), timeslot_timings integer, avg_daily_power integer, avg_visit_duration integer, nreqs integer, nvisits integer, total_minutes integer, timeslots hstore);")

# Export data
timeslot_timings = 0
for day_key in days.keys():
  for mac_key in days[day_key].keys():
    if timeslot_timings == 0:
      ts_keys = days[day_key][mac_key]['timeslots'].keys()
      ts_keys.sort()
      timeslot_timings = int(ts_keys[1].replace('h',''))-int(ts_keys[0].replace('h',''))
    
    cur.execute("INSERT INTO footprint_stats (day, mac_address, timeslot_timings, avg_daily_power, avg_visit_duration, nreqs, nvisits, total_minutes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
      (int(day_key), mac_key, timeslot_timings,
      days[day_key][mac_key]['avg_daily_power'],
      days[day_key][mac_key]['avg_visit_duration'],
      days[day_key][mac_key]['nreqs'],
      days[day_key][mac_key]['nvisits'],
      days[day_key][mac_key]['total_minutes']))#,
      #days[day_key][mac_key]['timeslots'].values()))

cur.close()
conn.close()