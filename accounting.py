###
# Run this second
###
import time
import itertools
import re
from tables import *
import numpy as np

fp_h5file = openFile("footprint.h5", mode = "r")
fp_table = fp_h5file.getNode('/footprint/sensors')

# Group by days
def day_selector(row):
  #day = time.gmtime(row['date'])
  #return time.strftime("%y-%m-%d",day)
  return row['date']

# Format days
def day_formater(seconds):
  day = time.gmtime(seconds)
  return time.strftime("%y-%m-%d",day)

# Convert time to seconds
def time_to_secs(time_string):
  t_a = time_string.split(':')
  return int(t_a[0])*60*60+int(t_a[1])*60

# Given a time, determine its timeslot
def time_slot_segmented(time_string,hour_segments):
  if hour_segments == 0:
    hour_segments = 1
  t_a = time_string.split(':')

  hour =int(t_a[0])
  minute = (int(t_a[1])/(60/hour_segments))*(60/hour_segments)

  if minute < 10:
    minute = "0%s" % minute

  return "%sh%s" % (hour,minute)

# Create and format segmented timeslots
def build_time_a(slots,hour_segments):
  if hour_segments == 0:
    hour_segments = 1
  time_hash = {}
  for s in xrange(slots):
    for hs in xrange(hour_segments):
      minute = hs*(60/hour_segments)
      if minute < 10:
        minute = "0%s" % minute

      time_hash["%sh%s" % (s,minute)] = [0,0]

  return time_hash

# Natural sort for times inside timeslot
# Used when we need to preserve correct time sequence
def natural_sort(l): 
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(l, key = alphanum_key)

####
# Main structure
# A hash structure with:
#  - first-level keys as date, in integers
#  - second-level keys as mac addresses
#  - third-level are daily stats
#  - fourth-level are timeslot stats
def daily_struct(table):
  days = {}
  nodays = {}
  slot_segments = 4

  # Building structure for unique days
  for d, rows_grouped_by_day in itertools.groupby(table, day_selector):
    if not days.has_key(d): days[d] = {}

  # Accounting data for each day per mac address:
  for dd in days.keys():
    for row in table:
      if row['date'] == dd:
        for register in days[dd],nodays:
          if not register.has_key(row['client_mac_addr']):
            # number of requests, avg daily power, total minutes detected, timeslot:[ number of requests, avg power], number of visits, avg duration of vitits
            register[row['client_mac_addr']] = {
                    'nreqs': 1, 
                    'avg_daily_power': row['minified_raw_data/power'],
                    'total_minutes': 0, 
                    'timeslots': build_time_a(24,slot_segments),
                    'nvisits': 0,
                    'avg_visit_duration': 0}
            register[row['client_mac_addr']]['timeslots'][time_slot_segmented(row['minified_raw_data/time'],slot_segments)][0] += 1
          else:
            register[row['client_mac_addr']]['nreqs'] += 1
            register[row['client_mac_addr']]['avg_daily_power'] += row['minified_raw_data/power']
            register[row['client_mac_addr']]['timeslots'][time_slot_segmented(row['minified_raw_data/time'],slot_segments)][0] += 1
            register[row['client_mac_addr']]['timeslots'][time_slot_segmented(row['minified_raw_data/time'],slot_segments)][1] += row['minified_raw_data/power']           

  # Now compute (per mac per day):
  # - stay time
  # - daily and slot average power
  # - number of visits
  # - avg duration of visits
  for dd in days.keys():
    for m in days[dd].keys():
      days[dd][m]['avg_daily_power'] = days[dd][m]['avg_daily_power']/days[dd][m]['nreqs']
      timer = 0
      visits = 0
      v_counter = 0
      v_buff = []
      prev_buff_count = 0

      # Initialize buffer array
      for i in range(slot_segments):
        v_buff.append(0)

      for ts in natural_sort(days[dd][m]['timeslots'].keys()):
        if prev_buff_count == 0 and v_buff.count(1) != 0:
          visits += 1

        prev_buff_count = v_buff.count(1)

        # Buffer of x timeslots (default: enough slot_segments for one hour)
        # This means that if a mac isn't seen for x timeslots, we'll count the next occurence as a visit
        if days[dd][m]['timeslots'][ts][0] > 0:
          days[dd][m]['timeslots'][ts][1] = days[dd][m]['timeslots'][ts][1]/days[dd][m]['timeslots'][ts][0]
          timer += 60/slot_segments
          v_buff[v_counter%slot_segments] = 1
        else:
          v_buff[v_counter%slot_segments] = 0

        v_counter += 1

      days[dd][m]['nvisits'] += visits
      days[dd][m]['total_minutes'] = timer
      nodays[m]['nvisits'] += visits
      nodays[m]['total_minutes'] += timer
      if timer > 0 and visits > 0:
        days[dd][m]['avg_visit_duration'] = int(timer)/int(visits)
        nodays[m]['avg_visit_duration'] += int(timer)/int(visits)

  return days, nodays

days, nodays = daily_struct(fp_table)
#print "Bench took %s seconds" % (timeit.timeit(stmt="daily_struct(fp_table)", setup="from __main__ import *", number=1))

# Results in days:
# {1380240000.0: {
#   '40:25:C2:BB:47:34': {
#    'avg_daily_power': -82,
#    'avg_visit_duration': 6,
#    'nreqs': 2,
#    'nvisits': 2,
#    'timeslots': {
#     '0h00': [0, 0],
#     '0h06': [0, 0],
#     ...
#     '9h48': [1, -98],
#     '9h54': [0, 0]},
#    'total_minutes': 12}},
#  1380758400.0: {
#   'C0:63:94:77:3E:A5': {
#    'avg_daily_power': -90,
#    'avg_visit_duration': 6,
#    'nreqs': 2,
#    'nvisits': 2,
#    'timeslots': {
#     '0h00': [0, 0],
#     '0h06': [1, -59],
#     ...
#     '9h54': [0, 0]},
#    'total_minutes': 12},
#   'CE:9E:00:07:BF:32': {
#    'avg_daily_power': -68,
#    'avg_visit_duration': 6,
#    'nreqs': 1,
#    'nvisits': 1,
#    'timeslots': {
#     '0h00': [0, 0],
#     ...

# Create dataset
ds_reqs_aux = []
ds_avgp_aux = []
ds_c_aux = []
ds_aux = []
for day_key in days.keys():
  day = int(time.strftime("%d",time.gmtime(day_key)))
  for mac_key in days[day_key].keys():
    ds_reqs_aux.insert(0,[int(days[day_key][mac_key]['nreqs']), day])
    ds_avgp_aux.insert(0,[int(days[day_key][mac_key]['avg_daily_power']/days[day_key][mac_key]['nreqs']), day])
    ds_aux.insert(0, [int(days[day_key][mac_key]['nreqs']), int(days[day_key][mac_key]['avg_daily_power']/days[day_key][mac_key]['nreqs'])])
    if days[day_key][mac_key] > 5:
      ds_c_aux.insert(0,1)
    else:
      ds_c_aux.insert(0,0)
  
ds = np.array(ds_reqs_aux)
ds_a = np.array(ds_aux)
ds_c = np.array(ds_c_aux)
ds_p = np.array(ds_avgp_aux)
#dataset = (ds,ds_p,ds_c)
dataset = (ds,ds_c)
#dataset = (ds_a,ds_c)