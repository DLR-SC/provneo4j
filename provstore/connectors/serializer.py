
class Serializer:

    @staticmethod
    def valid_qualified_name(bundle, value):
        if value is None:
            return None
        qualified_name = bundle.valid_qualified_name(value)
        return qualified_name


    def __init__(self):
        pass