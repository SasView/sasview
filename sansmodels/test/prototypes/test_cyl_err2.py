try:
    from sans.models.prototypes.SimCylinderF import SimCylinderF
except:
    print "This test uses the prototypes module."
from sans.models.CylinderModel import CylinderModel
import time, math, random

def reset(seed=0):
    sim = SimCylinderF()
    sim.setParam('radius', 20)
    sim.setParam('length', 200)
    sim.setParam('phi', 1)
    sim.setParam('theta', 1)
    sim.setParam('seed', math.fmod(time.time()*100+seed,10000))
    return sim

# number of times to repeat each point
N_q = 50
# Relative error on the simulation
sig_val = 0.20


counter = 0

sim = reset()
sph = CylinderModel()


sph.setParam('radius', 20)
sph.setParam('length', 200)
sph.setParam('scale', 1)
sph.setParam('contrast',1)
sph.setParam('length', 200)
sph.setParam('cyl_phi', 1)
sph.setParam('cyl_theta', 1)

vol = math.pi*20*20*200

f = open('sim_err_cyl.txt', 'w')
f.write("<q>  <npts>  <sigma>\n")




for i_npts in range(1):

    # Find which q has an error of sig_val
    #print err    
    q_sigma = 0
    i_min = 0
    i_max = 0
    i_last_max = 0
    val_min = 0
    val_max = 0
    last_error = 0
    last_val = 0
    error_vec = []
    
    found_it = False
    i_vec = 0
        
    
    t_0 = time.time()
    npts = 50000
    #npts = 50000*i_npts+1000
    #npts = 1000 * math.pow(2.0,(i_npts+1))
    
    sim = reset()
    #sim.setParam('npoints', npts)
    
    # Vectors of errors
    err = []
    for i in range(80):
        q = 0.40*(i) /50
        
        
        # For each Q, repeat the simulation N_q times
        sum_q_ana = 0
        sum_q_sim = 0
        sum = 0
        vec = []
        for i_q in range(N_q):
            counter += 1
            sim = reset(counter)
            #sim.setParam('npoints', npts)
                    
            simval = sim.run([q, 0])
            sum_q_ana += sph.run([q, 0])
            sum_q_sim += simval
            
            vec.append(simval)
            
        mean = sum_q_sim/N_q
        for val in range(N_q):
            diff = vec[val] - mean
            sum += diff * diff
        sum /= (N_q-1)

        ana_value = sum_q_ana/N_q
        sim_value = sum_q_sim/N_q
        
         
        try:    
            err_i = [q, (sim_value-ana_value)/ana_value, ana_value, math.sqrt(sum)/ana_value]
        except:
            err_i = [q,0,0,0]
        
        err.append(err_i)
                    
        print err_i
    
        
        # update extrema
        if val_min > err_i[2]:
            val_min = err_i[2]
            
        if val_max < err_i[2]:
            val_max = err_i[2]
        
        # Find a minimum, where the error changes sign
        if last_val==val_min and err_i[2] > val_min:
            
            
            #print "  min", err_i[0]
            if i_min > 0:
                i_plateau = i_last_max
      
                # check error for plateau
                #if math.fabs(err[i_plateau][1])>sig_val:
                if math.fabs(err[i_max][3])>sig_val:
                    error_vec.append(err[i_plateau])
                    t_f = time.time()
                    pred = sph.run([err[i_plateau][0],0])
                    print '[',t_f-t_0,']',math.pow((vol/npts),-.6666), 'n=',npts, 'q=',err[i_plateau][0], \
                        'err=',math.fabs(err[i_plateau][1]), i_min, 'sig=',err[i_plateau][3]
                        
                    f.write("%10g %10g %10g\n" % (err[i_plateau][0], npts, err[i_plateau][3]))
                    found_it = True
                    break
                
            i_min = i_vec
            # Get ready for next maximum
            val_max = val_min
            
        # check if we are at max
        elif last_val==val_max and err_i[2]<val_max:
            #print "   max", err[i_vec-1][0], err[i_vec-1][1]
            i_last_max = i_max
            i_max = i_vec-1
            # get ready for next minimum
            val_min = val_max

        last_error = err_i[1]
        last_val = err_i[2]
        i_vec += 1

        
    if found_it == False:
        print "Could not complete", npts
    #print "Npts = %g; %s" %(npts, str(len(error_vec)))
        

f.close()

