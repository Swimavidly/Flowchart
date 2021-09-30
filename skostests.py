# -*- coding: utf-8 -*-
"""
Created on Sat Mar 6 12:56:26 2021

@author: Alex VanFosson
"""

import skostools
from os import getcwd
from sys import path

# =============================================================================
# Set up logging
# =============================================================================

CWD = getcwd()

path.append( CWD )

logPath = '{}\\log'.format(CWD)

logConfigFile = '{}\\logging.json'.format(logPath)

path.append( logPath )

import custom_logging

logger = custom_logging.setup_logging(__name__, logConfigFile)

# =============================================================================
# Begin tests
# =============================================================================

logger.info("Begin testing.")

aScheme = skostools.ConceptScheme('https://example.com/schemes/a')

logger.debug("Scheme a created.")

bScheme = skostools.ConceptScheme('https://example.com/schemes/b')

logger.debug("Scheme b created.")

cScheme = skostools.ConceptScheme('https://example.com/schemes/c')

logger.debug("Scheme c created.")

#Populate test1
test1 = skostools.Concept('https://example.com/concepts/1')

aScheme.addTopConcept(test1)

test1.addPrefLabel("Test 1", "en")

test1.addAltLabel("Test one", "en")

test1.addHiddenLabel("test1", "en")

test1.addDefinition("First skostools test concept.", "en")

test1.addScopeNote("Inside Scheme A.", "en")

test1.addExample("test1 = skostools.Concept('https://example.com/concepts/1')", "en")

test1.addEditorialNote("Tests in scheme A are numbers. Tests in scheme B are Roman numerals.", "en")

test1.addHistoryNote("Test 1 was first defined on 12-July-2021.", "en")

test1.addChangeNote("This is here to test change notes.", "en")

#Populate test2
test2 = skostools.Concept('https://example.com/concepts/2')

aScheme.addConcept(test2)

test2.addPrefLabel("Test 2", "en")

#Populate testi
testi = skostools.Concept('https://example.com/concepts/i')

testi.addPrefLabel("Test I", 'en')

bScheme.addTopConcept(testi)

#Populate testii
testii = skostools.Concept('https://example.com/concepts/ii')

testii.addPrefLabel("Test II", 'en')

bScheme.addConcept(testii)

#Populate test one
testOne = skostools.Concept('https://example.com/concepts/one')

cScheme.addTopConcept(testOne)

#Relate concepts
test1.addExactMatch(testi)

testi.addExactMatch(testOne)

test2.addBroader(test1)

testi.addNarrower(testii)

test2.addBroadMatch(testi)

testii.addCloseMatch(test2)

#Test exception throwing

#Test reflexive triple
test1.addBroader(test1, False)

try:
    test1.addBroader(test1, True)
except skostools.ReflexiveError:
    logger.info("Self reference (reflexive triple) test passed.")
else:
    logger.info("Self reference (reflexive triple) test failed.")

#Test Scheme-Concept error
try:
    skostools.ConceptScheme(test1.uri)
except skostools.SchemeConceptError:
    logger.info("Concept-Scheme-Concept test passed.")
else:
    logger.info("Concept-Scheme-Concept test failed.")
    
#Test Top Concept error
try:
    aScheme.addTopConcept(test2)
except skostools.TopConceptError:
    logger.info("Top Concept test passed.")
else:
    logger.info("Top Concept test failed.")
    
#Test disjoing exact match error
try:
    test2.addExactMatch(testi)
except skostools.DisjointMatchError:
    logger.info("Disjoint exact match test passed.")
else:
    logger.info("Disjoint exact match test failed.")

#Write graphs to files
skostools.masterGraph.serialize(r'D:\Code Stuff\pythonProjects\skos\test\masterGraph.ttl', format='ttl')

#Test get methods
for l in aScheme.getConceptsByLabel(skostools.PlainLiteral("Test 1", 'en')):
    print(l)

tripleSet = test1.getAllTriples()

print( len(tripleSet) )
    
logger.info("End testing.")