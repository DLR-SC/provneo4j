provneo4j-api [![PyPI version](https://badge.fury.io/py/provstore-api.svg)](http://badge.fury.io/py/provneo4j-api) [![Build Status](https://travis-ci.org/DLR-SC/provneo4j-api.svg?branch=master)](https://travis-ci.org/DLR-SC/provneo4j-api) [![Coverage Status](https://coveralls.io/repos/DLR-SC/provneo4j-api/badge.png)](https://coveralls.io/r/millar/provstore-api)
=========

PROV Client for the [Neo4j](https://neo4j.com/) graph database 

(based on [provstore-api](https://github.com/millar/provstore-api).)

## Installation
```bash
pip install provneo4j-api
```

You can view [provneo4j-api on PyPi's package index](https://pypi.python.org/pypi/provneo4j-api/)
## Usage

To use the client import the API and configure your access credentials:

```python
from provneo4j.api import Api

api = Api(userame="your_neo4j_username", password="your_password")
```

*Note: credentials can also be set via the `PROVNEO4J_USERNAME` and `PROVNEO4J_PASSWORD` environment variables and omitted from the initialization.*

For demonstrations purposes we will use the ProvDocuments given in the examples
module, but you would use your documents instead.
```python
import provstore.tests.examples as examples
```

#### Storing documents

```python
prov_document = examples.flat_document()
prov_bundle = examples.flat_document()

# Store the document to ProvStore:
#   - the public parameter is optional and defaults to False
stored_document = api.document.create(prov_document,
                                      name="name",
                                      public=False)

# => This will store the document and return a ProvStore Document object
```

#### Retrieving documents

```python
# Get a document with ID 148 from ProvStore:
stored_document = api.document.get(148)
# The document's provenance is available like so:
stored_document.prov

# => This will fetch the document and return a ProvStore Document object
```

#### Deleting documents

```python
# Delete the document with ID 148 from the store:
api.document.get(148).delete()
```

#### Adding bundles

```python
# Get document with this ID's bundles
api.document.get(148).add_bundle(prov_bundle, 'ex:bundle-1')
# or the shorthand:
api.document.get(148).bundles['ex:bundle-1'] = prov_bundle
```

#### Fetching bundle

```python
# Get document's bundle with matching identifier
api.document.get(148).bundles['ex:bundle-1']
```

#### Iterating over bundles
```python
# Get document with this ID's bundles
# WARNING: This is expensive, consider using api.document.get(148).prov.bundles instead
for bundle in api.document.get(148).bundles:
    # print the bundle's identifier
    print bundle.identifier
    # the bundle's provenance is at:
    bundle.prov
```


## Contribute

- Issue Tracker: https://github.com/DLR-SC/provneo4j-api/issues
- Source Code: https://github.com/DLR-SC/provneo4j-api

## Documentation

- Available on [ReadTheDocs](http://provstore-api.readthedocs.org/en/latest/)

### API
- See the [full API reference](http://provstore-api.readthedocs.org/en/latest/provstore.html)

## License

This project is licensed under the MIT license.

## Contributors

Sam Millar &lt;http://millar.io&gt;

Stefan Bieliauskas 
