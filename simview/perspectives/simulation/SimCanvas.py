"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2009, University of Tennessee
"""
import wx
import math

try:
    import OpenGL
except:
    import sys, os
    sys.path.insert(1,os.path.dirname(sys.executable))

import OpenGL.GL
try:
    from wx import glcanvas
    haveGLCanvas = True
except ImportError:
    haveGLCanvas = False
try:
    # The Python OpenGL package can be found at
    # http://PyOpenGL.sourceforge.net/
    from OpenGL.GL import *
    from OpenGL.GLU import *
    from OpenGL.GLUT import *
    haveOpenGL = True
except ImportError:
    haveOpenGL = False
    
# Color set
DEFAULT_COLOR = [1.0, 1.0, 0.0, .2]    
COLOR_RED     = [1.0, 0.0, 0.0, .2]
COLOR_GREEN   = [0.0, 1.0, 0.0, .2]
COLOR_BLUE    = [0.0, 0.0, 1.0, .2]
COLOR_YELLOW  = [1.0, 1.0, 0.0, .2]
COLOR_HIGHLIGHT = [.2, .2, .8, .5]

# List of shapes
SHAPE_LIST = []

import ShapeParameters

class SimPanel(wx.Panel):
    """
        3D viewer to support real-space simulation. 
    """
    window_name = "3dview"
    window_caption = "3D viewer"
    
    def __init__(self, parent, id = -1, plots = None, standalone=False, **kwargs):
        wx.Panel.__init__(self, parent, id = id, **kwargs)
        self.parent = parent
    
        #Add a sizer
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        sliderSizer = wx.BoxSizer(wx.HORIZONTAL)
    
        self.canvas    = CanvasBase(self) 
        self.canvas.SetMinSize((200,2100))

        #Add the model to it's sizer
        mainSizer.Add(self.canvas, 1, wx.EXPAND)

        #Add the Subsizers to mainsizer
        mainSizer.Add(sliderSizer, 0, wx.EXPAND)

        self.SetSizer(mainSizer)
        self.Bind(wx.EVT_CONTEXT_MENU, self._on_context_menu)
        
 
    def _on_context_menu(self, event):
        """
            Default context menu for a plot panel
        """
        # Slicer plot popup menu
        id = wx.NewId()
        slicerpop = wx.Menu()
        slicerpop.Append(id, '&Reset 3D View')
        wx.EVT_MENU(self, id, self.canvas.resetView)
       
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(slicerpop, pos)        
    
class CanvasBase(glcanvas.GLCanvas):
    """
        3D canvas to display OpenGL 3D shapes
    """
    window_name = "Simulation"
    window_caption = "Simulation"
    
    def __init__(self, parent):
        glcanvas.GLCanvas.__init__(self, parent, -1)
        self.init = False
        # initial mouse position
        self.lastx = self.x = 30
        self.lasty = self.y = 30
        self.tr_lastx = self.tr_x = 30
        self.tr_lasty = self.tr_y = 30
        self.size = None
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnMouseDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMotion)
        self.Bind(wx.EVT_MOUSEWHEEL, self._onMouseWheel)
        
        self.initialized = False
        self.shapes = []
        self.parent = parent
        
        # Reference vectors
        self.x_vec = [1,0,0]
        self.y_vec = [0,1,0]
        
        self.mouse_down = False
        self.scale = 1.0
        self.zoom  = 1.0
        self.translation = [0,0,0]
        
        # Bind to Edit events
        self.parent.Bind(ShapeParameters.EVT_EDIT_SHAPE, self._onEditShape)
        
    def resetView(self, evt=None):
        """
            Resets zooming, translation and rotation.
        """
        self.zoom = 1.0
        self.scale = 1.0
        self.x_vec = [1,0,0]
        self.y_vec = [0,1,0]
        glLoadIdentity()
        self.Refresh()
                
    def _onEditShape(self, evt):
        evt.Skip()
        evt.shape.highlight(True)
        for item in self.shapes:
            if not item == evt.shape:
                item.highlight(False)
        self.Refresh(False)

    def OnEraseBackground(self, event):
        pass # Do nothing, to avoid flashing on MSW.

    def OnSize(self, event):
        size = self.size = self.GetClientSize()
        if self.GetContext():
            glViewport(0, 0, size.width, size.height)
        event.Skip()

    def OnPaint(self, event):     
        size = self.GetClientSize()
        side = size.width
        if size.height<size.width:
            side = size.height
        
        if self.GetContext():
            glViewport(0, 0, side, side)
            self.SetMinSize((side,side))
            
        dc = wx.PaintDC(self)
        self.SetCurrent()
        if not self.init:
            self.InitGL()
            self.init = True
        self.OnDraw()
        event.Skip()        
        
    def _onMouseWheel(self, evt):
        # Initialize mouse position so we don't have unwanted rotation
        self.x, self.y = self.lastx, self.lasty = evt.GetPosition()
        self.tr_x, self.tr_y = self.tr_lastx, self.tr_lasty = evt.GetPosition()
        
        scale = 1.15
        if evt.GetWheelRotation()<0:
            scale = 1.0/scale
             
        self.zoom *= scale             
             
        glScale(scale, scale, scale)
        self.Refresh(False)
        
    def OnMouseDown(self, evt):
        self.SetFocus()
        self.CaptureMouse()
        self.x, self.y = self.lastx, self.lasty = evt.GetPosition()
        self.tr_x, self.tr_y = self.tr_lastx, self.tr_lasty = self.x, self.y
        self.mouse_down = True

    def OnMouseUp(self, evt):
        self.ReleaseMouse()
        self.mouse_down = False

    def OnRightUp(self, evt):
        self.OnMouseUp(evt)
        if self.x==self.tr_lastx and self.y==self.tr_lasty:
            self._on_context_menu(evt)

    def _on_context_menu(self, event):
        """
            Default context menu for a plot panel
        """
        id = wx.NewId()
        slicerpop = wx.Menu()
        slicerpop.Append(id, '&Reset 3D View')
        wx.EVT_MENU(self, id, self.resetView)
       
        pos = event.GetPosition()
        #pos = self.ScreenToClient(pos)
        self.PopupMenu(slicerpop, pos)        

    def OnMouseMotion(self, evt):
        if evt.Dragging() and evt.LeftIsDown():
            self.tr_lastx, self.tr_lasty = self.tr_x, self.tr_y
            x, y = evt.GetPosition()
            
            # Min distance to do anything
            if math.fabs(self.lastx-x)>10 or math.fabs(self.lasty-y)>10:
                
                self.lastx, self.lasty = self.x, self.y
        
                
                if math.fabs(self.lastx-x)>math.fabs(self.lasty-y):
                    self.x = x
                else:
                    self.y = y
                
                #self.x, self.y = evt.GetPosition()
                self.Refresh(False)
                
        elif evt.Dragging() and evt.RightIsDown():
            self.lastx, self.lasty = self.x, self.y
            self.tr_lastx, self.tr_lasty = self.tr_x, self.tr_y
            self.tr_x, self.tr_y = evt.GetPosition()
            self.Refresh(False)
            
    def InitGL( self ):      
        glutInitDisplayMode (GLUT_DOUBLE | GLUT_RGBA)
        #glShadeModel(GL_FLAT);
        
        glMatrixMode(GL_PROJECTION)
        
        glLight(GL_LIGHT0, GL_AMBIENT, [.2, .2, .2, 0])
        
        # Object color
        #glLight(GL_LIGHT0, GL_DIFFUSE, COLOR_BLUE)
        
        glLight(GL_LIGHT0, GL_POSITION, [1.0, 1.0, -1.0, 0.0])
        
        
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [1, 1, 1, 0])
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_BLEND)
        glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        
        glEnable ( GL_ALPHA_TEST ) ;
        glAlphaFunc ( GL_GREATER, 0 ) ;
        glPixelStorei(GL_PACK_ALIGNMENT, 1)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        
        glEnable(GL_NORMALIZE)
        glDepthFunc(GL_LESS)
        glEnable(GL_DEPTH_TEST)
        glDepthMask(GL_TRUE);
        glClearColor (1.0, 1.0, 1.0, 0.0);
        #glClear (GL_COLOR_BUFFER_BIT);
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        
        gluPerspective(0, 1.0, 0.1, 60.0);

        glMatrixMode(GL_MODELVIEW)

    def getMaxSize(self):
        max_size = 0.0
        # Ready to draw shapes
        for item in self.shapes:
            item.draw()
            l = item.get_length()
            if l>max_size:
                max_size = l
        return max_size

    def OnDraw(self):
        # clear color and depth buffers
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # use a fresh transformation matrix
        
        # get the max object size to re-scale
        max_size = 1.0
        # Ready to draw shapes
        for item in self.shapes:
            item.draw()
            l = item.get_length()
            if l>max_size:
                max_size = l
        
        max_size *= 1.05
        scale = self.scale/max_size
        glScale(scale, scale, scale)
        self.scale = max_size
        
        self.drawAxes()
        
        if self.mouse_down:
            if math.fabs((self.x - self.lastx))>math.fabs((self.y - self.lasty)):
                angle = 10.0*(self.x - self.lastx) / math.fabs(self.x - self.lastx) 
                glRotate(angle, self.y_vec[0], self.y_vec[1], self.y_vec[2]);
                self._rot_y(angle)
            elif math.fabs(self.y - self.lasty)>0:
                angle = 10.0*(self.y - self.lasty) / math.fabs(self.y - self.lasty) 
                glRotate(angle, self.x_vec[0], self.x_vec[1], self.x_vec[2]);
                self._rot_x(angle)

            self.lasty = self.y
            self.lastx = self.x
        
            w,h = self.GetVirtualSizeTuple()
        
            # Translate in the x-y plane
            vx = self.x_vec[0] * 2.0*float(self.tr_x - self.tr_lastx)/w \
               + self.y_vec[0] * 2.0*float(self.tr_lasty - self.tr_y)/h
            vy = self.x_vec[1] * 2.0*float(self.tr_x - self.tr_lastx)/w \
               + self.y_vec[1] * 2.0*float(self.tr_lasty - self.tr_y)/h
            vz = self.x_vec[2] * 2.0*float(self.tr_x - self.tr_lastx)/w \
               + self.y_vec[2] * 2.0*float(self.tr_lasty - self.tr_y)/h
            
            glTranslate(self.scale*vx/self.zoom, self.scale*vy/self.zoom, self.scale*vz/self.zoom)    
                
        # push into visible buffer
        self.SwapBuffers()
        
    def _matrix_mult(self, v, axis, angle):
        c = math.cos(angle)
        s = math.sin(angle) 
        x = axis[0]
        y = axis[1]
        z = axis[2]
        vx = v[0]*(x*x*(1-c)+c)   + v[1]*(x*y*(1-c)-z*s) + v[2]*(x*z*(1-c)+y*s)
        vy = v[0]*(y*x*(1-c)+z*s) + v[1]*(y*y*(1-c)+c)   + v[2]*(y*z*(1-c)-x*s)
        vz = v[0]*(x*z*(1-c)-y*s) + v[1]*(y*z*(1-c)+x*s) + v[2]*(z*z*(1-c)+c)
        return [vx, vy, vz]
    
    def _rot_y(self, theta):
        """
            Rotate the view by theta around the y-axis
        """
        angle = theta/180.0*math.pi 
        axis = self.y_vec
        self.x_vec = self._matrix_mult(self.x_vec, self.y_vec, -angle)
        
    def _rot_x(self, theta):
        """
            Rotate the view by theta around the x-axis
        """
        angle = theta/180.0*math.pi
        self.y_vec = self._matrix_mult(self.y_vec, self.x_vec, -angle)
        
        
    def addShape(self, shape, name=None):
        """
            Add a shape to the list of displayed shapes
            @param shape: BaseShape object
            @param name: name given to the shape
        """
        if not name==None:
            shape.name = name
        shape.params['order']=len(self.shapes)
        self.shapes.append(shape)
        self.Refresh(False)

    def delShape(self, name):
        """
            Delete a shape by name
            @param name: name of the shape to be deleted
        """
        for i in range(len(self.shapes)):
            if self.shapes[i].name == name:
                del self.shapes[i]
                break
        self.Refresh(False)

    def getMaxVolume(self):
        """
            Returns the maximum volume of the combination of all shapes.
            The maximum volume is the simple sum of the volumes of all the shapes.
            @return: sum of the volumes of all the shapes [float]
        """
        sum = 0
        for item in self.shapes:
            sum += item.get_volume()
        return sum

    def drawAxes(self):
        """ 
            Draw 3D axes
        """
        pos = self.scale * 0.7
       
        # Z-axis is red
        zaxis= Arrow(x=pos, y=-pos, z=0, r_cyl=self.scale*0.005, r_cone=self.scale*0.01, 
                     l_cyl=self.scale*0.1, l_cone=self.scale*0.05)
        zaxis.color = COLOR_RED
        zaxis.draw()
        
        # Y-axis is yellow
        yaxis= Arrow(x=pos, y=-pos, z=0, r_cyl=self.scale*0.005, r_cone=self.scale*0.01, 
                     l_cyl=self.scale*0.1, l_cone=self.scale*0.05)
        yaxis.color = COLOR_YELLOW
        yaxis.rotate(-90,0,0)
        yaxis.draw()
        
        # X-axis is green
        xaxis= Arrow(x=pos, y=-pos, z=0, r_cyl=self.scale*0.005, r_cone=self.scale*0.01, 
                     l_cyl=self.scale*0.1, l_cone=self.scale*0.05)
        xaxis.color = COLOR_GREEN
        xaxis.rotate(0,-90,0)
        xaxis.draw()
        
        glLight(GL_LIGHT0, GL_DIFFUSE, DEFAULT_COLOR)


class BaseShape:
    """
        Basic shape functionality
    """
    def __init__(self, x=0, y=0, z=0):
        self.name = ''
        ## Position
        self.x = x
        self.y = y
        self.z = z
        ## Orientation
        self.theta_x = 0
        self.theta_y = 0
        self.theta_z = 0
        
        # Params
        self.params = {}
        self.params['contrast']  = 1.0
        self.params['order']     = 0
        self.details = {}
        self.details['contrast'] = 'A-2'
        self.details['order']    = ' '
        
        self.highlighted = False
        self.color = DEFAULT_COLOR
    
    def get_volume(self):
        return 0
    
    def get_length(self):
        return 1.0
    
    def highlight(self, value=False):
        self.highlighted = value
        
    def rotate(self, alpha, beta, gamma):
        """ 
            Set the rotation angles of the shape
            @param alpha: angle around the x-axis [degrees]
            @param beta: angle around the y-axis [degrees]
            @param gamma: angle around the z-axis [degrees]
        """
        self.theta_x = alpha
        self.theta_y = beta
        self.theta_z = gamma
        
    def _rotate(self):
        """
            Perform the OpenGL rotation
            
            Note that the rotation order is reversed.
            We do Y, X, Z do be compatible with simulation...
        """
        
        glRotated(self.theta_z, 0, 0, 1)
        glRotated(self.theta_x, 1, 0, 0)
        glRotated(self.theta_y, 0, 1, 0)
        
    def _pre_draw(self):
        if self.highlighted:
            glLight(GL_LIGHT0, GL_DIFFUSE, COLOR_HIGHLIGHT)
        else:
            glLight(GL_LIGHT0, GL_DIFFUSE, self.color)


class Arrow(BaseShape):
    """
        Arrow shape used to show the three axes
    """
    def __init__(self, x=0, y=0, z=0, r_cyl=0.01, r_cone=0.02, l_cyl=0.3, l_cone=0.1):
        BaseShape.__init__(self, x, y, z)
        self.r_cyl = r_cyl
        self.r_cone = r_cone
        self.l_cyl = l_cyl
        self.l_cone = l_cone
           
    def draw(self):
        self._pre_draw()
        glPushMatrix()
        glTranslate(self.x, self.y, self.z)
        
        # Perform rotation
        glRotate(self.theta_x, 1, 0, 0)
        glRotate(self.theta_y, 0, 1, 0)
        glRotate(self.theta_z, 0, 0, 1)

        # Draw axis cylinder
        qobj = gluNewQuadric();
        gluCylinder(qobj, self.r_cyl, self.r_cyl, self.l_cyl, 15, 5);
                
        glTranslate(0, 0, self.z+self.l_cyl)
        
        # Draw cone of the arrow
        glutSolidCone(self.r_cone, self.l_cone, 30, 5)
        
        # Translate back to original position
        glTranslate(-self.x, -self.y, -self.z)
        glPopMatrix()

class Cone(BaseShape):
    """
        Conical shape
    """
    def __init__(self, x=0, y=0, z=0, radius=0.5, height=1):
        BaseShape.__init__(self, x, y, z)
        self.radius = radius
        self.height = height
        
    def draw(self):
        glPushMatrix()
        glTranslate(self.x, self.y, self.z)
        glutSolidCone(self.radius, self.height, 30, 5)
        self._rotate()
        glTranslate(-self.x, -self.y, -self.z)
        glPopMatrix()

class Sphere(BaseShape):
    """
        Spherical shape
    """
    def __init__(self, x=0, y=0, z=0, radius=10.0):
        BaseShape.__init__(self, x, y, z)
        self.name = 'sphere'
        self.params['radius'] = radius
        self.details['radius'] = 'A'
        
    def get_volume(self):
        return 4.0/3.0*math.pi*self.params['radius']*self.params['radius']*self.params['radius']
        
    def get_length(self):
        return 2.0*self.params['radius']
    
    def draw(self):
        self._pre_draw()
        glPushMatrix()
        glTranslate(self.x, self.y, self.z)
        #glutSolidSphere(self.params['radius'], 30, 30)
        qobj = gluNewQuadric();
        #gluQuadricDrawStyle(qobj,GLU_SILHOUETTE)
        gluSphere(qobj,self.params['radius'], 30, 30)
        glTranslate(-self.x, -self.y, -self.z)
        glPopMatrix()
        glLight(GL_LIGHT0, GL_DIFFUSE, DEFAULT_COLOR)

    def accept(self, visitor):
        return visitor.fromSphere(self)

    def accept_update(self, visitor):
        return visitor.update_sphere(self)

class Cylinder(BaseShape):
    """
        Cylinder shape, by default the cylinder is oriented along
        the z-axis. 
        
        The reference point of the cylinder is the center of the
        bottom circle.
    """
    def __init__(self, x=0, y=0, z=0, radius=10.0, length=100.0):
        BaseShape.__init__(self, x, y, z)
        self.name = 'cylinder'
        self.params['radius'] = radius
        self.params['length'] = length
        self.details['radius'] = 'A'
        self.details['length'] = 'A'
        
    def get_volume(self):
        return math.pi*self.params['radius']*self.params['radius']*self.params['length']
        
    def get_length(self):
        if self.params['length']>2.0*self.params['radius']:
            return self.params['length']
        else:
            return 2.0*self.params['radius']
        
    def draw(self):
        self._pre_draw()
        glPushMatrix()
        
        glTranslate(self.x, self.y, self.z)
        self._rotate() 
        qobj = gluNewQuadric();
        # gluCylinder(qobj, r_base, r_top, L, div around z, div along z)
        gluCylinder(qobj, self.params['radius'], self.params['radius'], self.params['length'], 15, 5);

        glTranslate(-self.x, -self.y, -self.z)
        glPopMatrix()
        glLight(GL_LIGHT0, GL_DIFFUSE, DEFAULT_COLOR)
        
    def accept(self, visitor):
        return visitor.fromCylinder(self)
        
    def accept_update(self, visitor):
        return visitor.update_cylinder(self)
        
# Fill the shape list
SHAPE_LIST.append(dict(name='Sphere',   id=wx.NewId(), cl=Sphere))
SHAPE_LIST.append(dict(name='Cylinder', id=wx.NewId(), cl=Cylinder))
        
def getShapes():
    """
        Returns a list of all available shapes
    """
    return SHAPE_LIST
    
def getShapeClass(id):
    """
        Returns a child class of BaseShape corresponding
        to the supplied shape ID.
        @param id: shape ID number
    """
    def f(s): return s['id']==id
    if SHAPE_LIST is not None:
        shape = filter(f, SHAPE_LIST)
        return shape[0]['cl']
    return None
    
def getShapeClassByName(name):
    """
        Returns a child class of BaseShape corresponding
        to the supplied shape name.
        @param name: shape name
    """
    def f(s): return s['name']==name
    if SHAPE_LIST is not None:
        shape = filter(f, SHAPE_LIST)
        return shape[0]['cl']
    return None
