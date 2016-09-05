import os
import json
import requests
from copy import copy
from prov.model import ProvDocument
from provstore.document import Document
from neo4jrestclient.client import GraphDatabase, StatusException
from prov.model import ProvDocument, PROV, DEFAULT_NAMESPACES
from neo4jrestclient.client import GraphDatabase, StatusException
from prov.constants import PROV_N_MAP
from prov.graph import prov_to_graph

from connector import *



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
        # node is a MulitDiGrpah.Node
        # see: http://networkx.readthedocs.io/en/networkx-1.10/reference/classes.multidigraph.html

        n = self._connection.nodes.create()
        n.labels.add(str(node.label))
        properties =  dict(map(lambda (key, value): (str(key), str(value)), node.attributes))

        #add namespace
        namespace = node.label.namespace
        if namespace is None:
            raise InvalidDataException("every node need a namespace the node " + node.label + " has no namespace")

        properties.update({
            "namespace:uri": namespace.uri,
            "namespace:prefix": namespace.prefix
        })
        print properties
        n.properties = properties

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

    def post_document(self, prov_document,name=None):
        # creates a database entry from a prov-n document
        # returns the saved neo4J doc
        #

        gdb = self._connection

        # create graph from prov doc
        g = prov_to_graph(prov_document)

        # store all database nodes in dict
        db_nodes = {}

        # Create nodes
        for node in g.nodes():
            db_nodes[node] = self._create_node(node)

        # Begin transaction for relations
        with gdb.transaction() as tx:
            # Create relations
            for from_node, to_node, relations in g.edges_iter(data=True):

                # interate over relations (usually only one item)
                for key, relation in relations.iteritems():
                    self._create_relation(db_nodes,from_node,to_node,relation)

        return None
