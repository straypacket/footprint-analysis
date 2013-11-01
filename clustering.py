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

def time_to_secs(time_string):
  t_a = time_string.split(':')
  return int(t_a[0])*60*60+int(t_a[1])*60

def time_slot(time_string):
  t_a = time_string.split(':')
  return int(t_a[0])

def time_slot_segmented(time_string,hour_segments):
  if hour_segments == 0:
    hour_segments = 1
  t_a = time_string.split(':')
  return "%sh%s" % (int(t_a[0]),(int(t_a[1])/(60/hour_segments))*(60/hour_segments))

def build_time_a(slots,hour_segments):
  if hour_segments == 0:
    hour_segments = 1
  time_hash = {}
  for s in xrange(slots):
    for hs in xrange(hour_segments):
      time_hash["%sh%s" % (s,hs*(60/hour_segments))] = 0

  return time_hash

def daily_struct(table):
  days = {}
  nodays = {}
  day_mac_prevtime = {}
  slot_segments = 4
  # Unique days
  for d, rows_grouped_by_day in itertools.groupby(table, day_selector):
    if not days.has_key(d): days[d] = {}
    if not day_mac_prevtime.has_key(d): day_mac_prevtime[d] = {}
  # Queries per unique day per mac:
  for dd in days.keys():
    for row in table:
      if row['date'] == dd:
        if not days[dd].has_key(row['client_mac_addr']):
          days[dd][row['client_mac_addr']] = [1, row['minified_raw_data/power'], 0, build_time_a(24,slot_segments)]
          days[dd][row['client_mac_addr']][3][time_slot_segmented(row['minified_raw_data/time'],slot_segments)] += 1
          nodays[row['client_mac_addr']] = [1, row['minified_raw_data/power'], 0, build_time_a(24,slot_segments)]
          nodays[row['client_mac_addr']][3][time_slot_segmented(row['minified_raw_data/time'],slot_segments)] += 1
        else:
          days[dd][row['client_mac_addr']][0] += 1
          days[dd][row['client_mac_addr']][1] += row['minified_raw_data/power']
          days[dd][row['client_mac_addr']][3][time_slot_segmented(row['minified_raw_data/time'],slot_segments)] += 1
          nodays[row['client_mac_addr']][0] += 1
          nodays[row['client_mac_addr']][1] += row['minified_raw_data/power']
          nodays[row['client_mac_addr']][3][time_slot_segmented(row['minified_raw_data/time'],slot_segments)] += 1

        day_mac_prevtime[dd][row['client_mac_addr']] = time_to_secs(row['minified_raw_data/time'])

  return days, nodays

days, nodays = daily_struct(fp_table)
#print "Bench took %s seconds" % (timeit.timeit(stmt="daily_struct(fp_table)", setup="from __main__ import *", number=1))

# Results in days:
# {1380240000.0: {'40:25:C2:BB:47:34': [2, -164]},
#  1380758400.0: {'C0:63:94:77:3E:A5': [2, -179],
#   'CE:9E:00:07:BF:32': [1, -68],
#   'E2:0C:7F:D6:05:7C': [2, -138],
#   'E8:8D:28:B6:70:AF': [2, -193]},
#  1380844800.0: {'CE:9E:00:07:BF:32': [1, -80]},
#  1381017600.0: {'02:C9:D0:7B:7B:C9': [1, -88], 'C8:6F:1D:62:DD:39': [1, -87]},
#  1381104000.0: {'44:A7:CF:AA:F9:42': [1, -86]},
#  1381190400.0: {'42:F4:07:11:09:EC': [1, -66]},
#  1381276800.0: {'64:80:99:36:15:80': [2, -116],
#   '8C:2D:AA:C4:0A:17': [2, -144],
#   '9E:E6:35:13:58:5B': [1, -75],
#   'A4:C3:61:7F:57:64': [1, -67],
#   'CC:78:5F:AE:40:8E': [1, -82]},

##
# End of ugly code
##

ds_reqs_aux = []
ds_avgp_aux = []
ds_c_aux = []
for dddd in days.keys():
  day = int(time.strftime("%d",time.gmtime(dddd)))
  for ddd in days[dddd].keys():
    ds_aux.insert(0,[int(days[dddd][ddd]), day])
    ds_reqs_aux.insert(0,[int(days[dddd][ddd][0]), day])
    ds_avgp_aux.insert(0,[int(days[dddd][ddd][1]/days[dddd][ddd][0]), day])
    if days[dddd][ddd] > 5:
      ds_c_aux.insert(0,1)
    else:
      ds_c_aux.insert(0,0)

# ds_aux = []
# for ddd in nodays.keys():
#   ds_aux.insert(0,[int(nodays[ddd]), 10])
  
ds = np.array(ds_reqs_aux)
ds_c = np.array(ds_c_aux)
ds_p = np.array(ds_avgp_aux)
#dataset = (ds,ds_p,ds_c)
dataset = (ds,ds_c)

###
# Clustering
##
import numpy as np
import pylab as pl

from sklearn import cluster, datasets
from sklearn.metrics import euclidean_distances
from sklearn.neighbors import kneighbors_graph
#from sklearn.preprocessing import StandardScaler
from sklearn import preprocessing
from sklearn import decomposition
from sklearn import manifold

np.random.seed(0)

# Generate datasets. We choose the size big enough to see the scalability
# of the algorithms, but not too big to avoid too long running times
n_samples = 1500

#dataset = datasets.make_moons(n_samples=n_samples, noise=.05)

colors = np.array([x for x in 'bgrcmykbgrcmykbgrcmykbgrcmyk'])
colors = np.hstack([colors] * 20)

pl.figure(figsize=(14, 12))
pl.subplots_adjust(left=.001, right=.999, bottom=-.001, top=.96, wspace=.05,
                   hspace=0.30)

plot_num = 1

X, y = dataset
# normalize dataset for easier parameter selection
#X = preprocessing.StandardScaler().fit_transform(X)
#X = preprocessing.MinMaxScaler().fit_transform(X)
#X = preprocessing.scale(X)
#X = preprocessing.Normalizer().fit_transform(X)
#X = preprocessing.Binarizer().fit_transform(X)
#X = preprocessing.Binarizer(threshold=20).fit_transform(X)
#
#X = decomposition.RandomizedPCA().fit_transform(X)
#X = decomposition.RandomizedPCA(whiten=True).fit_transform(X)
#X = decomposition.PCA().fit_transform(X)
#X = decomposition.PCA(whiten=True).fit_transform(X)
#X = decomposition.ProbabilisticPCA().fit_transform(X)
#X = decomposition.ProbabilisticPCA(whiten=True).fit_transform(X)
#X = decomposition.KernelPCA().fit_transform(X)
#X = decomposition.SparsePCA().fit_transform(X)
#X = decomposition.FastICA().fit_transform(X)
#X = decomposition.FastICA(whiten=True).fit_transform(X)
#X = decomposition.NMF().fit_transform(X)
#X = decomposition.ProjectedGradientNMF().fit_transform(X)
#X = decomposition.ProjectedGradientNMF(sparseness='data').fit_transform(X)
#X = decomposition.NMF(sparseness='data').fit_transform(X)
#X = decomposition.NMF(sparseness='components').fit_transform(X)

#X = manifold.Isomap().fit_transform(X)
#X = manifold.LocallyLinearEmbedding(eigen_solver='dense').fit_transform(X)
X = manifold.MDS().fit_transform(X)
#X = manifold.SpectralEmbedding().fit_transform(X)

# estimate bandwidth for mean shift
bandwidth = cluster.estimate_bandwidth(X, quantile=0.9)

# connectivity matrix for structured Ward
connectivity = kneighbors_graph(X, n_neighbors=50)
# make connectivity symmetric
connectivity = 0.5 * (connectivity + connectivity.T)

# Compute distances
#distances = np.exp(-euclidean_distances(X))
distances = euclidean_distances(X)

# create clustering estimators
kmeans = cluster.KMeans(n_clusters=2)
ms = cluster.MeanShift(bandwidth=bandwidth, bin_seeding=True)
two_means = cluster.MiniBatchKMeans(n_clusters=2)
ward_five = cluster.Ward(n_clusters=2, connectivity=connectivity)
ward_agglo = cluster.WardAgglomeration(n_clusters=2)
spectral = cluster.SpectralClustering(n_clusters=2,
                                      eigen_solver='arpack',
                                      affinity="nearest_neighbors",
                                      n_neighbors=250)
dbscan = cluster.DBSCAN(eps=1)
affinity_propagation = cluster.AffinityPropagation(damping=.99
                                                   ,convergence_iter=3
                                                   ,max_iter=1
                                                   ,verbose=True)
                                                   #,preference=-200)

for algorithm in [kmeans, two_means, ms, ward_five, dbscan,
                      affinity_propagation, spectral]:
    # predict cluster memberships
    t0 = time.time()
    algorithm.fit(X)
    t1 = time.time()
    if hasattr(algorithm, 'labels_'):
        y_pred = algorithm.labels_.astype(np.int)
    else:
        y_pred = algorithm.predict(X)

    # plot
    pl.subplot(7, 1, plot_num)

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