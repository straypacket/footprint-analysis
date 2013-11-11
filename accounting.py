###
# Run this second
###

import time
from datetime import datetime
import itertools
import re
from tables import *
import numpy as np
import pylab as pl
from mpl_toolkits.mplot3d import Axes3D

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

def js_day_formater(day_and_time):
  local_epoch = '13-10-04 00:00'
  delta = datetime.strptime(day_and_time,'%y-%m-%d %H:%M')-datetime.strptime(local_epoch,'%y-%m-%d %H:%M')
  return int(delta.total_seconds()/60)

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
# JSON structure for viz
#
# - Method json_times() creates the timeslots
# - Method json_matrix() creates the matrices according to the number of timeslots
# - Method json_points() creates the matrix with the AP locations (knda static for now)
# - Method json_viz bundles it all together, in order to return a compliant JSON
#
def json_times():
  local_epoch = '13-10-04 00:00'
  threshold = 15 #minutes for bucket

  day = time.gmtime(time.time())
  now = time.strftime("%y-%m-%d %H:%M",day)

  delta = datetime.strptime(now,'%y-%m-%d %H:%M')-datetime.strptime(local_epoch,'%y-%m-%d %H:%M')
  minutes_to_now = int(delta.total_seconds()/60)

  print range(0, minutes_to_now, threshold)

def json_matrix(table):
  ap_list = ['28:C6:8E:0F:48:2E','B0:C7:45:6E:7E:BC']
  js = {}
  for row in table:
    #print "%s %s %s %s" % (row['client_mac_addr'], row['minified_raw_data/time'], row['minified_raw_data/mac'], row['minified_raw_data/power'])
    if not js.has_key(row['client_mac_addr']): js[row['client_mac_addr']] = {}
    k = js_day_formater("%s %s" % (day_formater(row['date']),row['minified_raw_data/time']))

    if not js[row['client_mac_addr']].has_key(k): js[row['client_mac_addr']][k] = {}

    if not js[row['client_mac_addr']][k].has_key('power') and not js[row['client_mac_addr']][k].has_key('ap'): 
      js[row['client_mac_addr']][k]['power'] = row['minified_raw_data/power']
      js[row['client_mac_addr']][k]['ap'] = ap_list.index(row['minified_raw_data/mac'])
    elif int(js[row['client_mac_addr']][k]['power']) < int(row['minified_raw_data/power']):
      js[row['client_mac_addr']][k]['power'] = row['minified_raw_data/power']
      js[row['client_mac_addr']][k]['ap'] = ap_list.index(row['minified_raw_data/mac'])

  return js

def json_points():
  return 1

def json_viz():
  return 1

js_matrix = json_matrix(fp_table)

# { '00:00:00:00:00:01':
#   {'13-10-15 16:01': {'ap': '28:C6:8E:0F:48:2E', 'power': -77},
#    '13-10-16 13:02': {'ap': '28:C6:8E:0F:48:2E', 'power': -74},
#    '13-10-16 14:32': {'ap': '28:C6:8E:0F:48:2E', 'power': -73},
#    '13-10-17 09:42': {'ap': '28:C6:8E:0F:48:2E', 'power': -78},
#    '13-10-18 10:03': {'ap': 'B0:C7:45:6E:7E:BC', 'power': -39},
#    '13-10-18 10:28': {'ap': 'B0:C7:45:6E:7E:BC', 'power': -41},
#    ...
#    '13-10-28 10:25': {'ap': 'B0:C7:45:6E:7E:BC', 'power': -43},
#    '13-10-28 10:32': {'ap': 'B0:C7:45:6E:7E:BC', 'power': -43},
#    '13-10-28 16:43': {'ap': 'B0:C7:45:6E:7E:BC', 'power': -43}
#   },
#   ...
# }

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
                    'nvisits': 1,
                    'avg_visit_duration': int(60/slot_segments)}
            register[row['client_mac_addr']]['timeslots'][time_slot_segmented(row['minified_raw_data/time'],slot_segments)][0] += 1
            register[row['client_mac_addr']]['timeslots'][time_slot_segmented(row['minified_raw_data/time'],slot_segments)][1] += row['minified_raw_data/power']
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
#   '00:00:00:00:00:01': {
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
#   '00:00:00:00:00:02': {
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
#   '00:00:00:00:00:0F': {
#    'avg_daily_power': -68,
#    'avg_visit_duration': 6,
#    'nreqs': 1,
#    'nvisits': 1,
#    'timeslots': {
#     '0h00': [0, 0],
#     ...

# Create dataset
ds_nreq_day_aux = []
ds_nreq_avgp_aux = []
ds_nreq_avgvd_aux = []
ds_nreq_nv_aux = []
ds_avgp_avgvd_aux = []
ds_aux = []
ds_count_aux = []
for day_key in days.keys():
  day = int(time.strftime("%d",time.gmtime(day_key)))
  for mac_key in days[day_key].keys():
    ds_nreq_day_aux.insert(0,[int(days[day_key][mac_key]['nreqs']), day])
    ds_nreq_avgp_aux.insert(0, [int(days[day_key][mac_key]['nreqs']), int(days[day_key][mac_key]['avg_daily_power'])])
    ds_nreq_avgvd_aux.insert(0,[int(days[day_key][mac_key]['nreqs']), int(days[day_key][mac_key]['avg_visit_duration'])])
    ds_nreq_nv_aux.insert(0,[int(days[day_key][mac_key]['nreqs']), int(days[day_key][mac_key]['nvisits'])])
    ds_avgp_avgvd_aux.insert(0, [int(days[day_key][mac_key]['avg_visit_duration']),int(days[day_key][mac_key]['avg_daily_power'])])
    if days[day_key][mac_key] > 5:
      ds_count_aux.insert(0,1)
    else:
      ds_count_aux.insert(0,0)
  
ds_d = np.array(ds_nreq_day_aux)
ds_v = np.array(ds_nreq_nv_aux)
ds_vd = np.array(ds_nreq_avgvd_aux)
ds_p = np.array(ds_nreq_avgp_aux)
ds_pvd = np.array(ds_avgp_avgvd_aux)
ds_c = np.array(ds_count_aux)
#dataset = (ds,ds_p,ds_c)
dataset = (ds_d,ds_c)
dataset_p = (ds_p,ds_c)
dataset_v = (ds_v,ds_c)
dataset_vd = (ds_vd,ds_c)
dataset_pvd = (ds_pvd, ds_c)
# 3D dataset
dataset_pvdd_3d = (np.array(zip(ds_p[:,1], ds_vd[:,1], ds_d[:,0])),ds_c)
dataset_pvdv_3d = (np.array(zip(ds_p[:,1], ds_vd[:,1], ds_v[:,1])),ds_c)

# Dynamically calculate ticks for axis, given a fixed amount of ticks
def axis_ticks(dataset,nticks):
  n_y = (dataset[0][:,1].max()-dataset[0][:,1].min())/nticks
  n_x = (dataset[0][:,0].max()-dataset[0][:,0].min())/nticks
  y_ticks = np.arange(dataset[0][:,1].min(),dataset[0][:,1].max(),n_y).tolist()
  x_ticks = np.arange(dataset[0][:,0].min(),dataset[0][:,0].max(),n_x).tolist()
  y_ticks.insert(len(y_ticks),y_ticks[-1]+n_y)
  x_ticks.insert(len(x_ticks),x_ticks[-1]+n_x)
    
  return x_ticks, y_ticks
    
# Print resulting datasets
pl.figure(figsize=(14, 12))
pl.subplots_adjust(left=.05, right=.99, bottom=.04, top=.99, wspace=.05, hspace=0.25)
n_sub_plots = 5
subplot_alpha = 0.01

# subplot nreqs vs days
pl.subplot(n_sub_plots, 1, 1)
#pl.title("nreqs vs days", size=18)
pl.scatter(dataset[0][:, 0], dataset[0][:, 1], alpha=subplot_alpha)
pl.xlabel("number of requests", size=12)
pl.ylabel("day of month", size=12)
pl.xlim(-50, 3000)
pl.ylim(-2, 30)
x_ticks, y_ticks = axis_ticks(dataset,5)
pl.xticks(x_ticks, size=10)
pl.yticks(y_ticks, size=10)
pl.text(.99, .01, ('%.2fs' % (t1 - t0)).lstrip('0'),
            transform=pl.gca().transAxes, size=15,
            horizontalalignment='right')
 
# subplot power vs nreqs
pl.subplot(n_sub_plots, 1, 2)
#pl.title("power vs nreqs", size=18)
pl.scatter(dataset_p[0][:, 0], dataset_p[0][:, 1], alpha=subplot_alpha)
pl.ylabel("power (dB)", size=12)
pl.xlabel("number of requests", size=12)
pl.ylim(-120, 2)
pl.xlim(-50, 3000)
x_ticks, y_ticks = axis_ticks(dataset_p,5)
pl.xticks(x_ticks, size=10)
pl.yticks(y_ticks, size=10)
pl.text(.99, .01, ('%.2fs' % (t1 - t0)).lstrip('0'),
            transform=pl.gca().transAxes, size=15,
            horizontalalignment='right')

# subplot number of visits vs nreqs
pl.subplot(n_sub_plots, 1, 3)
#pl.title("number of visits vs nreqs", size=18)
pl.scatter(dataset_v[0][:, 0], dataset_v[0][:, 1], alpha=subplot_alpha)
pl.ylabel("number of visits", size=12)
pl.xlabel("number of requests", size=12)
pl.ylim(-2, 24)
pl.xlim(-50, 3000)
x_ticks, y_ticks = axis_ticks(dataset_v,5)
pl.xticks(x_ticks, size=10)
pl.yticks(y_ticks, size=10)
pl.text(.99, .01, ('%.2fs' % (t1 - t0)).lstrip('0'),
            transform=pl.gca().transAxes, size=15,
            horizontalalignment='right')

# subplot visit duration vs nreqs
pl.subplot(n_sub_plots, 1, 4)
#pl.title("visit duration vs nreqs", size=18)
pl.scatter(dataset_vd[0][:, 0], dataset_vd[0][:, 1], alpha=subplot_alpha)
pl.ylabel("avg visit duration (m)", size=12)
pl.xlabel("number of requests", size=12)
pl.ylim(-50, 1500)
pl.xlim(-50, 3000)
x_ticks, y_ticks = axis_ticks(dataset_vd,5)
pl.xticks(x_ticks, size=10)
pl.yticks(y_ticks, size=10)
pl.text(.99, .01, ('%.2fs' % (t1 - t0)).lstrip('0'),
            transform=pl.gca().transAxes, size=15,
            horizontalalignment='right')

# subplot power vs visit duration
pl.subplot(n_sub_plots, 1, 5)
#pl.title("visit duration vs nreqs", size=18)
pl.scatter(dataset_pvd[0][:, 0], dataset_pvd[0][:, 1], alpha=subplot_alpha)
pl.ylabel("avg power (dB)", size=12)
pl.xlabel("avg visit duration (m)", size=12)
pl.ylim(-120, -2)
pl.xlim(-20, 1500)
x_ticks, y_ticks = axis_ticks(dataset_pvd,5)
pl.xticks(x_ticks, size=10)
pl.yticks(y_ticks, size=10)
pl.text(.99, .01, ('%.2fs' % (t1 - t0)).lstrip('0'),
            transform=pl.gca().transAxes, size=15,
            horizontalalignment='right')

# 3D graph
fig = pl.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(dataset_pvdd_3d[0][:,0], dataset_pvdd_3d[0][:,1], dataset_pvdd_3d[0][:,2], alpha=0.01)

ax.set_xlabel('Power (dB)')
ax.set_ylabel('Visit duration (m)')
ax.set_zlabel('Number of requests')

# 3D graph
fig = pl.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(dataset_pvdv_3d[0][:,0], dataset_pvdv_3d[0][:,1], dataset_pvdv_3d[0][:,2], alpha=0.01)

ax.set_xlabel('Power (dB)')
ax.set_ylabel('Visit duration (m)')
ax.set_zlabel('Number of visits')

# print
pl.show()
