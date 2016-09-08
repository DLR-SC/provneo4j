
from provstore.connectors.connector import *
from provstore.connectors.deserializer import Deserializer
from provstore.connectors.neo4j_rest.neo4j import DOC_PROPERTY_MAP,DOC_PROPERTY_NAME_LABEL,DOC_PROPERTY_NAME_NAMESPACE_URI,DOC_PROPERTY_NAME_NAMESPACE_PREFIX
from prov.model import PROV_REC_CLS,Namespace
from prov.constants import PROV_RECORD_IDS_MAP

class Neo4JRestDeserializer(Deserializer):

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

        #Remove all metda-data from the properties

        real_property_keys = set(db_record.properties.keys()) - set(DOC_PROPERTY_MAP)
        properties = filter(lambda (key,value): key in real_property_keys, db_record.properties.iteritems())

        #Get id for the node from the properties
        rec_id  = db_record.properties.get(DOC_PROPERTY_NAME_LABEL)
        return Deserializer.create_prov_record(bundle,rec_type,rec_id,properties)



    def create_relation(self,bundle,db_relation):
        print db_relation.type
        rec_type = Deserializer.valid_qualified_name(bundle,db_relation.type)
        if rec_type is None:
            #Normal prov namesocae
            rec_type = PROV_RECORD_IDS_MAP[db_relation.type]
            if rec_type is None:
                raise InvalidDataException("No valid relation type provided the type was %s"%db_relation.type)

        return Deserializer.create_prov_record(bundle, rec_type, None, db_relation.properties)


    def add_namespace(self,db_node,prov_bundle):
        prefix  = db_node.properties[DOC_PROPERTY_NAME_NAMESPACE_PREFIX]
        uri = db_node.properties[DOC_PROPERTY_NAME_NAMESPACE_URI]

        if prefix is not None and uri is not None:
            if prefix != 'default':
                prov_bundle.add_namespace(Namespace(prefix, uri))
            else:
                prov_bundle.set_default_namespace(uri)
        else:
            ProvDeserializerException("No valid namespace provided for the node: %s"%db_node)

