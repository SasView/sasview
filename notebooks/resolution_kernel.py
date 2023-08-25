import numpy as np

kernel_fwhmwidth = 2 #extent to which convolution kernel goes out.
kernel_finesse = 201  #finesse (number of points) over the concolution kernel - should be ODD number

#Where the sigma comes from and if it is a vector?
#Gausian:  FWHM = (2*sqrt(2*log(2))) = 2.3548 sigma
gaussian_fwhm = 2.3548*sigma
#TopHat:   FWHM = 3.4 sigma,  HWHM = 1.7 sigma
tophat_fwhm = 3.4 * sigma
#Triangular: FWHM = 2.45 sigma,  FWHM = Base Half-Width
triangular_fwhm = 2.45 * sigma

#TODO: Are these defined for each q point?
lambda_fwhm = triangular_fwhm
theta_fwhm = tophat_fwhm
pixel_fwhm = tophat_fwhm
binning_fwhm = tophat_fwhm

def delta_kernel_1d(x0,x,dx):
    y = np.zeros(len(x))
    [a, temp] = min(abs(x - x0))
    y(temp) = 1
    y =  y / (sum(y) * dx)
    return y

def make_resolution_kernels(q_vector):

    for n, q in enumerate(q_vector):
        #These are different resolution terms, so it has to be defined
        fwhm_max = max([lambda_fwhm(n), theta_fwhm(n), pixel_fwhm(n), binning_fwhm(n)])

        low = q - kernel_fwhmwidth * fwhm_max
        high = q + kernel_fwhmwidth * fwhm_max
        dx = (high - low) / (kernel_finesse - 1) #Make sure there is an ODD number of points - why this is important
        #TODO: check if dx is integer
        new_x = np.linspace(low, high, dx)

        #Delta - Function Starter Kernel - default kernel to start convoluting with
        weight_final = delta_kernel_1d(q, new_x, dx)

