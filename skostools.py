# -*- coding: utf-8 -*-
"""
Created on Wed Mar  3 12:47:59 2021

This module is my attempt to implement https://pypi.org/project/python-skos/
in python 3. I want to be able to treat SKOS concepts (or terms) as python
OBJECTS that can be added to or deleted from a Concept Scheme (vocabulary) and
be able to track changes in the relationships between concepts.

SKOS and RDF, a brief explanation:
    
RDF is an abstract methodology for storing and sharing data and information
across the internet. SKOS is a web standard based on RDF used to share
vocabularies. Both SKOS and RDF store information in units called triples.

Each triple is composed of three URIs. The first URI is called the subject.
The subject is the thing the triple describes. The second URI is the predicate.
The predicate is the type of information the triple describes about the
subject. The object is the information itself.

You can think of each triple as a statement of fact. For example, the triple
https://www.example.com/people/jane : https://www.example.com/hasName : "Jane"
means Jane's name is Jane. The subject, https://www.example.com/people/jane,
is the URI representing the idea of Jane. The predicate, https://www.example.com/hasName,
represents the idea of having a name. The object, "Jane", is Jane's name.

At this point you are probably thinking that this is an overly complicated way
to say that Jane is named Jane. And you would be right. However RDF and SKOS
are meant to represent much more complicated information and relationships
than a person's name. And their flexibility is what makes them powerful and
worth learning.

@author: Alex VanFosson
"""
# =============================================================================
# MAJOR TODO ITEMS
# 1) Create a settings file that can be used to control how SKOS consistency
# and conventions are handled. For example, the default should be to prevent
# SKOS inconsistencies, but allow convention to be broken (and warn the user).
# 2) Finish creating exceptions based on https://www.w3.org/TR/skos-reference/
# 3) The settings file should also control how far the entailments go. For
# example, if a user wants to explicitly add transitive properties, then they
# can set that level, or they can set 0 entailments and only add triples
# explicitly.
# 4) Every SKOS predicate should be an object.
# 5) The sets of SKOS properties should be dictionaries with the URIs as keys
# and the predicate objects as values.
# 6) Each symmantic relationship object should have an inverse property and a
# transitive property (or method) that can be called by the concept method.
# =============================================================================

import rdflib
import logging

# =============================================================================
# Configure logging for the skostools module
# =============================================================================

# Create a logger with the same name as the module
logger = logging.getLogger(__name__)

# Assign a null handler to the logger to suppress output. Users of this module
# may add handlers to this logger in their own code if they want to log
# messages. This puts control of logging configuration in the user's hands.
logger.addHandler(logging.NullHandler())

# TODO: I should convert this module to a package and define the global variables in the initialization file (__init__.py)
# Helpful: https://realpython.com/python-modules-packages/#python-packages

# =============================================================================
# Instantiation of variables internal to the module.
# =============================================================================

#Variables to store namespaces
RDF = rdflib.namespace.RDF
SKOS = rdflib.namespace.SKOS

#Sets of URIs of SKOS properties (predicates)
SKOSLabels = {SKOS.altLabel,
              SKOS.hiddenLabel,
              SKOS.prefLabel}

SKOSNotes = {SKOS.definition,
             SKOS.changeNote,
             SKOS.editorialNote,
             SKOS.example,
             SKOS.historyNote,
             SKOS.note,
             SKOS.scopeNote}

SKOSSemanticRelations = {SKOS.broader,
                         SKOS.broaderTransitive,
                         SKOS.narrower,
                         SKOS.narrowerTransitive,
                         SKOS.related}

SKOSMappingRelations = {SKOS.broadMatch,
                        SKOS.closeMatch,
                        SKOS.exactMatch,
                        SKOS.narrowMatch,
                        SKOS.relatedMatch}

SKOSSchemeRelations = {SKOS.inScheme,
                       SKOS.hasTopConcept,
                       SKOS.topConceptOf}

SKOSCollections = {SKOS.Collection,
                   SKOS.member,
                   SKOS.OrderedCollection,
                   SKOS.memberList}

SKOSPredicates = SKOSLabels.union(SKOSNotes,
                                  SKOSSemanticRelations,
                                  SKOSMappingRelations,
                                  SKOSSchemeRelations,
                                  SKOSCollections)

SKOSPredicates.add(SKOS.notation)

# =============================================================================
# Custom Exceptions
# =============================================================================

class SKOSError(Exception):
    """Serves as base class for other custom errors. Do not use directly."""
    
    def __init__(self, exampleNumber, referenceURL, triple, message=None):
        """
        SKOS errors are raised when a user tries to add a triple that would violate the SKOS standard.

        Parameters
        ----------
        triple : 3-tuple, optional
            The triple the user attempted to add to masterGraph. The default is None.
        exampleNumber : str, optional
            The error number corresponds to the example number in the SKOS reference. The default is None.
        referenceURL : str, optional
            The URL of the SKOS refrence section which describes the violation that threw the exception. The default is None.

        Returns
        -------
        None.

        """
        self.err = exampleNumber
        
        self.ref = referenceURL
        
        self.tpl = triple
        
        self.msg = "Triple {} violates example {} from {}.".format(self.tpl, self.err, self.ref)
        
        if message != None:
            self.msg = ' '.join([self.msg, message])
        
        super().__init__(self.msg)

class ConflictingLabelError(SKOSError):
    """It is an error if a concept has the same literal both as its preferred
    label and as an alternative label or hidden label.
    Source: https://www.w3.org/TR/skos-primer/#seclabel"""
    def __init__(self, triple):
        
        SKOSError.__init__(self,
                           "S13",
                           "https://www.w3.org/TR/skos-reference/#L1567",
                           triple,
                           "A concept cannot have the same plain literal for two or more different label types.")

class DisjointMatchError(SKOSError):
    """By convention, mapping relationships are expected to be asserted between
    concepts that belong to different concept schemes.
    Source: https://www.w3.org/TR/skos-primer/#secmapping"""
    def __init__(self, triple):
        
        SKOSError.__init__(self,
                           "S46",
                           "https://www.w3.org/TR/skos-reference/#L5429",
                           triple,
                           "skos:exactMatch is disjoint with skos:broadMatch, skos:narrowMatch, and skos:relatedMatch.")

class DisjointRelationError(SKOSError):
    """The transitive closure of skos:broader is disjoint from skos:related.
    If resources A and B are related via skos:related, there must not be a
    chain of skos:broader relationships from A to B. The same holds of
    skos:narrower.
    Source: https://www.w3.org/TR/skos-primer/#secassociative"""
    def __init__(self, triple):
        
        SKOSError.__init__(self,
                           "S27",
                           "https://www.w3.org/TR/skos-reference/#L2422",
                           triple,
                           "The transitive closure of skos:broader is disjoint from skos:related.")

class RedundantLabelError(SKOSError):
    """There cannot be more than one preferred label per language."""
    def __init__(self, triple):
        
        SKOSError.__init__(self,
                           "S14",
                           "https://www.w3.org/TR/skos-reference/#L1567",
                           triple,
                           "A concept cannot have more than one preferred label per language.")

class ReflexiveError(SKOSError):
    """By default, SKOS allows reflexive triples. That means a concept can be
    related to itself. This relationship is represented by a triple's subject
    and object being the same URI. If the irreflexive flag is set to True on
    method that adds a relationship, then a triple cannot have the same URI for
    the subject and object. That is, you cannot create a relationship between a
    concept and itself."""
    def __init__(self, triple):
        
        predicate = triple[1]
        
        if predicate == SKOS.related:
            SKOSError.__init__(self,
                               "E33",
                               "https://www.w3.org/TR/skos-reference/#L2376",
                               triple,
                               "If the irreflexive flag is true, then a concept cannot be related to itself.")
        elif predicate == SKOS.broader:
            SKOSError.__init__(self,
                               "E36",
                               "https://www.w3.org/TR/skos-reference/#L2449",
                               triple,
                               "If the irreflexive flag is true, then a concept cannot be broader than itself.")
        elif predicate == SKOS.narrower:
            SKOSError.__init__(self,
                               "E36",
                               "https://www.w3.org/TR/skos-reference/#L2449",
                               triple,
                               "If the irreflexive flag is true, then a concept cannot be narrower than itself.")
        elif predicate == SKOS.broaderTransitive:
            SKOSError.__init__(self,
                               "E37",
                               "https://www.w3.org/TR/skos-reference/#L2484",
                               triple,
                               "If the irreflexive flag is true, then a concept cannot be broader (transitive) than itself.")
        elif predicate == SKOS.narrowerTransitive:
            SKOSError.__init__(self,
                               "E37",
                               "https://www.w3.org/TR/skos-reference/#L2484",
                               triple,
                               "If the irreflexive flag is true, then a concept cannot be narrower (transitive) than itself.")
        elif predicate == SKOS.broadMatch:
            SKOSError.__init__(self,
                               "E66",
                               "https://www.w3.org/TR/skos-reference/#L4499",
                               triple,
                               "If the irreflexive flag is true, then a concept cannot be a broad match of itself.")
        elif predicate == SKOS.closeMatch:
            SKOSError.__init__(self,
                               "E66",
                               "https://www.w3.org/TR/skos-reference/#L4499",
                               triple,
                               "If the irreflexive flag is true, then a concept cannot be a close match of itself.")
        elif predicate == SKOS.exactMatch:
            SKOSError.__init__(self,
                               "E66",
                               "https://www.w3.org/TR/skos-reference/#L4499",
                               triple,
                               "If the irreflexive flag is true, then a concept cannot be an exact match of itself.")
        elif predicate == SKOS.narrowMatch:
            SKOSError.__init__(self,
                               "E66",
                               "https://www.w3.org/TR/skos-reference/#L4499",
                               triple,
                               "If the irreflexive flag is true, then a concept cannot be a narrow match of itself.")
        elif predicate == SKOS.relatedMatch:
            SKOSError.__init__(self,
                               "E66",
                               "https://www.w3.org/TR/skos-reference/#L4499",
                               triple,
                               "If the irreflexive flag is true, then a concept cannot be a related match of itself.")
        else:
            SKOSError.__init__(self,
                               "N/A",
                               "https://www.w3.org/TR/skos-reference/",
                               triple,
                               "If the irreflexive flag is true, then a concept cannot a subject and object with predicate, {}.".format(predicate))

class InvalidPredicateError(SKOSError):
    """Thrown when the wrong predicate is passed to the _addRelationships
    method of a concept, which should never happen."""
    def __init__(self, triple):
        
        SKOSError.__init__(self,
                           "N/A",
                           "N/A",
                           triple)

class ImproperAssociationError(SKOSError):
    """By convention, non-mapping relationships are expected to be asserted
    between concepts that belong to the same concept schemes. But they are
    implied by mapping relationships.
    Source: https://www.w3.org/TR/skos-primer/#secmapping"""
    def __init__(self, triple):
        
        SKOSError.__init__(self,
                           "N/A",
                           "https://www.w3.org/TR/skos-primer/#secmapping",
                           triple)

class ImproperMappingError(SKOSError):
    """By convention, mapping relationships are expected to be asserted between
    concepts that belong to different concept schemes.
    Source: https://www.w3.org/TR/skos-primer/#secmapping"""
    def __init__(self, triple):
        
        SKOSError.__init__(self,
                           "N/A",
                           "https://www.w3.org/TR/skos-primer/#secmapping",
                           triple)

class SchemeConceptError(SKOSError):
    """Right now this is only thrown when the integrity condition in section
    4.4 of the SKOS reference is violated:
    https://www.w3.org/TR/skos-reference/#L1228"""
    def __init__(self, triple):
        
        SKOSError.__init__(self,
                           "S9",
                           "https://www.w3.org/TR/skos-reference/#L1228",
                           triple,
                           "A concept cannot be a concept scheme, and a concept scheme cannot be a concept.")
        
class TopConceptError(SKOSError):
    """By convention, top concepts of a scheme should not have a broader
    concept in the same scheme."""
    def __init__(self, triple):
        
        SKOSError.__init__(self,
                           "E8",
                           "https://www.w3.org/TR/skos-reference/#L2446",
                           triple,
                           "By convention, top concepts of a scheme should not have a broader concept in the same scheme.")

# =============================================================================
# Helper functions (functions intended for use inside the module)
# =============================================================================

def _checkType(theObject, theType):
    """
    Checks that theObject is an instance of theType.

    Parameters
    ----------
    theObject : object
        Any Python object.
    theType : a type
        Any Python type including custom classes.

    Raises
    ------
    TypeError
        A type error is raised if theObject is not an instance of theType.

    Returns
    -------
    None.

    """
    if not isinstance(theObject, theType):
        raise TypeError
        
    return True

def _cleanUpPlainLiteral(literal, lang):
    """
    An internal function used to convert strings to RDF plain literals
    (strings with language tags) and correct language tags of plain literals.

    Parameters
    ----------
    literal : str or PlainLiteral
        The string or plain literal that will be converted into a plain
        literal. If a plain literal with language == None is passed and lang
        is not None, then a new plain literal will be created with language =
        lang.
    lang : str
        The language tag of the plain literal (examples: 'en', 'fr').

    Returns
    -------
    newLiteral : PlainLiteral
        A plain literal with the string matching the input variable literal
        and language of input variable lang (if not already defined).

    """
    if isinstance(literal, str):
        newLiteral = PlainLiteral(literal, lang)
    elif isinstance(literal, rdflib.term.Literal) or isinstance(literal, PlainLiteral):
        if literal.language == None and lang != None:
            newLiteral = PlainLiteral(str(literal), lang)
        else:
            newLiteral = PlainLiteral(str(literal), literal.language)
    else:
        raise TypeError
        
    return newLiteral

def easyURI(thing):
    """
    Return a URI given a SKOSSubject, URIRef, or string.

    Parameters
    ----------
    thing : SKOSSubject, URIRef, or string
        The Python variable from which a URI must be obtained.

    Raises
    ------
    ValueError
        If the type of thing is not a SKOSSubject, URIRef, or string.

    Returns
    -------
    thingURI : redflib.term.URIRef
        The URI reference obtained from thing.

    """
    if isinstance(thing, SKOSSubject):
        thingURI = thing.uri
    elif isinstance(thing, rdflib.term.URIRef):
        thingURI = thing
    elif isinstance(thing, str):
        thingURI = rdflib.term.URIRef(thing)
    else:
        raise ValueError
    
    return thingURI

# =============================================================================
# Class definitions
# =============================================================================

class SKOSGraph(rdflib.graph.Graph):
    """An RDF graph with the SKOS namespace bound to skos."""
    
    def __init__(self, store="default", identifier=None, namespace_manager=None, base=None):
        
        super(SKOSGraph, self).__init__(store, identifier, namespace_manager, base)
        
        self.bind('skos', SKOS, override=False)
        
        logger.debug("Graph with identifier {} was created.".format(self.identifier))

# =============================================================================
# Define the masterGraph. The masterGraph will store all of the triples of all
# of the SKOSSubject python objects. Whoof, that was a hard sentence to write.
# =============================================================================

masterGraph = SKOSGraph(identifier='master')

# =============================================================================
# More class definitions
# =============================================================================

class PlainLiteral(rdflib.term.Literal):
    """A plain literal is a string combined with an optional language tag.
    Source: https://www.w3.org/TR/rdf-concepts/#section-Literals"""
    
    def __new__(cls, lexical, lang=None, normalize=None):
        
        _checkType(lexical, str)
        
        return super().__new__(cls, lexical, lang, None, normalize)

class SKOSSubject(object):
    
    def __init__(self, URI):
        
        global masterGraph
        
        self.graph = masterGraph
        
        if isinstance(URI, rdflib.URIRef):
            self.uri = URI
        else:
            self.uri = rdflib.URIRef(URI)
        
    def __str__(self):
        return str(self.uri)
    
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.uri)
    
    def _addTriple(self, triple):
        """
        Adds a triple to the graph where the concept is stored.

        Parameters
        ----------
        triple : 3-tuple
            An RDF triple expressed as a Python tuple of length 3.

        Returns
        -------
        triple : 3-tuple
            The triple passed to the function.

        """
        self.graph.add(triple)
        
        logger.debug("Triple, {}, added to graph, {}.".format(triple, self.graph.identifier))
        
        return triple
    
    def _easyTriple(self, SKOSobject, predicate):
        """
        A private function that gets a URI from the argument added to the 

        Parameters
        ----------
        SKOSobject : Concept, ConceptScheme, rdflib.term.URIref, str
            The concept or concept scheme that is the object of the triple that is returned.
        predicate : rdflib.term.URIref
            The predicate of the triple that is returned.

        Returns
        -------
        URI : rdflib.term.URIref
            The URI of the object of the triple that is returned.
        triple : 3-tuple
            A length three tuple of URIs. The subject is self.uri; the predicate is passed to this function; and the object is the URI of the passed object.

        """
        URI = easyURI(SKOSobject)
        
        triple = (self.uri, predicate, URI)
        
        return URI, triple
    
    def getAllTriples(self):
        """
        Returns all triples where the SKOS subject is the subject or object of the triple. In other words, the method returns all triples about this SKOS object.

        Returns
        -------
        outputSet : set
            A set of all triples concerning self.uri.

        """

        outputSet = set( self.graph.triples( (self.uri, None, None) ) )
            
        outputSet = outputSet.union( set( self.graph.triples( (None, None, self.uri) ) ) )
            
        return outputSet
        
    def updateURI(self, newURI):
        """
        Changes the URI of the SKOS subject to match the new URI passed to the method.

        Parameters
        ----------
        newURI : SKOSSubject, URIRef, or string
            The new URI that will replace the subject's current URI.

        Returns
        -------
        updatedURI : URIRef
            The URIRef object created from newURI.

        """
        updatedURI = easyURI(newURI)
        
        allTriples = self.getAllTriples()
        
        for triple in allTriples:
            subject = triple[0]
            predicate = triple[1]
            RDFobject = triple[2]
            if subject == self.uri:
                subject = updatedURI
            if RDFobject == self.uri:
                RDFobject = updatedURI
            newTriple = (subject, predicate, RDFobject)
            self.graph.remove(triple)
            self.graph.add(newTriple)
            
        self.uri = updatedURI
        
        return updatedURI

class Concept(SKOSSubject):
    """Implements a SKOS concept.
    
    Note: Since SKOS, RDF, and Python use the words object the following class
    description will use OBJECT to mean Python OBJECT and object to mean SKOS
    or RDF object.
    
    The self.uri attribute of a Concept (Python class) OBJECT is the URI of the
    SKOS concept. Concept attributes (self.broader, self.narrower,
    self.prefLabel, etc.) represent SKOS predicates. Each attribute stores
    Python OBJECTS that are either Literals, URIRefs, or other Concepts. These
    OBJECTS represent the objects of a SKOS triple where the subject is
    self.uri and the predicate is the name of the attribute (with the SKOS
    namespace prefix).
    
    For example, OBJECT.prefLabel = [Literal('concept's name')] is the Python
    way of describing the triple, (URI, skos:prefLabel, 'concept's name').
    
    Predicates support more than one object in relation to the subject, so
    the OBJECTS are stored in a set."""
    
    def __init__(self, URI):
        
        SKOSSubject.__init__(self, URI)
        
        triple = (self.uri, RDF.type, SKOS.Concept)
        
        notAConceptScheme = (self.uri, RDF.type, SKOS.ConceptScheme) not in self.graph
        
        notACollection = (self.uri, RDF.type, SKOS.Collection) not in self.graph
        
        if notAConceptScheme and notACollection:
            self._addTriple( triple )
        else:
            raise SchemeConceptError(triple)

    def _addLabel(self, predicate, literal, lang):
        """
        Converts the literal variable into a PlainLiteral, checks if the literal has been used in another label already, and then adds a triple to the concept's graph representing the label.

        Parameters
        ----------
        predicate : rdflib.term.URIref
            The predicate of the triple used to add the label. It should be a SKOS label property.
        literal : PlainLiteral, rdflib.term.Literal, or str
            A plain literal (https://www.w3.org/TR/rdf-concepts/#dfn-plain-literal) used for the label.
        lang : str
            The language code (https://datatracker.ietf.org/doc/html/rfc3066) used for the label. Can be None.

        Returns
        -------
        triple : 3-tuple
            The triple that represents the label that was added.

        """
        newLiteral = _cleanUpPlainLiteral(literal, lang)
        
        triple = (self.uri, predicate, newLiteral)
        
        for label in SKOSLabels:
            for RDFObject in self.graph.objects(self.uri, label):
                if RDFObject == newLiteral:
                    #A literal cannot be the object of more than one label predicate. In other words, you can't have the same string as hidden label and an alternate label.
                    raise ConflictingLabelError(triple)
        
        return self._addTriple(triple)
    
    def _addRelationship(self, triple, inverse):
        """
        A function for adding SKOS relationships between concepts.

        Parameters
        ----------
        triple : 3-tuple
            The triple where self.uri is the subject
        inverse : 3-tuple
            The inverse of triple, where self.uri is the object. For unidirectional relationships, the inverse should be set to None.

        Returns
        -------
        triple : 3-tuple
            The triple where self.uri is the subject. The same triple that was passed to the method.
        """          
        self._addTriple(triple)
        
        if inverse != None:
            self._addTriple(inverse)
        
        return triple
    
    def _getObjects(self, predicate):
        """
        Private function for simplifying other 'get' functions.

        Parameters
        ----------
        predicate : rdflib.term.URIref
            A skos property.

        Returns
        -------
        A generator of objects.

        """
        return self.graph.objects(self.uri, predicate)
    
    def _testReflexive(self, triple, raiseException):
        """Private function to check for reflexive statements."""
        if (triple[0] == triple[2]):
            if raiseException:
                #Preventing self-reference is a personal choice, not part of the SKOS model.
                raise ReflexiveError(triple)
            else:
                logger.warning("Reflexive triple added: {}".format(triple))
                
    def _testSameScheme(self, concept):
        """
        Private function to test if this concept is in the same scheme as the passed concept.

        Parameters
        ----------
        concept : Concept
            Concept that is being related to this concept.

        Returns
        -------
        inSameScheme : bool
            True if concepts share one scheme. False if concepts share no schemes.

        """
        selfSchemes = set( self.getConceptSchemes() )
        
        conceptSchemes = set( concept.getConceptSchemes() )
        
        inSameScheme = not selfSchemes.isdisjoint(conceptSchemes)
        
        return inSameScheme

    def addAltLabel(self, literal, lang=None):
        """
        Adds an alternate label for the concept.

        Parameters
        ----------
        literal : PlainLiteral, rdflib.term.Literal, or str
            A plain literal (https://www.w3.org/TR/rdf-concepts/#dfn-plain-literal) used for the label.
        lang : str, optional
            The language code (https://datatracker.ietf.org/doc/html/rfc3066) used for the label. The default is None.

        Returns
        -------
        triple : 3-tuple
            The triple that represents the label.
        """
        return self._addLabel(SKOS.altLabel, literal, lang)
        
    def addBroader(self, concept, irreflexive=False):
        """
        Add a skos:broader relationship between the concept supplied to the method (the broader concept) and the concept from which the method is called (the narrower concept). The concepts must be in the same concept scheme.

        Parameters
        ----------
        concept : Concept, rdflib.term.URIref, str
            The broader concept.
        irreflexive : bool, optional
            Setting this variable to True prevents self-reference. The default is False.

        Returns
        -------
        triple : 3-tuple
            The triple created by this method.
        """
        conceptURI, triple = self._easyTriple(concept, SKOS.broader)
                
        self._testReflexive(triple, irreflexive)
                          
        inSameScheme = self._testSameScheme(concept)
        
        if inSameScheme == False:
            raise ImproperAssociationError(triple)
            
        if (self.uri, SKOS.related, conceptURI) in self.graph or \
            (conceptURI, SKOS.related, self.uri) in self.graph:
            raise DisjointRelationError(triple)
            
        self._addRelationship(triple, (conceptURI, SKOS.narrower, self.uri) )
        
        return triple
    
    def addBroaderTransitive(self, concept, irreflexive=False):
        #TODO: implement this
        #I made the temporary decision not to implement skos:broaderTransitive because it was complicated and possibly unnecessary for the application I planned to use this code for. https://www.w3.org/TR/skos-primer/#sectransitivebroader
        #"Note especially that, by convention, skos:broader and skos:narrower are only used to assert immediate (i.e., direct) hierarchical links between two SKOS concepts. By convention, skos:broaderTransitive and skos:narrowerTransitive are not used to make assertions, but are instead used only to draw inferences." Source: https://www.w3.org/TR/skos-reference/#example-35
        #Based on the above comment, I should make asserting the transitive hierarchical triples optional to the user (since they are technically redundant)
        raise NotImplementedError
        
    def addBroadMatch(self, concept):
        """
        Add a skos:broadMatch relationship between the concept supplied to the method (the broader concept) and the concept from which the method is called (the narrower concept). The concepts must be in different concept schemes.

        Parameters
        ----------
        concept : Concept, rdflib.term.URIref, str
            The broader concept.

        Returns
        -------
        triple : 3-tuple
            The triple created by this method.
        """
        conceptURI, triple = self._easyTriple(concept, SKOS.broadMatch)
                
        self._testReflexive(triple, True)
                          
        inSameScheme = self._testSameScheme(concept)
        
        if inSameScheme == True:
            raise ImproperMappingError(triple)
            
        if (self.uri, SKOS.relatedMatch, conceptURI) in self.graph or \
            (conceptURI, SKOS.relatedMatch, self.uri) in self.graph:
            raise DisjointRelationError(triple)
            
        if (self.uri, SKOS.exactMatch, conceptURI) in self.graph or \
            (conceptURI, SKOS.exactMatch, self.uri) in self.graph:
            raise DisjointMatchError(triple)
            
        self._addRelationship(triple, (conceptURI, SKOS.narrowMatch, self.uri) )
            
        return triple
        
    def addChangeNote(self, note, lang=None):
        """
        Adds a change note triple. Change notes typically are, but do not have to be, plain literals. They can also be blank nodes or URIs of other documents. Source: https://www.w3.org/TR/skos-primer/#secadvanceddocumentation

        Parameters
        ----------
        note : PlainLiteral, rdflib.term.Literal, str, rdflib.term.URIRef, rdflib.term.BNode
            The change note to be added to this concept.
        lang : str, optional
            The language code (https://datatracker.ietf.org/doc/html/rfc3066) used for the change note. Default is None.

        Returns
        -------
        newNote : PlainLiteral
            If note was a string or literal, then newNote is the PlainLiteral created from note & lang. If note was a blank node or URI reference, then newNote is note.

        """
        return self.addNote(note, lang, SKOS.changeNote)
        
    def addCloseMatch(self, concept):
        """
        Add a skos:closeMatch relationship between the concept supplied to the method and the concept from which the method is called. The concepts must be in different concept schemes.

        Parameters
        ----------
        concept : Concept, rdflib.term.URIref, str
            The concept which is a close match.

        Returns
        -------
        triple : 3-tuple
            The triple created by this method.
        """
        conceptURI, triple = self._easyTriple(concept, SKOS.closeMatch)
                
        self._testReflexive(triple, True)
                          
        inSameScheme = self._testSameScheme(concept)
        
        if inSameScheme == True:
            raise ImproperMappingError(triple)
            
        self._addRelationship(triple, (conceptURI, SKOS.closeMatch, self.uri) )
            
        return triple
    
    def addDefinition(self, note, lang=None):
        """
        Adds a definition triple. Definitions typically are, but do not have to be, plain literals. They can also be blank nodes or URIs of other documents. Source: https://www.w3.org/TR/skos-primer/#secadvanceddocumentation

        Parameters
        ----------
        note : PlainLiteral, rdflib.term.Literal, str, rdflib.term.URIRef, rdflib.term.BNode
            The definition to be added to this concept.
        lang : str, optional
            The language code (https://datatracker.ietf.org/doc/html/rfc3066) used for the definition. Default is None.

        Returns
        -------
        newNote : PlainLiteral
            If note was a string or literal, then newNote is the PlainLiteral created from note & lang. If note was a blank node or URI reference, then newNote is note.

        """
        return self.addNote(note, lang, SKOS.definition)
    
    def addEditorialNote(self, note, lang=None):
        """
        Adds an editorial note triple. Editorial notes typically are, but do not have to be, plain literals. They can also be blank nodes or URIs of other documents. Source: https://www.w3.org/TR/skos-primer/#secadvanceddocumentation

        Parameters
        ----------
        note : PlainLiteral, rdflib.term.Literal, str, rdflib.term.URIRef, rdflib.term.BNode
            The editorial note to be added to this concept.
        lang : str, optional
            The language code (https://datatracker.ietf.org/doc/html/rfc3066) used for the editorial note. Default is None.

        Returns
        -------
        newNote : PlainLiteral
            If note was a string or literal, then newNote is the PlainLiteral created from note & lang. If note was a blank node or URI reference, then newNote is note.

        """
        return self.addNote(note, lang, SKOS.editorialNote)
        
    def addExactMatch(self, concept):
        """
        Add a skos:exactMatch relationship between the concept supplied to the method and the concept from which the method is called. The concepts must be in different concept schemes.

        Parameters
        ----------
        concept : Concept, rdflib.term.URIref, str
            The concept which is an exact match.

        Returns
        -------
        triple : 3-tuple
            The triple created by this method.
        """
        #"The property skos:exactMatch is used to link two concepts, indicating a high degree of confidence that the concepts can be used interchangeably across a wide range of information retrieval applications. skos:exactMatch is a transitive property, and is a sub-property of skos:closeMatch." from https://www.w3.org/TR/skos-reference/#mapping
        conceptURI, triple = self._easyTriple(concept, SKOS.exactMatch)
                
        self._testReflexive(triple, True)
                          
        inSameScheme = self._testSameScheme(concept)
        
        if inSameScheme == True:
            raise ImproperMappingError(triple)
        
        BMset = set( self.getBroadMatches() )
        
        NMset = set( self.getNarrowMatches() )
        
        RMset = set( self.getRelatedMatches() )
        
        if conceptURI in BMset.union(NMset, RMset):
            raise DisjointMatchError(triple)
        
        self._addRelationship(triple, (conceptURI, SKOS.exactMatch, self.uri) )
        
        self.addCloseMatch(concept)
        
        #TODO: Clean this code up. It is messy for two reasons:
        # 1) I am trying to add duplicate triples (the graph object should ignore these; it works like a set).
        # 2) I am ignoring the possibility of in-scheme relationships here, but elsewhere in the code I am preventing them.
        # This is the only transitive property I have tried to implement, so if I find a good way to do it, then I should try implementing broaderTransitive and narrowerTransitive as well.
        for match in self.graph.objects(conceptURI, SKOS.exactMatch):
            if match != self.uri and match != conceptURI:
                self._addTriple( (self.uri, SKOS.exactMatch, match) )
                self._addTriple( (self.uri, SKOS.closeMatch, match) )
        for match in self.graph.objects(self.uri, SKOS.exactMatch):
            if match != self.uri and match != conceptURI:
                self._addTriple( (conceptURI, SKOS.exactMatch, match) )
                self._addTriple( (conceptURI, SKOS.closeMatch, match) )

        return triple
    
    def addExample(self, note, lang=None):
        """
        Adds an example triple. Examples typically are, but do not have to be, plain literals. They can also be blank nodes or URIs of other documents. Source: https://www.w3.org/TR/skos-primer/#secadvanceddocumentation

        Parameters
        ----------
        note : PlainLiteral, rdflib.term.Literal, str, rdflib.term.URIRef, rdflib.term.BNode
            The example to be added to this concept.
        lang : str, optional
            The language code (https://datatracker.ietf.org/doc/html/rfc3066) used for the example. Default is None.

        Returns
        -------
        newNote : PlainLiteral
            If note was a string or literal, then newNote is the PlainLiteral created from note & lang. If note was a blank node or URI reference, then newNote is note.

        """
        return self.addNote(note, lang, SKOS.example)

    def addHiddenLabel(self, literal, lang=None):
        """
        Adds a hidden label for the concept.

        Parameters
        ----------
        literal : PlainLiteral, rdflib.term.Literal, or str
            A plain literal (https://www.w3.org/TR/rdf-concepts/#dfn-plain-literal) used for the label.
        lang : str, optional
            The language code (https://datatracker.ietf.org/doc/html/rfc3066) used for the label. The default is None.

        Returns
        -------
        triple : 3-tuple
            The triple that represents the label.

        """
        return self._addLabel(SKOS.hiddenLabel, literal, lang)
        
    def addHistoryNote(self, note, lang=None):
        """
        Adds an history note triple. History notes typically are, but do not have to be, plain literals. They can also be blank nodes or URIs of other documents. Source: https://www.w3.org/TR/skos-primer/#secadvanceddocumentation

        Parameters
        ----------
        note : PlainLiteral, rdflib.term.Literal, str, rdflib.term.URIRef, rdflib.term.BNode
            The history note to be added to this concept.
        lang : str, optional
            The language code (https://datatracker.ietf.org/doc/html/rfc3066) used for the history note. Default is None.

        Returns
        -------
        newNote : PlainLiteral
            If note was a string or literal, then newNote is the PlainLiteral created from note & lang. If note was a blank node or URI reference, then newNote is note.

        """
        return self.addNote(note, lang, SKOS.historyNote)
        
    def addNarrower(self, concept, irreflexive=False):
        """
        Add a skos:narrower relationship between the concept supplied to the method (the narrower concept) and the concept from which the method is called (the broader concept). The concepts must be in the same concept scheme.

        Parameters
        ----------
        concept : Concept, rdflib.term.URIref, str
            The narrower concept.
        irreflexive : bool, optional
            Setting this variable to True prevents self-reference. The default is False.

        Returns
        -------
        triple : 3-tuple
            The triple created by this method.
        """
        conceptURI, triple = self._easyTriple(concept, SKOS.narrower)
                
        self._testReflexive(triple, irreflexive)
                          
        inSameScheme = self._testSameScheme(concept)
        
        if inSameScheme == False:
            raise ImproperAssociationError(triple)
            
        if (self.uri, SKOS.related, conceptURI) in self.graph or \
            (conceptURI, SKOS.related, self.uri) in self.graph:
            raise DisjointRelationError(triple)
            
        self._addRelationship(triple, (conceptURI, SKOS.broader, self.uri) )
        
        return triple
    
    def addNarrowerTransitive(self, concept, irreflexive=False):
        #TODO: implement this
        #I made the temporary decision not to implement skos:narrowerTransitive because it was complicated and possibly unnecessary for the application I planned to use this code for. https://www.w3.org/TR/skos-primer/#sectransitivebroader
        #"Note especially that, by convention, skos:broader and skos:narrower are only used to assert immediate (i.e., direct) hierarchical links between two SKOS concepts. By convention, skos:broaderTransitive and skos:narrowerTransitive are not used to make assertions, but are instead used only to draw inferences." Source: https://www.w3.org/TR/skos-reference/#example-35
        raise NotImplementedError
        
    def addNarrowMatch(self, concept):
        #TODO: Left off the _addRelationships split here.
        """
        Add a skos:narrowMatch relationship between the concept supplied to the method (the narrower concept) and the concept from which the method is called (the broader concept). The concepts must be in different concept schemes.

        Parameters
        ----------
        concept : Concept, rdflib.term.URIref, str
            The narrower concept.

        Returns
        -------
        triple : 3-tuple
            The triple created by this method.
        """
        conceptURI, triple = self._easyTriple(concept, SKOS.narrowMatch)
                
        self._testReflexive(triple, True)
                          
        inSameScheme = self._testSameScheme(concept)
        
        if inSameScheme == True:
            raise ImproperMappingError(triple)
            
        self._addRelationship(triple, (conceptURI, SKOS.broadMatch, self.uri) )
            
        return triple
    
    def addNotation(self, notation):    
        #TODO: Add support for SKOS.notation https://www.w3.org/TR/skos-reference/#L2064
        raise NotImplementedError
    
    def addNote(self, note, lang, predicate=SKOS.note):
        """
        Adds a note triple. Notes typically are, but do not have to be, plain literals. They can also be blank nodes or URIs of other documents. Source: https://www.w3.org/TR/skos-primer/#secadvanceddocumentation

        Parameters
        ----------
        note : PlainLiteral, rdflib.term.Literal, str, rdflib.term.URIRef, rdflib.term.BNode
            The documentation note to be added to this concept.
        lang : str
            The language code (https://datatracker.ietf.org/doc/html/rfc3066) used for the note. Can be None.
        predicate : rdflib.term.URIref
            A note predicate from the SKOS standard (https://www.w3.org/TR/skos-primer/#secdocumentation). In other words, A member of the SKOSNotes list.

        Returns
        -------
        newNote : PlainLiteral
            If note was a string or literal, then newNote is the PlainLiteral created from note & lang. If note was a blank node or URI reference, then newNote is note.

        """
        if isinstance(note, str) or isinstance(note, rdflib.term.Literal):
            newNote = _cleanUpPlainLiteral(note, lang)
        elif isinstance(note, rdflib.term.BNode) or isinstance(note, rdflib.term.URIRef):
            newNote = note
        else:
            newNote = PlainLiteral(str(note), lang)

        if predicate in SKOSNotes:
            self._addTriple( (self.uri, predicate, newNote) )
        else:
            self._addTriple( (self.uri, SKOS.note, newNote) )
            logger.warning("Inappropriate predicate used on a note: {}".format(predicate))
        
        return newNote
    
    def addPrefLabel(self, literal, lang=None, replace=False):
        """
        Adds a preferred label for the concept.

        Parameters
        ----------
        literal : PlainLiteral, rdflib.term.Literal, or str
            A plain literal (https://www.w3.org/TR/rdf-concepts/#dfn-plain-literal) used for the label.
        lang : str, optional
            The language code (https://datatracker.ietf.org/doc/html/rfc3066) used for the label. The default is None.
        replace : bool, optional
            If set to true, any conflicting preferred label will be replaced. The default is False.

        Returns
        -------
        triple : 3-tuple
            The triple that represents the label.

        """
        for pl in self.graph.objects(self.uri, SKOS.prefLabel):
            # pl stands for plain literal
            if pl.language == lang:
                t = (self.uri, SKOS.prefLabel, pl)
                if replace == False:
                    raise RedundantLabelError(t)
                else:
                    self.graph.remove(t)
        
        return self._addLabel(SKOS.prefLabel, literal, lang)
        
    def addRelated(self, concept, irreflexive=False):
        """
        Add a skos:related relationship between the concept supplied to the method and the concept from which the method is called. The concepts must be in the same concept scheme.

        Parameters
        ----------
        concept : Concept, rdflib.term.URIref, str
            The related concept.
        irreflexive : bool, optional
            Setting this variable to True prevents self-reference. The default is False.

        Returns
        -------
        triple : 3-tuple
            The triple created by this method.
        """
        conceptURI, triple = self._easyTriple(concept, SKOS.related)
                
        self._testReflexive(triple, True)
                          
        inSameScheme = self._testSameScheme(concept)
        
        if inSameScheme == False:
            raise ImproperMappingError(triple)
            
        self._addRelationship(triple, (conceptURI, SKOS.related, self.uri) )
            
        return triple
        
    def addRelatedMatch(self, concept):
        """
        Add a skos:relatedMatch relationship between the concept supplied to the method and the concept from which the method is called. The concepts must be in different concept schemes.

        Parameters
        ----------
        concept : Concept, rdflib.term.URIref, str
            The related concept.

        Returns
        -------
        triple : 3-tuple
            The triple created by this method.
        """
        conceptURI, triple = self._easyTriple(concept, SKOS.relatedMatch)
                
        self._testReflexive(triple, True)
                          
        inSameScheme = self._testSameScheme(concept)
        
        if inSameScheme == True:
            raise ImproperMappingError(triple)
            
        self._addRelationship(triple, (conceptURI, SKOS.relatedMatch, self.uri) )
            
        return triple
        
    def addScopeNote(self, note, lang=None):
        """
        Adds a scope note triple. Scope notes typically are, but do not have to be, plain literals. They can also be blank nodes or URIs of other documents. Source: https://www.w3.org/TR/skos-primer/#secadvanceddocumentation

        Parameters
        ----------
        note : PlainLiteral, rdflib.term.Literal, str, rdflib.term.URIRef, rdflib.term.BNode
            The scope note to be added to this concept.
        lang : str, optional
            The language code (https://datatracker.ietf.org/doc/html/rfc3066) used for the scope note. Default is None.

        Returns
        -------
        newNote : PlainLiteral
            If note was a string or literal, then newNote is the PlainLiteral created from note & lang. If note was a blank node or URI reference, then newNote is note.

        """
        return self.addNote(note, lang, SKOS.scopeNote)
    
    def addToScheme(self, scheme):
        """
        Adds the concept to the passed concept scheme.

        Parameters
        ----------
        scheme : ConceptScheme
            The concept scheme to which the concept is added.

        Returns
        -------
        triple : 3-tuple
            The triple added to the graph, (self.uri, SKOS.inScheme, scheme.uri).

        """
        return scheme.addConcept(self)
    
    def getConceptSchemes(self):
        """
        Returns a generator of concept schemes that the concept is in.
        """
        return self._getObjects(SKOS.inScheme)
    
    def getBroaderConcepts(self):
        """
        Returns a generator of broader concepts.
        """
        return self._getObjects(SKOS.broader)
            
    def getBroaderTransitiveConcepts(self):
        """
        Returns a generator of broader (transitive) concepts.
        """
        return self._getObjects(SKOS.broaderTransitive)
    
    def getBroadMatches(self):
        """
        Returns a generator of broader matches.
        """
        return self._getObjects(SKOS.broadMatch)
    
    def getCloseMatches(self):
        """
        Returns a generator of close matches and exact matches.
        """
        return self._getObjects(SKOS.closeMatch)
    
    def getExactMatches(self):
        """
        Returns a generator of exact matches.
        """
        return self._getObjects(SKOS.exactMatch)
            
    def getNarrowerConcepts(self):
        """
        Returns a generator of narrower concepts.
        """
        return self._getObjects(SKOS.narrower)
    
    def getNarrowerTransitiveConcepts(self):
        """
        Returns a generator of narrower (transitive) concepts.
        """
        return self._getObjects(SKOS.narrowerTransitive)
    
    def getNarrowMatches(self):
        """
        Returns a generator of narrower matches.
        """
        return self._getObjects(SKOS.narrowMatch)
        
    def getPrefLabel(self, lang=None):
        """
        Returns the preferred label for the given language.

        Parameters
        ----------
        lang : str, optional
            The language code (https://datatracker.ietf.org/doc/html/rfc3066) used for the preferred label. Default is None.

        Returns
        -------
        label : PlainLiteral
            The preferred label for the given language.

        """
        for label in self.getPrefLabels():
            if label.language == lang:
                return label

        logger.info("No label for language, {}".format(lang))
            
        return None
    
    def getPrefLabels(self):
        """
        Returns a generator of preferred labels (one for each language tag).
        """
        return self._getObjects(SKOS.prefLabel)
    
    def getRelated(self):
        """
        Returns a generator of related concepts.
        """
        return self._getObjects(SKOS.related)
    
    def getRelatedMatches(self):
        """
        Returns a generator of related matches.
        """
        return self._getObjects(SKOS.relatedMatch)
    
    def inConceptScheme(self, scheme):
        """
        Tests if this concept is in the given scheme.

        Parameters
        ----------
        scheme : ConceptScheme, URIref, str
            The scheme in which the function looks for the concept.

        Returns
        -------
        bool
            True if the concept is in the concept scheme, false otherwise.

        """
        schemeURI = easyURI(scheme)
        
        return (self.uri, SKOS.inScheme, schemeURI) in self.graph
    
    def removeFromConceptScheme(self, scheme):
        """
        Removes the concept from a concept scheme.
        """
        schemeURI, triple = self._easyTriple(scheme, SKOS.inScheme)
        
        self.graph.remove(triple)
        
        self.graph.remove( (schemeURI, SKOS.hasConcept, self.uri) )
        
        self.graph.remove( (self.uri, SKOS.topConceptOf, schemeURI) )
        
        return triple

    def removeBroaderConcept(self, concept):
        """
        Removes a the broader-narrower relationship between the passed concept (broader) and this concept (narrower).
        """
        conceptURI, triple = self._easyTriple(concept, SKOS.broader)
        
        self.graph.remove(triple)
        
        self.graph.remove( (conceptURI, SKOS.narrower, self.uri) )
        
        return triple
            
    def removeBroaderTransitive(self):
        """
        Removes a broader concept and all broader (transitive) concepts.
        """
        #TODO: Implement this after implementing skos:narrowerTransitive
        raise NotImplementedError
    
    def removeBroadMatch(self, concept):
        """
        Removes a the broader-narrower mapping between the passed concept (broader) and this concept (narrower).
        """
        conceptURI, triple = self._easyTriple(concept, SKOS.broadMatch)
        
        self.graph.remove(triple)
        
        self.graph.remove( (conceptURI, SKOS.narrowMatch, self.uri) )
        
        return triple
    
    def removeCloseMatch(self, concept):
        """
        Removes the close and exact matches between this concept and the passed concept.
        """
        conceptURI, triple = self._easyTriple(concept, SKOS.closeMatch)
        
        self.graph.remove(triple)
        
        self.graph.remove( (conceptURI, SKOS.closeMatch, self.uri) )
        
        self.removeExactMatch(concept)
        
        return triple
    
    def removeExactMatch(self, concept):
        """
        Removes the exact matches between this concept and the passed concept.
        """
        conceptURI, triple = self._easyTriple(concept, SKOS.exactMatch)
        
        self.graph.remove(triple)

        self.graph.remove( (conceptURI, SKOS.exactMatch, self.uri) )
        
        return triple
            
    def removeNarrower(self, concept):
        """
        Removes a the broader-narrower relationship between the passed concept (narrower) and this concept (broader).
        """
        conceptURI, triple = self._easyTriple(concept, SKOS.narrower)
        
        self.graph.remove(triple)
        
        self.graph.remove( (conceptURI, SKOS.broader, self.uri) )
        
        return triple
    
    def removeNarrowerTransitive(self):
        """
        Removes a narrower concept and all narrower (transitive) concepts.
        """
        #TODO: Implement this after implementing skos:narrowerTransitive
        raise NotImplementedError
    
    def removeNarrowMatch(self, concept):
        """
        Removes a the broader-narrower relationship between the passed concept (narrower) and this concept (broader).
        """
        conceptURI, triple = self._easyTriple(concept, SKOS.narrowMatch)
        
        self.graph.remove(triple)
        
        self.graph.remove( (conceptURI, SKOS.broadMatch, self.uri) )
        
        return triple
        
    def removePrefLabel(self, language):
        """
        Removes the preferred label (for the passed language) from this concept.
        """
        for label in self.getPrefLabels():
            if label.language == language:
                triple = (self.uri, SKOS.prefLabel, label)
                self.graph.remove(triple)
                return triple
    
        logger.info("No label for language, {}".format(language))
            
        return None
    
    def removeRelated(self, concept):
        """
        Removes the related relationship between this concept and the passed concept.
        """
        conceptURI, triple = self._easyTriple(concept, SKOS.related)
        
        self.graph.remove(triple)

        self.graph.remove( (conceptURI, SKOS.related, self.uri) )
        
        return triple
    
    def removeRelatedMatch(self, concept):
        """
        Removes the related mapping between this concept and the passed concept.
        """
        conceptURI, triple = self._easyTriple(concept, SKOS.relatedMatch)
        
        self.graph.remove(triple)

        self.graph.remove( (conceptURI, SKOS.relatedMatch, self.uri) )
        
        return triple

class ConceptScheme(SKOSSubject):
    """Concepts belong to concept schemes."""

    def __init__(self, URI):
        
        SKOSSubject.__init__(self, URI)
        
        triple = (self.uri, RDF.type, SKOS.ConceptScheme)
        
        notAConcept = (self.uri, RDF.type, SKOS.Concept) not in self.graph
        
        notACollection = (self.uri, RDF.type, SKOS.Collection) not in self.graph
        
        if notAConcept and notACollection:
            self._addTriple(triple)
        else:
            raise SchemeConceptError(triple)
    
    def addConcept(self, concept):
        """
        Add a concept to the scheme.

        Parameters
        ----------
        concept : str, Concept, rdflib.term.URIRef
            The concept to be added to the concept scheme.

        Returns
        -------
        conceptURI : rdflib.term.URIRef
            The URI of the concept that is added to the scheme.

        """
        conceptURI = easyURI(concept)
        
        triple = (conceptURI, SKOS.inScheme, self.uri)
        
        self._addTriple( triple )

        return triple
    
    def addTopConcept(self, concept):
        """
        Add a top concept to the scheme.

        Parameters
        ----------
        concept : str, Concept, rdflib.term.URIRef
            The concept to be added to the concept scheme.

        Returns
        -------
        conceptURI : rdflib.term.URIRef
            The URI of the concept that is added to the scheme.

        """
        conceptURI, triple = self._easyTriple(concept, SKOS.hasTopConcept)
        
        #if concept has a broader concept in the same scheme, raise error.
        broaderConcepts = set( concept.getBroaderConcepts() )
        
        broaderTConcepts = set( concept.getBroaderTransitiveConcepts() )
        
        narrowerConcepts = set( self.graph.subjects(SKOS.narrower, conceptURI) )
        
        narrowerTConcepts = set( self.graph.subjects(SKOS.narrowerTransitive, conceptURI) )
        
        allBroaderConcepts = broaderConcepts.union(broaderTConcepts, narrowerConcepts, narrowerTConcepts)
    
        hasBroaderConcept = bool( allBroaderConcepts )
        
        inSameScheme = False
        
        for bigConcept in allBroaderConcepts:
            inSameScheme = inSameScheme or ( (bigConcept, SKOS.inScheme, self.uri) in self.graph )
                    
        if hasBroaderConcept and inSameScheme:
            raise TopConceptError(triple)

        self._addTriple(triple)
        
        self._addTriple( (conceptURI, SKOS.topConceptOf, self.uri) )
        
        self.addConcept(concept)

        return triple
        
    def getConceptsByLabel(self, label, prefLabelOnly=True):
        """
        Return a generator of subjects with any type of label that matches label. Only subjects that are in the concept scheme are returned.

        Parameters
        ----------
        label : str, PlainLiteral, rdflib.term.Literal
            The preferred label of the concept you are trying to find. The label variable is converted into a plain literal, then the new label is used to slice the graph.
        prefLabelOnly : TYPE, optional
            If set to true, then only concepts with a prefLabel that match label are returned. The default is True.

        Returns
        -------
        subjects : set
            A list of subject URIs that have skos labels that match label.

        """
        newLabel = _cleanUpPlainLiteral(label, None)
        
        subjects = set()
        
        def addSubjectsToList(p, o):
            nonlocal subjects
            nonlocal self
            for subj in self.graph.subjects(SKOS.inScheme, self.uri):
                if (subj, p, o) in self.graph:
                    subjects.add(subj)
            return None
        
        if prefLabelOnly == True:
            addSubjectsToList(SKOS.prefLabel, newLabel)
            return subjects
        else:
            for skosLabel in SKOSLabels:
                addSubjectsToList(skosLabel, newLabel)
            return subjects
        
    def getConcepts(self):
        return self.graph.subjects(SKOS.inScheme, self.uri)
        
    #TODO: Add functions that can clean concept schemes in case concept relationships are added before the concept is added to a concept scheme.
    
class Collection(SKOSSubject):
    #TODO: implement this class to match https://www.w3.org/TR/skos-primer/#seccollections 
    def __init__(self, URI=None):
        
        global masterGraph
        
        self.graph = masterGraph
        
        if isinstance(URI, rdflib.URIRef) or isinstance(URI, rdflib.BNode):
            self.uri = URI
        elif URI == None:
            self.uri = rdflib.BNode()
        else:
            self.uri = rdflib.URIRef(URI)
            
        triple = (self.uri, RDF.type, SKOS.Collection)
        
        notAConcept = (self.uri, RDF.type, SKOS.Concept) not in self.graph
        
        notAConceptScheme = (self.uri, RDF.type, SKOS.ConceptScheme) not in self.graph
        
        if notAConcept and notAConceptScheme:
            self._addTriple(triple)
        else:
            raise SchemeConceptError(triple)
    
    def addMember(self, concept):
        """
        Adds a member to the collection.

        Parameters
        ----------
        concept : Concept
            The concept that should be added to the collection.

        Returns
        -------
        triple : 3-tuple
            The triple that was added to the graph.

        """
        conceptURI, triple = self._easyTriple(concept, SKOS.member)
        
        return self._addTriple(triple)
    
    def addMembers(self, conceptList):
        """
        Adds multiple concepts to a collection.

        Parameters
        ----------
        conceptList : list
            List of concepts added to the collection.

        Returns
        -------
        memberSet : set
            Set of all triples added to the graph.

        """
        memberSet = set()
        
        for concept in conceptList:
            triple = self.addMember(concept)
            memberSet.add(triple)
            
        return memberSet
    
    def addPrefLabel(self, literal, lang=None, replace=False):
        """
        Adds a preferred label for the collection.

        Parameters
        ----------
        literal : PlainLiteral, rdflib.term.Literal, or str
            A plain literal (https://www.w3.org/TR/rdf-concepts/#dfn-plain-literal) used for the label.
        lang : str, optional
            The language code (https://datatracker.ietf.org/doc/html/rfc3066) used for the label. The default is None.
        replace : bool, optional
            If set to true, any conflicting preferred label will be replaced. The default is False.

        Returns
        -------
        triple : 3-tuple
            The triple that represents the label.

        """
        #TODO: This function is a good example of why SKOS properties should be Python objects.
        for pl in self.graph.objects(self.uri, SKOS.prefLabel):
            # pl stands for plain literal
            if pl.language == lang:
                t = (self.uri, SKOS.prefLabel, pl)
                if replace == False:
                    raise RedundantLabelError(t)
                else:
                    self.graph.remove(t)
                    
        newLiteral = _cleanUpPlainLiteral(literal, lang)
        
        triple = (self.uri, SKOS.prefLabel, newLiteral)
        
        for label in SKOSLabels:
            for RDFObject in self.graph.objects(self.uri, label):
                if RDFObject == newLiteral:
                    #A literal cannot be the object of more than one label predicate. In other words, you can't have the same string as hidden label and an alternate label.
                    raise ConflictingLabelError(triple)
        
        return self._addTriple(triple)

class OrderedCollection(Collection):
    #TODO: implement this class to match https://www.w3.org/TR/skos-primer/#seccollections
    # raise NotImplementedError
    pass

# =============================================================================
# Utility functions (functions intended for use outside the module)
# =============================================================================

def readFromFile(filepath):

    global masterGraph

    index = filepath.rfind(".")

    extension = filepath[index+1:]
    
    # fmat = rdflib.util.guess_format(filepath)

    with open(filepath, 'r') as fileObject:
        masterGraph.parse(format=extension, file=fileObject)
        # masterGraph.parse(format=fmat, file=fileObject)

    conceptSchemes = dict()

    concepts = dict()
    
    collections = dict()

#TODO: Turn the following loops into an inner function that can be called with the different classes and URIs as arguments.

    for subject in masterGraph.subjects(RDF.type, SKOS.ConceptScheme):
        key = str(subject)
        conceptSchemes[key] = ConceptScheme(subject)

    for subject in masterGraph.subjects(RDF.type, SKOS.Concept):
        key = str(subject)
        concepts[key] = Concept(subject)
        
    for subject in masterGraph.subjects(RDF.type, SKOS.Collection):
        key = str(subject)
        collections[key] = Collection(subject)

    #TODO: Finish this. It needs to check the imported graph for inconsistencies.

    return conceptSchemes, concepts, collections

#Note to self: Until I have a good reason to, I am not going to mess with advanced labels: https://www.w3.org/TR/skos-primer/#secrelationshipslabels

def writeToFile(filepath, fileFormat='ttl'):
    masterGraph.serialize(filepath, fileFormat)