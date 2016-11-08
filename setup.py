#!/usr/bin/env python
from setuptools import setup

setup(name='provneo4j',
    version='0.4',
    description='Neo4j PROV API client',
    keywords = 'provenance prov graph neo4j',
    author='DLR, Sam Millar, Stefan Bieliauskas',
    author_email='opensource@dlr.de, sam@millar.io, sb@conts.de',
    url='https://github.com/DLR-SC/provneo4j',
    packages=['provneo4j'],
    install_requires=[
        'prov>=1.0.0',
        'requests',
        'prov-db-connector'
    ],
    license="MIT",
    test_suite='provneo4j.tests',
        classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
    ],
)
