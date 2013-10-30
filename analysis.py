import time
import itertools
from tables import *

fp_h5file = openFile("footprint.h5", mode = "r")
fp_table = fp_h5file.getNode('/footprint/sensors')

# Create dataset
aux_a = []
for r in fp_table:
  day = time.gmtime(r['date'])
  #print "%s %s" % (time.strftime("%d",day),r['minified_raw_data/time'])
  aux_a.insert(0,[r['minified_raw_data/time'],time.strftime("%d",day)])

fp_dataset = np.array(aux_a)

##
# Ugly code, this needs to be put in the importer
##
# Group by days
def day_selector(row):
  #day = time.gmtime(row['date'])
  #return time.strftime("%y-%m-%d",day)
  return row['date']

def daily_struct(table):
  days = {}
  nodays = {}
  # Unique days
  for d, rows_grouped_by_day in itertools.groupby(table, day_selector):
    if not days.has_key(d): days[d] = {}  
  # Queries per unique day per mac:
  for dd in days.keys():
    for row in table:
      if row['date'] == dd:
        if not days[dd].has_key(row['client_mac_addr']): 
          days[dd][row['client_mac_addr']] = 1
          nodays[row['client_mac_addr']] = 1
        else:
          days[dd][row['client_mac_addr']] += 1
          nodays[row['client_mac_addr']] += 1

  return days, nodays

days, nodays = daily_struct(fp_table)
#print "Bench took %s seconds" % (timeit.timeit(stmt="daily_struct(fp_table)", setup="from __main__ import *", number=1))

# Results in days:
# {1380240000.0: {'40:25:C2:BB:47:34': 2},
#  1380758400.0: {'C0:63:94:77:3E:A5': 2,
#   'CE:9E:00:07:BF:32': 1,
#   'E2:0C:7F:D6:05:7C': 2,
#   'E8:8D:28:B6:70:AF': 2},
#  1380844800.0: {'CE:9E:00:07:BF:32': 1},
#  1381017600.0: {'02:C9:D0:7B:7B:C9': 1, 'C8:6F:1D:62:DD:39': 1},
#  1381104000.0: {'44:A7:CF:AA:F9:42': 1},
#  1381190400.0: {'42:F4:07:11:09:EC': 1},
#  1381276800.0: {'64:80:99:36:15:80': 2,
#   '8C:2D:AA:C4:0A:17': 2,
#   '9E:E6:35:13:58:5B': 1,
#   'A4:C3:61:7F:57:64': 1,
#   'CC:78:5F:AE:40:8E': 1},
#  1381363200.0: {'00:19:87:FF:76:E4': 4,
#   '00:21:5C:48:ED:33': 1,
#   '00:22:FA:86:BD:1A': 1,
#   '00:26:4A:F3:FF:63': 3,
#   ...
#   'F0:D1:A9:5F:59:D3': 192,
#   'F0:D1:A9:67:3B:B7': 9,
#   'F0:D1:A9:AE:CE:8B': 516}}


##
# End if ugly code
##

ds_aux = []
ds_c_aux = []
for dddd in days.keys():
  day = int(time.strftime("%d",time.gmtime(dddd)))
  for ddd in days[dddd].keys():
    ds_aux.insert(0,[int(days[dddd][ddd]), day])
    if days[dddd][ddd] > 5:
      ds_c_aux.insert(0,1)
    else:
      ds_c_aux.insert(0,0)

# ds_aux = []
# for ddd in nodays.keys():
#   ds_aux.insert(0,[int(nodays[ddd]), 10])
  
ds = np.array(ds_aux)
ds_c = np.array(ds_c_aux)
dataset = (ds,ds_c)

###
# Clustering
##
import numpy as np
import pylab as pl

from sklearn import cluster, datasets
from sklearn.metrics import euclidean_distances
from sklearn.neighbors import kneighbors_graph
from sklearn.preprocessing import StandardScaler

np.random.seed(0)

# Generate datasets. We choose the size big enough to see the scalability
# of the algorithms, but not too big to avoid too long running times
n_samples = 1500

#dataset = datasets.make_moons(n_samples=n_samples, noise=.05)

colors = np.array([x for x in 'bgrcmykbgrcmykbgrcmykbgrcmyk'])
colors = np.hstack([colors] * 20)

pl.figure(figsize=(14, 10))
pl.subplots_adjust(left=.001, right=.999, bottom=-.001, top=.96, wspace=.05,
                   hspace=0.30)

plot_num = 1

X, y = dataset
# normalize dataset for easier parameter selection
X = StandardScaler().fit_transform(X)

# estimate bandwidth for mean shift
bandwidth = cluster.estimate_bandwidth(X, quantile=0.3)

# connectivity matrix for structured Ward
connectivity = kneighbors_graph(X, n_neighbors=10)
# make connectivity symmetric
connectivity = 0.5 * (connectivity + connectivity.T)

# Compute distances
#distances = np.exp(-euclidean_distances(X))
distances = euclidean_distances(X)

# create clustering estimators
ms = cluster.MeanShift(bandwidth=bandwidth, bin_seeding=True)
two_means = cluster.MiniBatchKMeans(n_clusters=2)
ward_five = cluster.Ward(n_clusters=2, connectivity=connectivity)
spectral = cluster.SpectralClustering(n_clusters=2,
                                      eigen_solver='arpack',
                                      affinity="nearest_neighbors")
dbscan = cluster.DBSCAN(eps=.2)
affinity_propagation = cluster.AffinityPropagation(damping=.9,
                                                   preference=-200)

for algorithm in [two_means, ms, spectral,
                  ward_five, dbscan]:
    # predict cluster memberships
    t0 = time.time()
    algorithm.fit(X)
    t1 = time.time()
    if hasattr(algorithm, 'labels_'):
        y_pred = algorithm.labels_.astype(np.int)
    else:
        y_pred = algorithm.predict(X)

    # plot
    pl.subplot(6, 1, plot_num)

    pl.title(str(algorithm).split('(')[0], size=18)
    pl.scatter(X[:, 0], X[:, 1], color=colors[y_pred].tolist(), s=10)

    if hasattr(algorithm, 'cluster_centers_'):
        centers = algorithm.cluster_centers_
        center_colors = colors[:len(centers)]
        pl.scatter(centers[:, 0], centers[:, 1], s=100, c=center_colors)
    pl.xlim(-2, 200)
    pl.ylim(-2, 30)
    pl.xticks(())
    pl.yticks(())
    pl.text(.99, .01, ('%.2fs' % (t1 - t0)).lstrip('0'),
            transform=pl.gca().transAxes, size=15,
            horizontalalignment='right')
    plot_num += 1

pl.show()