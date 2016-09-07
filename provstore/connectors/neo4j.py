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
from connector import *
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

class Deserializer:

    @staticmethod
    def decode_json_representation(literal, bundle):
        if isinstance(literal, dict):
            # complex type
            value = literal['$']
            datatype = literal['type'] if 'type' in literal else None
            datatype = Deserializer.valid_qualified_name(bundle, datatype)
            langtag = literal['lang'] if 'lang' in literal else None
            if datatype == XSD_ANYURI:
                return Identifier(value)
            elif datatype == PROV_QUALIFIEDNAME:
                return Deserializer.valid_qualified_name(bundle, value)
            else:
                # The literal of standard Python types is not converted here
                # It will be automatically converted when added to a record by
                # _auto_literal_conversion()
                return Literal(value, datatype, langtag)
        else:
            # simple type, just return it
            return literal

    @staticmethod
    def valid_qualified_name(bundle, value):
        if value is None:
            return None
        qualified_name = bundle.valid_qualified_name(value)
        return qualified_name

    @staticmethod
    def create_prov_record(bundle,prov_type, prov_id, properties):
        """

        :param prov_type: valid prov type like prov:Entry as string
        :param prov_id: valid id as string like <namespace>:<name>
        :param properties: dict{attr_name:attr_value} dict with all properties (prov and additional)
        :return: ProvRecord
        """
        # Parse attributes
        attributes = dict()
        other_attributes = []
        # this is for the multiple-entity membership hack to come
        membership_extra_members = None
        for attr_name, values in properties.iteritems():
            print attr_name
            if attr_name not in DOC_PROPERTY_MAP:

                attr = (
                    PROV_ATTRIBUTES_ID_MAP[attr_name]
                    if attr_name in PROV_ATTRIBUTES_ID_MAP
                    else Deserializer.valid_qualified_name(bundle, attr_name)
                )
                if attr in PROV_ATTRIBUTES:
                    if isinstance(values, list):
                        # only one value is allowed
                        if len(values) > 1:
                            # unless it is the membership hack
                            if prov_type == PROV_MEMBERSHIP and \
                                            attr == PROV_ATTR_ENTITY:
                                # This is a membership relation with
                                # multiple entities
                                # HACK: create multiple membership
                                # relations, one x each entity

                                # Store all the extra entities
                                membership_extra_members = values[1:]
                                # Create the first membership relation as
                                # normal for the first entity
                                value = values[0]
                            else:
                                error_msg = (
                                    'The prov package does not support PROV'
                                    ' attributes having multiple values.'
                                )
                                logger.error(error_msg)
                                raise ProvDeserializerException(error_msg)
                        else:
                            value = values[0]
                    else:
                        value = values
                    value = (
                        Deserializer.valid_qualified_name(bundle, value)
                        if attr in PROV_ATTRIBUTE_QNAMES
                        else parse_xsd_datetime(value)
                    )
                    attributes[attr] = value
                else:
                    if isinstance(values, list):
                        other_attributes.extend(
                            (
                                attr,
                                Deserializer.decode_json_representation(value, bundle)
                            )
                            for value in values
                        )
                    else:
                        # single value
                        other_attributes.append(
                            (
                                attr,
                                Deserializer.decode_json_representation(values, bundle)
                            )
                        )
        record = bundle.new_record(
            prov_type, prov_id, attributes, other_attributes
        )
        # HACK: creating extra (unidentified) membership relations
        if membership_extra_members:
            collection = attributes[PROV_ATTR_COLLECTION]
            for member in membership_extra_members:
                bundle.membership(
                    collection, Deserializer.valid_qualified_name(bundle, member)
                )
        return record



    def create_record(self,bundle,db_record):
        jc = []
        #Get type from label
        rec_type = None
        print db_record.labels

        for label in iter(db_record.labels):
            label = Deserializer.valid_qualified_name(bundle, label._label)
            if label in PROV_REC_CLS:
                rec_type = label

        if rec_type is None:
            raise InvalidDataException("A node must provide the type of the node(%s) as label" % db_record.url)

        #Get id for the node from the properties
        rec_id  = db_record.properties.get(DOC_PROPERTY_NAME_LABEL)
        return Deserializer.create_prov_record(bundle,rec_type,rec_id,db_record.properties)



    def create_relation(self,bundle,db_relation):
        print db_relation.type
        rec_type = Deserializer.valid_qualified_name(bundle,db_relation.type)
        if rec_type is None:
            #Normal prov namesocae
            rec_type = PROV_RECORD_IDS_MAP[db_relation.type]
            if rec_type is None:
                raise InvalidDataException("No valid relation type provided the type was %s"%db_relation.type)

        return Deserializer.create_prov_record(bundle, rec_type, None, db_relation.properties)




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

    def _create_db_node(self, node):
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

        n.set(DOC_PROPERTY_NAME_LABEL, (str(node.identifier)))
        return n

    def _create_relation(self,db_nodes,from_node,to_node,relation):

        # Attributes to string map
        attributes = map(lambda (key, value): (str(key), str(value)), relation.attributes)

        if relation.label == None:
            relationName = PROV_N_MAP[relation.get_type()]
        elif relation.identifier is not None:
            relationName = str(relation.identifier)  # @todo Test this part of the code
            attributes.append((DOC_PROPERTY_NAME_NAMESPACE_URI,relation.identifier.namescpae.uri))
            attributes.append((DOC_PROPERTY_NAME_NAMESPACE_PREFIX,relation.identifier.namescpae.prefix))
        else:
            raise InvalidDataException("Relation is not valid. The type of the relation is not a default prov relation and has no identifier")

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

    def _parse_meta_data_to_prov(self,db_node,prov_bundle):
        prefix  = db_node.properties[DOC_PROPERTY_NAME_NAMESPACE_PREFIX]
        uri = db_node.properties[DOC_PROPERTY_NAME_NAMESPACE_URI]

        if prefix is not None and uri is not Node:
            if prefix != 'default':
                prov_bundle.add_namespace(Namespace(prefix, uri))
            else:
                prov_bundle.set_default_namespace(uri)


    def get_document(self,document_id,prov_format):
        results = self._connection.query(q=DOC_GET_DOC_BY_ID % document_id, returns=(Node, Relationship,Node))
        prov_document = ProvDocument()
        all_records= {}
        deserializer = Deserializer()
        for db_from_node, db_relation, db_to_node in results:
            self._parse_meta_data_to_prov(db_from_node,prov_document)
            self._parse_meta_data_to_prov(db_to_node,prov_document)

            all_keys = all_records.keys()
            if db_from_node.id not in all_keys:
                all_records.update({int(db_from_node.id): deserializer.create_record(prov_document,db_from_node)})
            if db_to_node.id not in all_keys:
                all_records.update({int(db_to_node.id): deserializer.create_record(prov_document, db_to_node)})
            if db_relation.id not in all_keys:
                all_records.update({int(db_relation.id): deserializer.create_relation(prov_document, db_relation)})


        if prov_format is ProvDocument:
            return prov_document
        else:
            raise NotImplementedException("Neo4j connector only supports ProvDocument format during the get request")
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
            db_nodes[node] = self._create_db_node(node)
        # Create nodes for bundles
        for bundle in prov_document.bundles:
            db_nodes[bundle.identifier] = self._create_db_node(bundle)

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





