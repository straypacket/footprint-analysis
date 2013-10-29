import time
from tables import *

fp_h5file = openFile("footprint.h5", mode = "r")
fp_table = fp_h5file.getNode('/footprint/sensors')

# Create dataset
aux_a = []
for r in fp_table:
  day = time.gmtime(r['date'])
  #print "%s %s" % (time.strftime("%d",day),r['minified_raw_data/time'])
  aux_a.insert(0,[r['minified_raw_data/time'],time.strftime("%d",day)])

fp_dataset = np.array([aux_a])

###
# Clustering
##
import time

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

dataset = datasets.make_moons(n_samples=n_samples, noise=.05)

colors = np.array([x for x in 'bgrcmykbgrcmykbgrcmykbgrcmyk'])
colors = np.hstack([colors] * 20)

pl.figure(figsize=(14, 3.5))
pl.subplots_adjust(left=.001, right=.999, bottom=.001, top=.86, wspace=.05,
                   hspace=.01)

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

for algorithm in [two_means, affinity_propagation, ms, spectral,
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
    pl.subplot(1, 6, plot_num)

    pl.title(str(algorithm).split('(')[0], size=18)
    pl.scatter(X[:, 0], X[:, 1], color=colors[y_pred].tolist(), s=10)

    if hasattr(algorithm, 'cluster_centers_'):
        centers = algorithm.cluster_centers_
        center_colors = colors[:len(centers)]
        pl.scatter(centers[:, 0], centers[:, 1], s=100, c=center_colors)
    pl.xlim(-2, 2)
    pl.ylim(-2, 2)
    pl.xticks(())
    pl.yticks(())
    pl.text(.99, .01, ('%.2fs' % (t1 - t0)).lstrip('0'),
            transform=pl.gca().transAxes, size=15,
            horizontalalignment='right')
    plot_num += 1

pl.show()