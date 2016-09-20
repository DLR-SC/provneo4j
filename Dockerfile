FROM python:2.7
ADD . /usr/src/app
WORKDIR /usr/src/app
RUN pip install -r requirements.txt
CMD sleep 20; curl -vX POST http://neo4j:neo4j@neo4j-server:7474/user/neo4j/password -d"password=neo4jneo4j"; python setup.py test
