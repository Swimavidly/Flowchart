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

boxObj = svgflowchart.Box((padding, padding), (100, 100), **defaultFormat)
dwg.add(boxObj)

ovalObj = svgflowchart.Oval(insert=(2*padding+boxObj.w, padding), \
               r=(boxObj.w, boxObj.ry), \
               **defaultFormat)
dwg.add(ovalObj)

diamondObj = svgflowchart.Diamond( (ovalObj.cr[0]+padding, padding), \
                     (ovalObj.w, ovalObj.h), \
                     **defaultFormat)
dwg.add(diamondObj)

arrowObj = svgflowchart.Arrow( (padding, 2*padding+boxObj.h), \
                              (3*padding+boxObj.w+ovalObj.w+diamondObj.w, 2*padding+boxObj.h), \
                              20, \
                              40 / math.sqrt(3), \
                              **{'stroke': 'black', 'fill': 'black'})
dwg.add(arrowObj)

base = boxObj.w
height = boxObj.h
triangleObj = svgflowchart.Triangle( (padding+base/2, 3*padding+boxObj.h), \
                                    (padding+base, 3*padding+boxObj.h+height), \
                                    (padding, 3*padding+boxObj.h+height), \
                                    **defaultFormat )
dwg.add(triangleObj)

dwg.save()