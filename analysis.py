from tables import *

fp_h5file = openFile("footprint.h5", mode = "r")
fp_table = fp_h5file.getNode('/footprint/sensors')

for r in fp_table:
  #do stuff
  
