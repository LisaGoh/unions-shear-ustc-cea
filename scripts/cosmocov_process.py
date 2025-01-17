#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import numpy as np
from numpy import linalg as LA
import matplotlib.pyplot as plt
import sys

def get_cov(filename):

	data = np.loadtxt(filename)
	ndata = int(np.max(data[:,0]))+1

	print("Dimension of cov: %dx%d"%(ndata,ndata))

	ndata_min = int(np.min(data[:,0]))
	cov_g = np.zeros((ndata,ndata))
	cov_ng = np.zeros((ndata,ndata))
	for i in range(0,data.shape[0]):
		cov_g[int(data[i,0]),int(data[i,1])] =data[i,8]
		cov_g[int(data[i,1]),int(data[i,0])] =data[i,8]
		cov_ng[int(data[i,0]),int(data[i,1])] =data[i,9]
		cov_ng[int(data[i,1]),int(data[i,0])] =data[i,9]

	return cov_g, cov_ng, ndata


if __name__ == '__main__':
	
	covfile = sys.argv[1]
	
	c_g, c_ng, ndata = get_cov(covfile)	
	cov = c_ng+c_g
	cov_g = c_g

	b = np.sort(LA.eigvals(cov))
	print("min+max eigenvalues cov: %e, %e"%(np.min(b), np.max(b)))
	if(np.min(b)<=0.):
		print("non-positive eigenvalue encountered! Covariance Invalid!")
		exit()

	print("Covariance is postive definite!")

	pp_var = []
	for i in range(ndata):
	
		pp_var.append(cov[i][i])

	np.savetxt(covfile+'.txt',cov)
	print("covmat saved as %s" %covfile+'.txt')
    
	np.savetxt(covfile+'_g.txt',cov_g)
	print("Gaussian covmat saved as %s" %covfile+'_g.txt')

	cmap = 'seismic'

	pp_norm = np.zeros((ndata,ndata))
	for i in range(ndata):
		for j in range(ndata):
			pp_norm[i][j] = cov[i][j]/ np.sqrt(cov[i][i]*cov[j][j])

	print("Plotting correlation matrix ...")

	plot_path = covfile+'_plot.pdf'
	fig = plt.figure()
	ax = fig.add_subplot(1, 1, 1)
	for i in range(1,21):
		if i==10:
			plt.axvline(x=20*i,color='black',linewidth=1.5)
			plt.axhline(y=20*i,color='black',linewidth=1.5)
		else:
			plt.axvline(x=20*i,color='black',linewidth=0.3)
			plt.axhline(y=20*i,color='black',linewidth=0.3)


# plt.axvline(x=20*20,color='black')
# plt.axvline(x=40*20,color='black')
# plt.axhline(y=10*20,color='black')
# plt.axhline(y=20*20,color='black')
# plt.axhline(y=40*20,color='black')
	im3 = ax.imshow(pp_norm, cmap=cmap, vmin=-1, vmax=1)
	# ax.set_xticks(np.arange(0,440,40))
	# ax.set_yticks(np.arange(0,440,40))
	fig.colorbar(im3, orientation='vertical')

	ax.text(10, 44, r'$\xi_+^{ij}(\theta)$', fontsize=12)
	ax.text(30, 44, r'$\xi_-^{ij}(\theta)$', fontsize=12)
	ax.text(-10, 10, r'$\xi_+^{ij}(\theta)$', fontsize=12)
	ax.text(-10, 30, r'$\xi_-^{ij}(\theta)$', fontsize=12)
	# ax.set_title('ShapePipe BlindC',fontsize=15)
	# ax.text(565, -15, r'$\gamma_t^{ij}(\theta)$', fontsize=14)
	# ax.text(815, -15, r'$w^{i}(\theta)$', fontsize=14)

	# ax.text(905, 95, r'$\xi_+$', fontsize=14)
	# ax.text(905, 295, r'$\xi_-$', fontsize=14)
	# ax.text(905, 595, r'$\gamma_t$', fontsize=14)
	# ax.text(905, 845, r'$w$', fontsize=14)
	plt.savefig(plot_path,dpi=2000)
	plt.show()
	print("Plot saved as %s"%(plot_path))

