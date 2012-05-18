import nxs
filename = "/home/m2d/data/output/5729_frame1_Iqxy.nxs"

fd = nxs.open(filename, 'rw')

fd.opengroup('mantid_workspace_1')
fd.opengroup('workspace')
fd.opendata('values')
y = fd.getdata().copy()

fd.closedata()

fd.opendata("errors")
e = fd.getdata().copy()


print y
print e

