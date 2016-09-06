import os
import json
import requests
from copy import copy
from prov.model import ProvDocument, QualifiedName, Namespace,ProvBundle,ProvElement
from provstore.document import Document
from neo4jrestclient.client import GraphDatabase, StatusException
from prov.model import ProvDocument, PROV, DEFAULT_NAMESPACES
from neo4jrestclient.client import GraphDatabase, StatusException
from prov.constants import PROV_N_MAP
from provstore.prov_to_graph import prov_to_graph_flattern
from connector import *



DOC_PROPERTY_NAME_ID = "document:id"
DOC_PROPERTY_NAME_BUNDLES = "document:bundles"
DOC_PROPERTY_NAME_NAMESPACE_URI = "namespace:uri"
DOC_PROPERTY_NAME_NAMESPACE_PREFIX = "namespace:prefix"

DOC_QUERY_BY_ID = "MATCH (d) WHERE (d.`document:id`)=%i RETURN d"
DOC_DELETE_BY_ID = "MATCH (d) WHERE (d.`document:id`)=%i DETACH DELETE d"

BUNDLE_LABEL_NAME= "prov:Bundle"
BUNDLE_RELATION_NAME = "includeIn"

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

    def _create_node(self,node):
        # node is a MulitDiGrpah.Node / ProvRecord
        # see: http://networkx.readthedocs.io/en/networkx-1.10/reference/classes.multidigraph.html

        n = self._connection.nodes.create()

        if isinstance(node,ProvBundle):
            n.labels.add(BUNDLE_LABEL_NAME)
        elif isinstance(node,ProvElement):
            n.labels.add(str(node.get_type()))
            n.properties = dict(map(lambda (key, value): (str(key), str(value)), node.attributes))
        else:
            raise InvalidDataException("Not supportet node class you passed %s " %type(node))

        n.set("label", (str(node.identifier)))
        return n

    def _create_relation(self,db_nodes,from_node,to_node,relation):

        if relation.label == None:
            relationName = PROV_N_MAP[relation.get_type()]
        else:
            relationName = str(relation.label)  # @todo Test this part of the code

        # Attributes to string map
        attributes = map(lambda (key, value): (str(key), str(value)), relation.attributes)


        db_from_node = db_nodes[from_node]
        db_to_node = db_nodes[to_node]

        db_from_node.relationships.create(relationName, db_to_node, **dict(attributes))

    def _create_bundle_relation(self, db_nodes, from_node, to_bundle):
        db_to_bundle = db_nodes[to_bundle.identifier]
        db_from_node = db_nodes[from_node]
        db_from_node.relationships.create(BUNDLE_RELATION_NAME, db_to_bundle )

        pass
    def _add_meta_data_to_node(self,db_node,identifier, doc_id):

        # add namespace
        if isinstance(identifier,QualifiedName)and isinstance(identifier.namespace,Namespace):

            namespace = identifier.namespace
            db_node.set(DOC_PROPERTY_NAME_NAMESPACE_URI,namespace.uri)
            db_node.set(DOC_PROPERTY_NAME_NAMESPACE_PREFIX,namespace.prefix)

        db_node.set(DOC_PROPERTY_NAME_ID,doc_id)

    def post_document(self, prov_document,name=None):
        # creates a database entry from a prov-n document
        # returns the saved neo4J doc
        #

        gdb = self._connection

        # create graph from prov doc
        g = prov_to_graph_flattern(prov_document)

        # store all database nodes in dict
        db_nodes = {}

        nodes = g.nodes()
        if len(nodes) is 0:
            nodes = prov_document.get_records()
        # Create nodes / for prov
        for node in nodes:
            db_nodes[node] = self._create_node(node)
        # Create nodes for bundles
        for bundle in prov_document.bundles:
            db_nodes[bundle.identifier] = self._create_node(bundle)

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
                    self._create_relation(db_nodes,from_node,to_node,relation)

            #Create relation to the bundle node
            for bundle in prov_document.bundles:
                for record in bundle.get_records(ProvElement):
                    self._create_bundle_relation(db_nodes, record, bundle)


        #Add meta data to each node
        for graph_node,db_node in db_nodes.iteritems():
            if type(graph_node) is QualifiedName:
                self._add_meta_data_to_node(db_node,graph_node,doc_node.id)
            elif isinstance(graph_node,ProvElement):
                self._add_meta_data_to_node(db_node,graph_node.identifier,doc_node.id)
            else:
                raise InvalidDataException("unknown type: %s" %type(graph_node))

        return doc_node.id

    def delete_doc(self,document_id):
        self._connection.query(q=DOC_DELETE_BY_ID % document_id)
        return True

    def add_bundle(self, document_id, bundle_document, identifier):
        bundle_doc_id = self.post_document(bundle_document, identifier)
        doc = self._connection.nodes.get(document_id)
        bundles_ids = doc.get(DOC_PROPERTY_NAME_BUNDLES, list())
        bundles_ids.append(bundle_doc_id)
        doc.set(DOC_PROPERTY_NAME_BUNDLES, bundles_ids)

