import os
import json
import requests
from copy import copy
from prov.model import ProvDocument, QualifiedName, Namespace,ProvBundle,ProvElement,parse_xsd_datetime,Literal, Identifier
from provstore.document import Document
from neo4jrestclient.client import GraphDatabase, StatusException
from prov.model import ProvDocument, PROV, DEFAULT_NAMESPACES,PROV_REC_CLS
from neo4jrestclient.client import GraphDatabase, StatusException, Node, Relationship
from prov.constants import PROV_N_MAP,PROV_RECORD_IDS_MAP,PROV_ATTRIBUTES_ID_MAP,PROV_ATTRIBUTES,PROV_MEMBERSHIP,PROV_ATTR_ENTITY,PROV_ATTRIBUTE_QNAMES,PROV_ATTR_COLLECTION,XSD_ANYURI,PROV_QUALIFIEDNAME
from provstore.prov_to_graph import prov_to_graph_flattern
from provstore.connectors.connector import  *

import logging


DOC_PROPERTY_NAME_ID = "document:id"
DOC_PROPERTY_NAME_LABEL = "document:label"
DOC_PROPERTY_NAME_BUNDLES = "document:bundles"
DOC_PROPERTY_NAME_NAMESPACE_URI = "namespace:uri"
DOC_PROPERTY_NAME_NAMESPACE_PREFIX = "namespace:prefix"

DOC_PROPERTY_MAP = [DOC_PROPERTY_NAME_ID,
                    DOC_PROPERTY_NAME_BUNDLES,
                    DOC_PROPERTY_NAME_NAMESPACE_URI,
                    DOC_PROPERTY_NAME_NAMESPACE_PREFIX,
                    DOC_PROPERTY_NAME_LABEL]

DOC_GET_DOC_BY_ID = "MATCH (d)-[r]-(x) WHERE (d.`document:id`)=%i RETURN d, r, x"
DOC_DELETE_BY_ID = "MATCH (d) WHERE (d.`document:id`)=%i DETACH DELETE d"

BUNDLE_LABEL_NAME= "prov:Bundle"
BUNDLE_RELATION_NAME = "includeIn"

logger = logging.getLogger(__name__)

from neo4j_serializer import Neo4jRestSerializer
from neo4j_deserializer import Neo4JRestDeserializer

class Neo4J(Connector):
    _base_url = None
    _user_name = None
    _user_password = None
    _connection = None


    def __init__(self):
        pass

    def connect(self, base_url=None, username=None, user_password=None):
        if base_url is None:
            raise InvalidCredentialsException("Please specify a base_url to connect to the database")
        else:
            self._base_url = base_url.rstrip('/')

        self._user_name = username
        self._user_password = user_password

        if not self._user_name:
            self._user_name = os.environ.get('NEO4J_USERNAME', None)
        if not self._user_password:
            self._user_password= os.environ.get('NEO4J_PASSWORD', None)

        if self._user_name is not None and self._user_password is not None:
            auth = {
                "username": self._user_name,
                "password": self._user_password
            }

        try:
            self._connection = GraphDatabase(self._base_url, **auth)
        except StatusException as e:
            if e.value == 401:  ##'Authorization Required'
                raise InvalidCredentialsException()
            else:
                raise e




    def get_document(self,document_id,prov_format):
        results = self._connection.query(q=DOC_GET_DOC_BY_ID % document_id, returns=(Node, Relationship,Node))
        prov_document = ProvDocument()
        all_records= {}
        deserializer = Neo4JRestDeserializer()
        for db_from_node, db_relation, db_to_node in results:
            deserializer.add_namespace(db_from_node,prov_document)
            deserializer.add_namespace(db_to_node,prov_document)

            all_keys = all_records.keys()
            #Add records
            if db_from_node.id not in all_keys:
                all_records.update({int(db_from_node.id): deserializer.create_record(prov_document,db_from_node)})
            if db_to_node.id not in all_keys:
                all_records.update({int(db_to_node.id): deserializer.create_record(prov_document, db_to_node)})
            #Add relations
            if db_relation.id not in all_keys:
                all_records.update({int(db_relation.id): deserializer.create_relation(prov_document, db_relation)})


        if prov_format is ProvDocument:
            return prov_document
        else:
            raise NotImplementedException("Neo4j connector only supports ProvDocument format for the get_document operation")
    def post_document(self, prov_document,name=None):
        # creates a database entry from a prov-n document
        # returns the saved neo4J doc
        #
        if len(name) == 0:
            raise InvalidDataException("Please provide a name for the document")
        gdb = self._connection

        # create graph from prov doc
        g = prov_to_graph_flattern(prov_document)

        # store all database nodes in dict
        db_nodes = {}
        serializer = Neo4jRestSerializer(self._connection)
        nodes = g.nodes()
        if len(nodes) is 0:
            nodes = prov_document.get_records()
        # Create nodes / for prov
        for node in nodes:
            db_nodes[node] = serializer.create_node(node)
        # Create nodes for bundles
        for bundle in prov_document.bundles:
            db_nodes[bundle.identifier] = serializer.create_node(bundle)

        if len(nodes) is not 0:
            #document node
            doc_node = db_nodes.values()[0]
        else:
            raise InvalidDataException("Please provide a document with at least one node")

        # Begin transaction for relations
        with gdb.transaction() as tx:
            # Create relations between nodes
            for from_node, to_node, relations in g.edges_iter(data=True):

                # interate over relations (usually only one item)
                for key, relation in relations.iteritems():
                    serializer.create_relation(db_nodes,from_node,to_node,relation)

            #Create relation to the bundle node
            for bundle in prov_document.bundles:
                for record in bundle.get_records(ProvElement):
                    serializer.create_bundle_relation(db_nodes, record, bundle)


        #Add meta data to each node
        for graph_node,db_node in db_nodes.iteritems():
            if type(graph_node) is QualifiedName:
                serializer.add_meta_data_to_node(db_node,graph_node,doc_node.id)
            elif isinstance(graph_node,ProvElement):
                serializer.add_meta_data_to_node(db_node,graph_node.identifier,doc_node.id)
            else:
                raise InvalidDataException("unknown type: %s" %type(graph_node))

        return doc_node.id

    def delete_doc(self,document_id):
        self._connection.query(q=DOC_DELETE_BY_ID % document_id)
        return True

    def add_bundle(self, document_id, bundle_document, identifier):
        bundle_doc_id = self.post_document(bundle_document, identifier)

        #Set bundle ids to document
        doc = self._connection.nodes.get(document_id)
        bundles_ids = doc.get(DOC_PROPERTY_NAME_BUNDLES, list())
        bundles_ids.append(bundle_doc_id)
        doc.set(DOC_PROPERTY_NAME_BUNDLES, bundles_ids)

        #create Linking Across Provenance Bundles
        #https://www.w3.org/TR/2013/NOTE-prov-links-20130430/


        print "start"
        g = prov_to_graph(bundle_document)


        for from_node, to_node, relations in g.edges_iter(data=True):
            for key,relation in relations.iteritems():
                print PROV_N_MAP[relation.get_type()]
                print relation.get_type()
                if relation.get_type() is PROV['Mention']:
                    print "yes"


        print "end"





