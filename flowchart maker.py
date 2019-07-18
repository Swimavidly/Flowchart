# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 10:22:52 2019

@author: avanfosson
"""

import svgwrite
import math

def quadratic_formula(A, B, C):

	# get the coefficients from the user
    a = float(A)
    b = float(B)
    c = float(C)

    discRoot = math.sqrt((b * b) - 4 * a * c)
    root1 = (-b + discRoot) / (2 * a) # solving positive
    root2 = (-b - discRoot) / (2 * a) # solving negative

    return (root1, root2)

#Define shapes and drawing functions here
# Square
class Box(svgwrite.shapes.Rect):
    
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
        
# Diamond
class Diamond(svgwrite.shapes.Polygon):
    
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
        self.points = [self.ct, self.cr, self.cb, self.cl]
        svgwrite.shapes.Polygon.__init__(self, self.points, **extra)

# Arrow
class Arrow(svgwrite.path.Path):
    #TODO: Need to finish this class. Arrowhead should be a triangle.
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
        self.length = math.sqrt((E_x-S_x)**2 + (E_y-S_y)**2)
        if arrowHeadLength >= self.length or arrowHeadLength < 0:
            self.ahl = 0.1*self.length
        else:
            self.ahl = arrowHeadLength
        if arrowHeadWidth >= self.ahl or arrowHeadWidth < 0:
            self.ahw = 2 * self.ahl / math.sqrt(3)
        else:
            self.ahw = arrowHeadWidth
        
        #solve for the arrowhead points
        
        #C is the square of the hypotenuse of the right triangle formed between
        # the tail of the arrow and one of the points of the arrow's head
        C = (self.length-self.ahl)**2 + (self.ahw/2)**2
        #D is the square of the hypotenuse of the right triangle formed between
        # the tip of the arrow and one of the points of the arrow's head
        D = self.ahl**2 + (self.ahw/2)**2
        #F and G store complicated constant expressions to be used later
        G = C - D - S_x**2 + E_x**2 - (E_y - S_y)**2
        F = 4*(E_y - S_y)**2
        #A, B, and C are the coefficients of the quadratic equation used to
        # solve for the x-coordiates in the arrowhead points
        second = 4*(S_x - E_x)**2 + F
        first = 4*(S_x - E_x)*G - 2*E_x*F
        zeroth = G**2 - F*(D + E_x**2)
        #debug
        print(second, first, zeroth)
        (x_1, x_2) = quadratic_formula(second, first, zeroth)
        #debug
        print(x_1, x_2) 
        y_1 = E_y + math.sqrt(D - (E_x-x_1)**2) #TODO: Figure out where this broke
        y_2 = E_y - math.sqrt(D - (E_x-x_2)**2)
        #debug
        print(y_1, y_2)
        #Start forming the path
        svgwrite.path.Path.__init__(self, d='M {0} {1}'.format(start[0], \
                                    start[1]), **extra)
        self.push('L {0} {1}'.format(end[0], end[1]))
        if self.ahl != 0:
            self.push('M {0} {1}'.format(E_x, E_y)) #starts a subpath using absolute coordinates
            self.push('L {0} {1}'.format(x_1, y_1))
            self.push('L {0} {1}'.format(x_2, y_2))
            self.push('Z')
        
# Ellipse
class Oval(svgwrite.shapes.Ellipse):
    
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

svgFile = 'flowchart.svg'
dwg = svgwrite.Drawing(filename=svgFile)

#Put flowchart here
padding = 10
defaultFormat = {'stroke': 'black', 'fill': 'none'}

boxObj = Box((padding, padding), (100, 100), **defaultFormat)
dwg.add(boxObj)

ovalObj = Oval(insert=(2*padding+boxObj.w, padding), \
               r=(boxObj.w, boxObj.ry), \
               **defaultFormat)
dwg.add(ovalObj)

diamondObj = Diamond( (ovalObj.cr[0]+padding, padding), \
                     (ovalObj.w, ovalObj.h), \
                     **defaultFormat)
dwg.add(diamondObj)

arrowObj = Arrow( (padding, 2*padding+boxObj.h), \
                 (3*padding+boxObj.w+ovalObj.w+diamondObj.w, 2*padding+2*boxObj.h), \
                 20, 40 / math.sqrt(3), \
                 **{'stroke': 'black', 'fill': 'black'})
dwg.add(arrowObj)

dwg.save()