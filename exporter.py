###
# Run this last, if you need to export results
###
import psycopg2, psycopg2.extras

# PostgreSQL connection
conn = psycopg2.connect("host=127.0.0.1 user=postgres dbname=footprint_tracker_production")
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

# Enable PostgreSQL's json support
psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)
psycopg2.extras.register_json(conn)

# Create table
cur.execute("CREATE TABLE IF NOT EXISTS footprint_stats (day integer, mac_address varchar(18), avg_daily_power integer, avg_visit_duration integer, nreqs integer, nvisits integer, total_minutes integer, timeslots_visits hstore, timeslots_power hstore, timeslots json);")
conn.commit()

# Export data
for day_key in days.keys():
  for mac_key in days[day_key].keys():
    # Build timeslots_power and timeslots_visits
    ts_visits = {}
    ts_power = {}
    for ts in days[day_key][mac_key]['timeslots']:
      ts_visits[ts] = "%s" % (days[day_key][mac_key]['timeslots'][ts][0])
      ts_power[ts] = "%s" % (days[day_key][mac_key]['timeslots'][ts][1])
      ts_json = [json({'visits': days[day_key][mac_key]['timeslots'][ts][0], 'power': days[day_key][mac_key]['timeslots'][ts][1]})]

    cur.execute("INSERT INTO footprint_stats (day, mac_address, avg_daily_power, avg_visit_duration, nreqs, nvisits, total_minutes, timeslots_visits, timeslots_power) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
      (int(day_key), mac_key,
      days[day_key][mac_key]['avg_daily_power'],
      days[day_key][mac_key]['avg_visit_duration'],
      days[day_key][mac_key]['nreqs'],
      days[day_key][mac_key]['nvisits'],
      days[day_key][mac_key]['total_minutes'],
      ts_visits, ts_power, ts_json))

conn.commit()
cur.close()
conn.close()