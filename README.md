# Usage

## Schema
The file `schema.py` defines the schema used for PyTables, and therefore should be run first.

We'll be creating three tables, according to the data already available in the PostgreSQL server: 

* **SensorData** - This table will have data from each MAC address, per day

* **minified_raw_data** - This sub-table has raw data from the routers

* **minified_data** - This sub-table has processed data from the routers

## Importing data
To import and process the data from PostgreSQL, `importer.py` will read the data with the psycopg2 library and write it into a PyTables table.

## Accounting
Preprocessing of the data accurs with `accounting.py`. Here we calculate each day and MAC address':

* **Average Daily Power**
* **Average Visit Duration**
* **Number of Requests**
* **Number of Visits**
* **Timeslots**
* **Total Daily Minutes**

The average daily power is the sum of all the powers divided by the number of requests and the average visit duration is calculated by dividing the total daily minutes by the slot time threshold.

Resulting in data formated in the following fashion:

	
	 {1380240000.0: {		
	   '40:25:C2:BB:47:34': {
	    'avg_daily_power': -82,
	    'avg_visit_duration': 6,
	    'nreqs': 2,
	    'nvisits': 2,
	    'timeslots': {
	     '0h00': [0, 0],
	     '0h06': [0, 0],
	     ...
	     '9h48': [1, -98],
	     '9h54': [0, 0]},
	    'total_minutes': 12}},
	  1380758400.0: {
	   'C0:63:94:77:3E:A5': {
	    'avg_daily_power': -90,
	    'avg_visit_duration': 6,
	    'nreqs': 2,
	    'nvisits': 2,
	    'timeslots': {
	     '0h00': [0, 0],
	     '0h06': [1, -59],
	     ...
	     '9h54': [0, 0]},
	    'total_minutes': 12},
	   'CE:9E:00:07:BF:32': {
	    'avg_daily_power': -68,
	    'avg_visit_duration': 6,
	    'nreqs': 1,
	    'nvisits': 1,
	    'timeslots': {
	     '0h00': [0, 0],
	     ...

It will then create 2D datasets, according to the number of requests. Two extra 3D datasets are created with power, visit duration and number of requests as well as power, visit duration and number of visits in the X, Y and Z axes , respectively.


## Exporting data
With the help of `exporter.py` we export the computed data back into PostgreSQL, in the `footprint_stats` table.
The table has the following columns:

 * **day** - Day of measurement, as *integer*
 * **mac_address** - Mac Address, as *varchar(18)*
 * **avg_daily_power** - Average daily power for the MAC address, as *integer*
 * **avg_visit_duration** - Average daily visit duration for the MAC address, as *integer*
 * **nreqs** - Total number of requests for the MAC address, as *integer*
 * **nvisits** - Total number of visits for the MAC address, as *integer*
 * **total_minutes** - Total minutes of visit for the MAC address, as *integer*
 * **timeslots** - timeslot structure for the MAC address, as *JSON*
 
A single row typically looks like:

`1382918400 | 88:30:8A:74:F4:C2 |             -43 |                 24 |     8 |       6 |           120 | {"14h00": {"visits": 0, "power": 0}, "16h30": {"visits": 1, "power": -43}, … `

## Mining and graphing
Here be dragons :) The file `mining.py` has our datamining playground with help of sklearn for the algorithms and PyLab for graphing.

We use the datasets created in the accounting section and make some prepsocessing (normalizing or scaling) operations before. We then do some dimensionality reduction (tipically PCA) and finally apply clustering algorithms before graphing for 2D and 3D plots. 
