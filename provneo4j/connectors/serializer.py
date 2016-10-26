from prov.constants import *
from prov.model import QualifiedName, Identifier, Literal

from datetime import datetime


# Reverse map for prov.model.XSD_DATATYPE_PARSERS
LITERAL_XSDTYPE_MAP = {
    float: 'xsd:double',
    int: 'xsd:int'
    # boolean, string values are supported natively by PROV-JSON
    # datetime values are converted separately
}

# Add long on Python 2
if six.integer_types[-1] not in LITERAL_XSDTYPE_MAP:
    LITERAL_XSDTYPE_MAP[six.integer_types[-1]] = 'xsd:long'


class Serializer:

    @staticmethod
    def encode_string_value(value):
        if type(value) is unicode:
            return value.encode("utf8")
        elif isinstance(value, Literal):
            return value.value
        elif type(value) is bool:
            return value
        return str(value)

    @staticmethod
    def valid_qualified_name(bundle, value):
        if value is None:
            return None
        qualified_name = bundle.valid_qualified_name(value)
        return qualified_name

    @staticmethod
    def literal_json_representation(literal):
        # TODO: QName export
        value, datatype, langtag = literal.value, literal.datatype, literal.langtag
        if langtag:
            return {'lang': langtag}
        else:
            return {'type': six.text_type(datatype)}

    @staticmethod
    def encode_json_representation(value):
        if isinstance(value, Literal):
            return Serializer.literal_json_representation(value)
        elif isinstance(value, datetime):
            return {'type': 'xsd:dateTime'}
        elif isinstance(value, QualifiedName):
            # TODO Manage prefix in the whole structure consistently
            # TODO QName export
            return {'type': PROV_QUALIFIEDNAME._str}
        elif isinstance(value, Identifier):
            return {'type': 'xsd:anyURI'}
        elif type(value) in LITERAL_XSDTYPE_MAP:
            return {'type': LITERAL_XSDTYPE_MAP[type(value)]}
        else:
            return None

    def __init__(self):
        pass
