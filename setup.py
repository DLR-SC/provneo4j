#!/usr/bin/env python
from setuptools import setup

setup(name='provneo4j-api',
    version='0.0.1',
    description='Neo4J Prov API client',
    author='Sam Millar, Stefan Bieliauskas',
    author_email='sam@millar.io, sb@conts.e',
    url='https://github.com/DLR-SC/provneo4j-api',
    packages=['provstore'],
    install_requires=[
        'prov>=1.0.0',
        'requests',
        'neo4jrestclient'
    ],
    license="MIT",
    test_suite='provstore.tests',
)
