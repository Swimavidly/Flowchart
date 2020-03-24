# -*- coding: utf-8 -*-
"""
Created on Thu Jul 25 13:27:15 2019

@author: avanfosson
"""
import svgwrite
import sys
import math
sys.path.append(r'D:\Code Stuff\pythonProjects\flowchart')
import svgflowchart

svgFile = 'flowchart.svg'
dwg = svgwrite.Drawing(filename=svgFile)

#Put flowchart here
padding = 10
defaultFormat = {'stroke': 'black', 'fill': 'none'}
blackFill = {'stroke': 'black', 'fill': 'black'}
redFill = {'stroke': 'red', 'fill': 'red'}
orangeFill = {'stroke': 'orange', 'fill': 'orange'}
yellowFill = {'stroke': 'yellow', 'fill': 'yellow'}
greenFill = {'stroke': 'green', 'fill': 'green'}
blueFill = {'stroke': 'blue', 'fill': 'blue'}
purpleFill = {'stroke': 'purple', 'fill': 'purple'}

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
                                  align='br', \
                                  gap=1.6, \
                                  characterHeightAdjustment=5, \
                                  textExtra = blackFill, \
                                  **defaultFormat)
#adjust text and left
boxTextObj.moveText('u', 10)
boxTextObj.moveText('l', 10)

dwg.add(boxTextObj)

connector = svgflowchart.JointedArrow(start=diamondObj.cb, \
                                      end=boxTextObj.boxObj.cr, \
                                          arrowWidth = 5, flip = True, \
                                              **blackFill)
dwg.add(connector)

upper = math.ceil(boxTextObj.boxObj.cb[1])+padding * 2
middle = math.floor(boxTextObj.boxObj.cb[0])
lower = upper + 100
lowest = lower + 100
left = middle - 100
right = middle + 100

testArrowBlack = svgflowchart.JointedArrow(start=(middle - 5, lower - 5), \
                                      end=(left, upper), \
                                          arrowWidth = 5, flip = True, \
                                              **blackFill)
dwg.add(testArrowBlack)

testArrowWhite = svgflowchart.JointedArrow(start=(middle - 5, lower-5), \
                                      end=(left, upper), \
                                          arrowWidth = 5, flip = False, \
                                              **defaultFormat)
dwg.add(testArrowWhite)

testArrowRed = svgflowchart.JointedArrow(start=(middle + 5, lower - 5), \
                                      end=(right, upper), \
                                          arrowWidth = 5, flip = True, \
                                              **redFill)
dwg.add(testArrowRed)

testArrowOrange = svgflowchart.JointedArrow(start=(middle + 5, lower - 5), \
                                      end=(right, upper), \
                                          arrowWidth = 5, flip = False, \
                                              **orangeFill)
dwg.add(testArrowOrange)

testArrowYellow = svgflowchart.JointedArrow(start=(middle - 5, lower + 5), \
                                      end=(left, lowest), \
                                          arrowWidth = 5, flip = True, \
                                              **yellowFill)
dwg.add(testArrowYellow)

testArrowGreen = svgflowchart.JointedArrow(start=(middle - 5, lower + 5), \
                                      end=(left, lowest), \
                                          arrowWidth = 5, flip = False, \
                                              **greenFill)
dwg.add(testArrowGreen)

testArrowBlue = svgflowchart.JointedArrow(start=(middle + 5, lower + 5), \
                                      end=(right, lowest), \
                                          arrowWidth = 5, flip = True, \
                                              **blueFill)
dwg.add(testArrowBlue)

testArrowPurple = svgflowchart.JointedArrow(start=(middle + 5, lower + 5), \
                                      end=(right, lowest), \
                                          arrowWidth = 5, flip = False, \
                                              **purpleFill)
dwg.add(testArrowPurple)

dwg.save(pretty=True)