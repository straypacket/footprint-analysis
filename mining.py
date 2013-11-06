###
# Run this third
###
import numpy as np
import pylab as pl

from sklearn import cluster, datasets
from sklearn.metrics import euclidean_distances
from sklearn.neighbors import kneighbors_graph
#from sklearn.preprocessing import StandardScaler
from sklearn import preprocessing
from sklearn import decomposition
from sklearn import manifold

from tables import *

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
#X = manifold.MDS().fit_transform(X)
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
    pl.xlim(-2, 3000)
    pl.ylim(-150, 2)
    pl.xticks(())
    pl.yticks(())
    pl.text(.99, .01, ('%.2fs' % (t1 - t0)).lstrip('0'),
            transform=pl.gca().transAxes, size=15,
            horizontalalignment='right')
    plot_num += 1

pl.show()