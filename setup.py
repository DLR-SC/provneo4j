#!/usr/bin/env python
from setuptools import setup

setup(name='provneo4j-api',
    version='0.1.1',
    description='Neo4j PROV API client',
    author='DLR, Sam Millar, Stefan Bieliauskas',
    author_email='sam@millar.io, sb@conts.de',
    url='https://github.com/DLR-SC/provneo4j-api',
    packages=['provneo4j', 'provneo4j.connectors', 'provneo4j.connectors.neo4j_rest', 'provneo4j.tests'],
    install_requires=[
        'prov>=1.0.0',
        'requests',
        'neo4jrestclient',
        'lxml'
    ],
    license="MIT",
    test_suite='provneo4j.tests',
)
