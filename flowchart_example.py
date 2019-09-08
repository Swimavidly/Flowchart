# -*- coding: utf-8 -*-
"""
Created on Thu Jul 25 13:27:15 2019

@author: avanfosson
"""
import svgwrite
import sys
import math
sys.path.append(r'C:\Users\avanfosson\Documents\Projects\PythonProjects\BetterGLE')
import svgflowchart

svgFile = 'flowchart.svg'
dwg = svgwrite.Drawing(filename=svgFile)

#Put flowchart here
padding = 10
defaultFormat = {'stroke': 'black', 'fill': 'none'}
blackFill = {'stroke': 'black', 'fill': 'black'}

boxObj = svgflowchart.Box((padding, padding), (100, 100), **defaultFormat)
dwg.add(boxObj)

ovalObj = svgflowchart.Oval(insert=(padding+boxObj.maxX, padding), \
               r=(boxObj.w, boxObj.ry), \
               **defaultFormat)
dwg.add(ovalObj)

diamondObj = svgflowchart.Diamond( (ovalObj.maxX+padding, padding), \
                     (ovalObj.w, ovalObj.h), \
                     **defaultFormat)
dwg.add(diamondObj)

arrowObj = svgflowchart.Arrow( (padding, padding+boxObj.maxY), \
                              (diamondObj.maxX, padding+boxObj.maxY), \
                              20, \
                              40 / math.sqrt(3), \
                              **blackFill)
dwg.add(arrowObj)

base = boxObj.w
height = math.sqrt(3)/2 * boxObj.w
triangleObj = svgflowchart.EquilateralTriangle( (padding+base/2, arrowObj.maxY), \
                                    (padding+base, arrowObj.maxY+height), \
                                    **defaultFormat )
dwg.add(triangleObj)
dwg.add(svgwrite.shapes.Circle(triangleObj.cc, **blackFill)) #centroid

boxTextObj = svgflowchart.BoxText( (triangleObj.maxX+padding, triangleObj.minY), \
                                  (boxObj.w * 2, boxObj.h), \
                                  """This is a whole bunch of test text.
Let's see where this goes!
I hope it goes to Narnia.""", \
                                  gap=1.6, \
                                  **defaultFormat)
dwg.add(boxTextObj)

dwg.save()