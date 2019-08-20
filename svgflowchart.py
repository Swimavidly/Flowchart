# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 10:22:52 2019

@author: avanfosson
"""

import svgwrite
import math
import logging

logger = logging.getLogger(__name__).addHandler(logging.NullHandler)

def quadratic_formula(A, B, C):

	# get the coefficients from the user
    a = float(A)
    b = float(B)
    c = float(C)

    discRoot = math.sqrt((b * b) - 4 * a * c)
    root1 = (-b + discRoot) / (2 * a) # solving positive
    root2 = (-b - discRoot) / (2 * a) # solving negative

    return (root1, root2)

def distance_formula(pt1, pt2):
    
    # pt1 and pt2 are tuples of x-y coordinates
    return math.sqrt((pt1[0]-pt2[0])**2 + (pt1[1]-pt2[1])**2)

# Each shape inherits shared variables and methods from the Shape class as well
# as an svgwrite class.
class Shape():
    
    def __init__(self, pts):
        assertionErrorString = "Variable \"pts\" must be a list of tuples that are of length 2."
        assert isinstance(pts, list), assertionErrorString
        for pt in pts:
            assert isinstance(pt, tuple), assertionErrorString
            assert len(pt)==2, assertionErrorString
        self.verticies = pts
        self.maxX = self.maxMinXY()[0]
        self.maxY = self.maxMinXY()[1]
        self.minX = self.maxMinXY()[2]
        self.minY = self.maxMinXY()[3]
        
    def maxMinXY(self):
        xMax = self.verticies[0][0]
        yMax = self.verticies[0][1]
        xMin = xMax
        yMin = yMax
        for (x, y) in self.verticies[1:]:
            if x > xMax : xMax = x
            if x < xMin : xMin = x
            if y > yMax : yMax = y
            if y < yMin : yMin = y
        return [xMax, yMax, xMin, yMin]
    
#Define shapes and drawing functions here
# Square
class Box(svgwrite.shapes.Rect, Shape):
    
    def __init__(self, insert=(0, 0), size=(1, 1), **extra):
        svgwrite.shapes.Rect.__init__(self, insert, size, None, None, \
                                      **extra)
        self.w = size[0] # width
        self.h = size[1] # height
        self.rx = self.w/2 # x "radius"
        self.ry = self.h/2 # y "radius"
        self.bl = (insert[0], insert[1] + self.h)
        self.br = (insert[0] + self.w, insert[1] + self.h)
        self.tl = insert
        self.tr = (insert[0] + self.w, insert[1])
        self.cc = ( (2 * insert[0] + self.w)/2, (2 * insert[1] + self.h)/2 )
        self.cb = (self.cc[0], self.bl[1])
        self.cl = (self.bl[0], self.cc[1])
        self.cr = (self.br[0], self.cc[1])
        self.ct = (self.cc[0], self.tl[1])
        Shape.__init__(self, [self.tl, self.tr, self.br, self.bl])
        
# Diamond
class Diamond(svgwrite.shapes.Polygon, Shape):
    
    def __init__(self, insert=(0, 0), size=(1, 1), **extra):
        self.w = size[0] # width
        self.h = size[1] # height
        self.rx = self.w/2 # x "radius"
        self.ry = self.h/2 # y "radius"
        self.cc = ( (2 * insert[0] + self.w)/2, (2 * insert[1] + self.h)/2 )
        self.cb = (self.cc[0], self.cc[1] + self.ry)
        self.cl = (self.cc[0] - self.rx, self.cc[1])
        self.cr = (self.cc[0] + self.rx, self.cc[1])
        self.ct = (self.cc[0], self.cc[1] - self.ry)
        Shape.__init__(self, [self.ct, self.cr, self.cb, self.cl])
        svgwrite.shapes.Polygon.__init__(self, self.verticies, **extra)

# Ellipse
class Oval(svgwrite.shapes.Ellipse, Shape):
    
    def __init__(self, insert=None, center=None, r=None, **extra):
        if r == None and insert != None and center !=None:
            #Define ellipse by upper left corner point and center point
            r = (center[0] - insert[0], center[1] - insert[1])
        elif center == None and insert != None and r !=None:
            #Define ellipse by upper left corner point and radii
            center = (insert[0] + r[0], insert[1] + r[1])
        elif insert == None and center != None and r != None:
            #Define ellipse by center point and radii
            insert = (center[0] - r[0], center[1] - r[1])
        elif insert != None and center != None and r != None:
            #Define ellipse by center point and radii
            insert = (center[0] - r[0], center[1] - r[1])
            logger.warning("""Creation of Oval object defined too many arguments: 
                           insert = {0}
                           center = {1}
                           r      = {2}
                           Only center and r will be used.""".format(insert, center, r) )
        else:
            raise Exception('Too many arguments passed to Oval with values of None.')
        svgwrite.shapes.Ellipse.__init__(self, center, r, **extra)
        self.rx = r[0] # x radius
        self.ry = r[1] # y radius
        self.w = 2 * self.rx # width
        self.h = 2 * self.ry # height
        self.cc = center
        self.cb = (self.cc[0], self.cc[1] + self.ry)
        self.cl = (self.cc[0] - self.rx, self.cc[1])
        self.cr = (self.cc[0] + self.rx, self.cc[1])
        self.ct = (self.cc[0], self.cc[1] - self.ry)
        Shape.__init__(self, [self.ct, self.cr, self.cb, self.cl])

# Triangle
class Triangle(svgwrite.shapes.Polygon, Shape):
    
    def __init__(self, insert=(0, 0), vertex1=(0, 0), vertex2=(0, 0), **extra):
        Shape.__init__(self, [insert, vertex1, vertex2])
        svgwrite.shapes.Polygon.__init__(self, self.verticies, **extra)
        # midpoint of the edge opposite the first vertex
        midpoint = ( (vertex1[0]+vertex2[0])/2, (vertex1[1]+vertex2[1])/2 )
        # centroid
        self.cc = ( insert[0]+(2/3)*(midpoint[0]-insert[0]), \
                   insert[1]+(2/3)*(midpoint[1]-insert[1]))

# Equilateral triangle
class EquilateralTriangle(Triangle):
    
    def __init__(self, insert=(0, 0), vertex1=(0, 0), CW=True, **extra):
        #These variables make the code easier to read
        x_1 = insert[0]
        y_1 = insert[1]
        x_2 = vertex1[0]
        y_2 = vertex1[1]
        # By default, the triangle is drawn clockwise
        if CW == True:
            vertex2 = ( ( x_1 + x_2 + math.sqrt(3) * (y_1 - y_2) )/2, \
                     ( y_1 + y_2 + math.sqrt(3) * (x_2 - x_1) )/2 )
        else:
            vertex2 = ( ( x_1 + x_2 - math.sqrt(3) * (y_1 - y_2) )/2, \
                     ( y_1 + y_2 - math.sqrt(3) * (x_2 - x_1) )/2 )
        Triangle.__init__(self, insert, vertex1, vertex2, **extra)

# Arrow
class Arrow(svgwrite.path.Path, Shape):

    def __init__(self, start=(0, 0), end=(0, 0), arrowHeadLength=10, \
                 arrowHeadWidth=10, **extra):
        
        #define the variables used to draw the arrow
        self.tail = start
        self.head = end
        #These four variables make the math easier to read later
        S_x = self.tail[0]
        S_y = self.tail[1]
        E_x = self.head[0]
        E_y = self.head[1]
        DeltaX = E_x - S_x
        DeltaY = E_y - S_y
        #Arrow's total length
        self.length = distance_formula(start, end)
        #Arrow's angle with the x-axis
        self.angle = math.atan2(DeltaY, DeltaX)
        if arrowHeadLength >= self.length or arrowHeadLength < 0:
            self.ahl = 0.1*self.length
        else:
            self.ahl = arrowHeadLength
        if arrowHeadWidth >= self.ahl or arrowHeadWidth < 0:
            self.ahw = 2 * self.ahl / math.sqrt(3)
        else:
            self.ahw = arrowHeadWidth
        
        #These variables make the math easier to read later
        l = self.ahl
        w = self.ahw/2
        alpha = self.angle
        beta = math.pi/2 + alpha
        gamma = alpha - math.pi/2
        
        #(x_0, y_0) is the intersection of the base of the arrowhead and the
        # arrow.
        x_0 = E_x - l*math.cos(alpha)
        y_0 = E_y - l*math.sin(alpha)
        
        #solve for the arrowhead points
        x_1 = x_0 + w*math.cos(beta)
        y_1 = y_0 + w*math.sin(beta)
        x_2 = x_0 + w*math.cos(gamma)
        y_2 = y_0 + w*math.sin(gamma)
        
        #Start forming the path
        svgwrite.path.Path.__init__(self, d='M {0} {1}'.format(start[0], \
                                    start[1]), **extra)
        self.push('L {0} {1}'.format(end[0], end[1]))
        if self.ahl != 0:
            self.push('M {0} {1}'.format(E_x, E_y)) #starts a subpath using absolute coordinates
            self.push('L {0} {1}'.format(x_1, y_1))
            self.push('L {0} {1}'.format(x_2, y_2))
            self.push('Z')
        
        Shape.__init__(self, [self.tail, self.head, (x_1, y_1), (x_2, y_2)])