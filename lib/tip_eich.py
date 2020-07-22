#!/usr/bin/env python

#=================================================#
# Eich class for transformation of a calibrated 
# resistance thermometer to a temperature         
# 2010 HR@KIT
# Fixme: poly-fit is far from complete (not included)
#=================================================#
#Note: Huuuhu Ugly code! (HR/2019)
import logging
from numpy import *
import numpy as np
from scipy.interpolate import splev, splrep
#from scipy.interpolate import *
import re
import os

class TIPEich(object):
	""" Class for all thermometers
	Object takes following parameters:
	- name of thermomenter
	- calibration file
	- text file format, column R T:"RT"(default); column T R:"TR"
	- type of interpolation: cubic spline, linear
	"""
	def __init__(self,thermometer,eich_file,order="RT",type="linear"):
		""" load calibration """
		self.thermometer = thermometer
		self.eich_file = os.path.join("calibrations",eich_file)
		self.flip=False
		
		if order=="TR":
			self.flip = True
		else:
			"Default, do nothing"
			pass
		""" In the moment two possible interpolations, linear and cubic spline() """
		if type == "linear":
			self._openEich_lin()
		elif type == "spline":
			self._openEich_spline()
		else:
			self._openEich_lin()
			
	def loadEich(self):
		#self._openEich_spline()
		self._openEich_lin()
				
	def _mySort(self,R,T):
		"""  sorting pair of values """
		""" maybe not the most elegant python code, but works very well """
		TR={}
		for i in range(len(T)):
			TR[R[i]]=T[i]
		Rs=sort(R)
		R_T_sorted=[]
		for i in range(len(Rs)):
			R_T_sorted.append([ Rs[i], TR[Rs[i]]])
		return array(R_T_sorted)

			
	def _openEich_spline(self):
		""" fits a cubic spline to the calibration file data """
		""" should be used with care, if the knots are not dense """ 
		try:
			f = file(str(self.eich_file))
			data = array([(float(t),float(r)) for (t,r) in [l.split() for l in f]])
		except:
			print(self.thermometer+' failed')
			raise()
		
		if self.flip:
			DATA=self._mySort(data[:,1],data[:,0]) # _mysort(T,R)
		else:
			DATA=self._mySort(data[:,0],data[:,1]) # _mysort(R,T)
		try:
			self.R_T_sprep=splrep(DATA[:,0],DATA[:,1],s=0, k=3)
		except:
			print(self.thermometer+" error while processing cubic spline fit")
			raise Error('Opening of '+self.eich_file+": ("+self.thermometer+') failed ')
		
	def _openEich_lin(self):
		""" fits a linear spline to the calibration file data"""
		""" also useful if the calibration data is not dense (default) """
		try:
			data = self.open_data_to_matrix(str(self.eich_file))
		except:
			print(self.thermometer+' failed')
			raise Error('Opening of '+self.eich_file+": ("+self.thermometer+') failed ')
		if self.flip:
			DATA=self._mySort(data[:,1],data[:,0]) # _mysort(T,R)
			
		else:
			DATA=self._mySort(data[:,0],data[:,1]) # _mysort(R,T)
			#print(data[:,0],data[:,1])
		logging.info ("open "+str(self.eich_file)+ " calibration-file with "+ str(len(DATA[:]))+" datapoints for "+self.thermometer )
		
		self.R_T_sprep=splrep(DATA[:,0],DATA[:,1],s=0, k=1 )
		self.DATA =  DATA 


	def open_data_to_matrix(self,filename):
		""" read file and split line into array of float values"""
		""" comment  lines (/* and #) are skipped"""
		""" returns Numeric array,"""
		""" can be accessed e.g. by arr[r,c] , where r and c are rows and columns"""
		p=re.compile('(\s*#.*)|(\s*/\*.*)')
		data=[]
		try:
			file=open(filename)
			for l in file:
				if p.match(l):
					continue
				else:
					data.append([ float(str(tok)) for tok in l.split()])
			return array(data) 
		except:
			print("Error while processing: "+filename)
			exit(1)

	def _getT_from_splined_R(self,R=1000):
		""" returns value of spline interpolated fit """
		return splev(R, self.R_T_sprep, der=0, ext=3)  # ext=3 returns boundary value (ext=0 [default] extrapolates)

	def get_T_from_R(self,R):
		""" only function which should be called from outside """
		""" returns Temperature from a given Resistance """
		return float(self._getT_from_splined_R(R))

# generic error class
class Error(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

if __name__ == "__main__":
	""" A couple of unity tests  """
	
	import matplotlib.pyplot as plt
	Therm0 = TIPEich("mxc","RU-1000-BF0_007_U03316_mxc_LS.txt",
			order="RT",type="linear")
	
	spl = splrep(Therm0.DATA[:,0], Therm0.DATA[:,1])

	Rs = np.linspace(3,4.5, 100)
	Ts = splev(Rs, spl)
	plt.yscale("log")
	plt.plot(Therm0.DATA[:,0], Therm0.DATA[:,1], '.')
	plt.plot(Rs,Ts,'r-')

	TsL = splev(Rs, Therm0.R_T_sprep)
	plt.plot(Rs,TsL,'b-')
	plt.show()
	"""
	R=29000
	
	print ("linear interpolation:", Therm0.get_T_from_R(R))
	Therm1 = TIPEich("Coldplate","RuOx_LT_thermometer.txt",order="RT",type="spline")
	print ("qubic spline:", Therm1.get_T_from_R(R))
	"""