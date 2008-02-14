try:
    from sans.models.prototypes.SimCylinder import SimCylinder
except:
    print "This test uses the prototypes module."
    
from sans.models.CylinderModel import CylinderModel

import os, sys

def simulate(filename="simul.txt", npts=500):
    output_file = open(filename, 'w')
    #output_file = open("simul_phi=0_theta=1_57_l=400_r=20_9.txt", 'w')
    
    sim = SimCylinder()
    sim.setParam('scale', 1.0)
    #sim.setParam('length', 100.0)
    #sim.setParam('radius', 40.0)
    sim.setParam('length', 400.0)
    sim.setParam('radius', 20.0)
    sim.setParam('theta', 1.57)
    sim.setParam('phi', 0.0)
    sim.setParam('qmax', 0.2)
    
    output_file.write("<q_value>  <ana_value>  <sim_value>\n")
    norma = 0
    for i in range(npts):
        q = 1.0/npts*(i+1)
        
        cyl_val = sim.run(q)
        sim_val = sim.run([q, 0.0])
        if i==0:
            norma = cyl_val/sim_val
        
        #print q, cyl_val, sim_val, sim_val/cyl_val
        output_file.write("%10g %10g %10g\n" % (q, cyl_val, sim_val*norma))
        
    output_file.close()
     
def create_model():
    sim = SimCylinder()
    sim.setParam('scale', 1.0)
    sim.setParam('length', 100.0)
    sim.setParam('radius', 40.0)
    # simul and simul_2
    #sim.setParam('theta', 1.57)
    #sim.setParam('phi', 0.0)
    sim.setParam('theta', 0.0)
    sim.setParam('phi', 1.0)
    sim.setParam('qmax', 0.2)
    return sim
    
def comp(): 
    """
        Simple test that should give 1 for the ratio
        of simulated and analytical
    """
    sim = create_model()
    
    ana_val = sim.run(.05)
    sim_val = sim.run([0.05, 0])
    print ana_val, sim_val, ana_val/sim_val
    
    
#    ana_val = sim.run(.05)
#    sim_val = sim.run([0.05, 1])
#    print ana_val, sim_val, ana_val/sim_val
    
#    sim = create_model()
#    sim.setParam('theta', 1.0)
#    sim.setParam('phi', 1.0)   
#    ana_val = sim.run(.05)
#    sim_val = sim.run([0.05, 1])
#    print ana_val, sim_val, ana_val/sim_val
    
#    sim = create_model()
#    sim.setParam('theta', 1.0)
#    sim.setParam('phi', 2.0)
#    ana_val = sim.run(.05)
#    sim_val = sim.run([0.05, 1])
#    print ana_val, sim_val, ana_val/sim_val
    
    sim = create_model()
    sim.setParam('theta', 1.0)
    sim.setParam('phi', -2.0)
    ana_val = sim.run(.05)
    sim_val = sim.run([0.15, 1])
    print ana_val, sim_val, ana_val/sim_val
    
def add_error_to_file(prefix = "", dir = "output"):
    import os, math
    
    # Open standard deviation file
    std_file = open("%s/std_simul.txt" % dir, 'r')
    std_content = std_file.read()
    std_lines = std_content.split('\n')
    
    std_values = {}
    for line in std_lines:
        if line == std_lines[0]:
            continue
        
        toks = line.split()
        if not len(toks) > 3:
            continue

        std_values[toks[0]] = float(toks[2])
    
    std_file.close()
    
    # Read the files
    
    file_list = os.listdir(dir)
    
    for file in file_list:
        if file.count(prefix)>0:
            print "Reading", file
    
            file_obj = open("%s/%s" % (dir, file), 'r')
            
            # open new file
            file_new = open("%s/error-%s" % (dir, file), 'w')
            file_content = file_obj.read()
            lines = file_content.split('\n')
            for line in lines:
                if line == lines[0]:
                    file_new.write(line+'\n')
                    continue
                    
                toks = line.split()
                
                if not len(toks) == 3:
                    file_new.write(line+'\n')
                    continue
            
                error = 0
                if toks[0].lower() in std_values:
                    error = float(toks[2]) * std_values[toks[0].lower()]
                    
                file_new.write(line+" %10g\n" % error)
                
            file_obj.close()
            file_new.close()
    
    
    
def std_estimate(prefix = "", dir="output"):
    import os, math
    
    file_list = os.listdir(dir)
    output_file = open("%s/std_simul.txt" % dir, 'w')
    output_file.write("<q_value>   <std>  <frac>\n")
    values = {}
    
    for file in file_list:
        if file.count(prefix)>0:
            print "Reading", file
            file_obj = open("%s/%s" % (dir, file), 'r')
            file_content = file_obj.read()
            lines = file_content.split('\n')
            for line in lines:
                if line == lines[0]:
                    continue
                toks = line.split()
                
                if not len(toks) == 3:
                    continue
                
                if toks[0] not in values:
                    values[toks[0]] = []
                    
                values[toks[0]].append(float(toks[2]))
                                       
    q_list = values.keys()
    q_list.sort()                 
    for q in q_list:
        num = len(values[q])
        sum = 0
        mean = 0
        for val in range(num):
            mean += values[q][val] 
        mean /= num
            
        for val in range(num):
            diff = values[q][val] - mean
            sum += diff * diff
        sum /= (num-1)
        #print q, math.sqrt(sum)
    
        output_file.write("%10s %10g %10g %10g\n" % (q, math.sqrt(sum), math.sqrt(sum)/mean, math.sqrt(sum)/mean*100.0))
        
    output_file.close()
    
    
    # sqrt( 1/(N-1) sum[ (x-mean)**2 ] )
    
def test_volume_pts():
    import random, math, time
    
    print "Generating points"
    pt_list = []
    for i in range(50000):
        x = random.random()
        y = random.random()
        z = random.random()
        pt_list.append([x, y, z])
        
    # Compute list of closest distance for each point
    print "Computing distances"
    closest_list = []
    t_init = time.time()
    
    for i in range(len(pt_list)):
        if math.fmod(i,100)==0:
            print i, time.time()-t_init
            t_init = time.time()
        pt = pt_list[i]
        
        min_dist = -1.0
        for j in range(i+1, len(pt_list)):
            pt_2 = pt_list[j]
            #print pt_2
            dx = pt[0]-pt_2[0]
            dy = pt[1]-pt_2[1]
            dz = pt[2]-pt_2[2]
            dist = math.sqrt( dx*dx + dy*dy + dz*dz ) 
            if min_dist<0 or dist < min_dist:
                min_dist = dist
             
        closest_list.append(min_dist)        
        
    # Analyze list of distances
    print "Analyzing"
    sum = 0
    for d in closest_list:
        sum += d
    average = sum/len(closest_list)
    
    sum = 0
    for d in closest_list:
        diff = d - average
        sum += diff*diff
    sum /= len(closest_list)
    
    print "%5g +/- %5g)" % (average, math.sqrt(sum))
    
                              
            
    
if __name__ == '__main__':
    #test_volume_pts()
    #simulate("simul_phi=0_theta=1_57_l=400_r=20_test.txt")
    #std_estimate("simul_phi=0_theta=1_57_l=400_r=20")
    #add_error_to_file("l=400_r=20.txt")
    
    option = "error"
    
    #if len(sys.argv)>1:
    if len(option)>0:
        if option=="gen":
            ifile = 0
            for i in range(100):
                ifile += 1
                #print "simul_qmax=1_phi=0_theta=1_57_l=400_r=20_%g.txt" % ifile
                #simulate("simul_phi=0_theta=1_57_l=400_r=20_%g.txt" % ifile)
                print "simul_qmax=1_phi=0_theta=1_57_l=400_r=20_%g.txt" % ifile
                simulate("output/pt5000/simul_phi=0_theta=1_57_l=400_r=20_%g.txt" % ifile)
        elif option=="comp":
            comp()
        elif option=="std":
            #std_estimate("simul_phi=0_theta=1_57_l=400_r=20")
            std_estimate("simul_phi=0_theta=1_57_l=400_r=20", "output/pt5000")
        elif option=="error":
            #add_error_to_file("l=400_r=20.txt")
            add_error_to_file("l=400_r=20_1.txt", "output/pt5000")
            