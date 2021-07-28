import numpy as np
import matplotlib.pyplot as plt
from time import perf_counter

from sas_gen import *

# test fourier file that can handle cells of different types - may be slower than other file

def get_normal_vec(geometry):
    """return array of normal vectors of elements"""
    v1 = geometry[:, 1] - geometry[:, 0]
    v2 = geometry[:, 2] - geometry[:, 0]
    normals = np.cross(v1, v2)
    temp = np.linalg.norm(normals, axis=-1)
    normals = normals / np.linalg.norm(normals, axis=-1)[..., None]
    return normals

def face_transform(geometry, geometry_shifted, active, normals, sep_vecs, qx, qy):
    """carries out fourier transform
    accepts pos_x, pos_y, pos_z, elements
    pos_x/y/z = 1D array of x/y/z positions
    elements is a 3D array: subvolumes x faces x vertices
    qx, qy are floats

    returns an array of fourier transforms for each of the subvolumes provided

    algorithm based off: An implementation of an efficient direct Fourier transform of polygonal areas and
                        volumes
                        Brian B. Maranville
                        https://arxiv.org/abs/2104.08309
    """
    # small value used in case where a fraction should limit to a finite answer with 0 on top and bottom
    # used in 2nd/3rd terms in sum over vertices
    eps = 1e-30
    # create the Q vector
    Q = np.array([qx+eps, qy+eps, 0+eps])
    # create the Q normal vector as the dot product of Q with the normal vector * the normal vector:
    # separately store the component of the Qn vector for later use
    # np.dot: (faces x normal_vector_coords) * (Q_coords) -> (faces)
    Qn_comp = np.dot(normals, Q)
    # Qn is the vector PARALLEL to the surface normal Q// in the referenced paper eq. (14)
    # np (*) (faces x 1) * (faces x normal_vector_coords) -> (faces x Qn_coords)
    Qn = Qn_comp[..., None] * normals
    # extract the parallel component of the Q vector
    # (1 x Q_coords) - (faces x Qn_coords)
    Qp = (Q[None, :] - Qn)[:, None, :]
    # extract the normal component of the displacement of the plane using the first point (faces)
    rn_norm = np.sum(geometry[:,0] * normals, axis=-1)
    # calculate the face-dependent prefactor for the sum over vertices (faces) 
    # TODO: divide by zero error - can nan and inf handle this?
    prefactor = (1j * Qn_comp * np.exp(1j * Qn_comp * rn_norm)) / np.sum(Q * Q)
    # calculate the sum over vertices term
    # TODO: divide by zero error - can nan and inf handle this?
    # the sub sum over the vertices in eq (14) (faces)
    sub_sum = np.zeros_like(prefactor, dtype="complex")
    term = np.zeros((geometry.shape[0], geometry.shape[1]))
    # the terms in the expr (faces)
    # WARNING: this uses the opposite sign convention as the article's code but agrees with the sign convention of the
    # main text - it takes line segment normals as pointing OUTWARDS from the surface - giving the 'standard' fourier transform
    # e.g. fourier transform of a box gives a positive sinc function
    term = (np.sum(Qp * np.cross(sep_vecs, normals[:, None, :]), axis=-1)) / np.sum(Qp * Qp, axis=-1)
    term = term * (np.exp(1j * np.sum(Qp * geometry_shifted, axis=-1)) - np.exp(1j * np.sum(Qp * geometry, axis=-1)))
    term = term / np.sum(Qp*sep_vecs, axis=-1)
    term[inactive] = 0
    sub_sum = prefactor*np.sum(term, axis=-1)
    # sum over all the faces in each subvolume to return an array of transforms of sub_volumes
    return sub_sum

def create_geometry(output):
    position_coords = np.column_stack((output.pos_x, output.pos_y, output.pos_z))
    position_coords = np.concatenate((position_coords, [[0,0,0]])) # add dummy vertex to flesh out arrays
    new_index = len(output.pos_x) - 1
    # make array non jagged so numpy can efficiently process
    if output.are_elements_identical:
        # all elements have same no. of faces, and all faces have same number of vertices
        # can cast directly to numpy array
        num_faces = output.elements.shape[0]*output.elements.shape[1]
        faces_full = output.elements.reshape(num_faces, output.elements.shape[2])
        faces_full = np.concatenate((faces_full, faces_full[:, :1]), axis = 1)
        inactive = np.concatenate((np.zeros((num_faces, output.elements.shape[2]), dtype=bool), np.ones((num_faces, 1), dtype=bool)), axis=1)
        sizes = output.elements.shape[1]*np.ones((output.elements.shape[0]))
    else: #arrays are jagged
        sizes = np.array([len(element) for element in output.elements])
        lengths = np.array([len(face) for element in output.elements for face in element])
        faces = np.array([index for element in output.elements for face in element for index in face])
        first_faces = np.array([face[0] for element in output.elements for face in element])
        max_len = max(lengths) + 1 # wrapping of last vertex
        # set active vertices
        inactive = np.ones((len(lengths), max_len), dtype=bool)
        r = np.arange(max_len)
        inactive[lengths[:, None] > r[None, :]] = False
        # set dummy vertices
        faces_full = np.ones_like(inactive) * new_index
        faces_full[lengths[:, None] > r[None, :]] = faces
        faces_full[lengths[:, None] == r[None, :]] = first_faces
    geometry = position_coords[faces_full]
    normals = get_normal_vec(geometry)
    return geometry, inactive, normals, sizes


reader = VTKReader()
#output = reader.read("C:\\Users\\Robert\\Documents\\STFC\\VTK_testdata\\originals\\NETGEN_magnetic_cylinder_non_uniform_cells.vtk")
output = reader.read("C:\\Users\\Robert\\Documents\\STFC\\VTK_testdata\\originals\\NETGEN_magnetic_cylinder.vtk")
#pre calculate geometric features - no need to recalculate for each Q
geometry, inactive, normals, sizes = create_geometry(output)
geometry_shifted = np.concatenate((geometry[:, (geometry.shape[1]-1):(geometry.shape[1]), :], geometry[:, :(geometry.shape[1]-1), :]), axis=1)
sep_vecs = geometry_shifted-geometry

qx = np.linspace(-10, 10, 1)
qy = np.linspace(-10, 10, 1)
qxs, qys = np.meshgrid(qx, qy)
qxs = qxs.flatten()
qys = qys.flatten()
results = np.zeros_like(qxs, dtype=complex)

for i in range(len(qxs)):
    results[i] = np.sum(face_transform(geometry, geometry_shifted, inactive, normals, sep_vecs, qxs[i], qys[i]))
    print(i)
#
#import matplotlib.pyplot as plt
#from matplotlib import colors, cm
#
#extent = (qx.min(), qx.max(), qy.min(), qy.max())
#fig1 = plt.figure()
#plt.imshow(abs(output), extent=extent, aspect=1, cmap=cm.get_cmap("jet"))
#plt.title('$Abs(FT)$')
#plt.xlabel('$Q_x$', size='large')
#plt.ylabel('$Q_y$', size='large')
#plt.axis
#plt.colorbar()
#fig2 = plt.figure()
#plt.imshow(np.imag(output), extent=extent, aspect=1, cmap=cm.get_cmap("jet"))
#plt.title('Real FT')
#plt.xlabel('$Q_x$', size='large')
#plt.ylabel('$Q_y$', size='large')
#plt.colorbar()
#plt.show()
#
#
##print(sub_volume_transform(pos_x, pos_y, pos_z, elements, 0.1, 0))
##plt.plot(qx, np.abs(output))
##plt.yscale("log")
##plt.show()