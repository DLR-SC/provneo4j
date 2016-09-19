FROM neo4j

ADD . /prov-neo4j-api

RUN echo "Install c compiler"
RUN apt-get clean && apt-get -y update

RUN  apt-get -y --fix-missing install python-pip python2.7-dev build-essential
RUN  pip install --upgrade pip
# install "virtualenv", since the vast majority of users of this image will want it
RUN  pip install --upgrade virtualenv --no-cache-dir

RUN  cd /prov-neo4j-api && pip install -r requirements.txt

WORKDIR /var/lib/neo4j

COPY docker-entrypoint.sh /docker-entrypoint-provneo4j-api.sh

#Fix : https://github.com/klaemo/docker-couchdb/issues/19
RUN chmod +x /docker-entrypoint-provneo4j-api.sh
RUN chmod +x /docker-entrypoint.sh
#Fix End


ENTRYPOINT ["/docker-entrypoint-provneo4j-api.sh"]
#CMD ["neo4j"]

#/var/lib/neo4j/bin/neo4j stop && /var/lib/neo4j/bin/neo4j start; sleep 10s  && cd /prov-neo4j-api
#&& curl -vX POST http://neo4j:neo4j@localhost:7474/user/neo4j/password -d"password=neo4jneo4j"