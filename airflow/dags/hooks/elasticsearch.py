import logging

from airflow.hooks.dbapi_hook import DbApiHook
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


class ElasticsearchHook(DbApiHook):
    """
        Interact with Elasticsearch through the elasticsearch-dbapi
    """

    conn_name_attr = 'elasticsearch_conn_id'
    default_conn_name = 'elasticsearch_default'

    def __init__(self,
                 conn_id=default_conn_name,
                 connection=None,
                 client:Elasticsearch=None,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.conn_id = conn_id
        self.connection = connection
        self.client = client

    def open_client(self) -> Elasticsearch:
        """
        Returns a elasticsearch connection object
        """
        if self.client is None:
            # use default or past-in conn_id
            connection = self.connection or self.get_connection(self.conn_id)

            logging.info("Connection", connection)

            # elasticsearch client
            self.client = Elasticsearch(
                hosts=connection.host
                #http_auth=(connection.login, connection.password)
            )
        else:
            self.client

        return self.client


    # TODO: decide where to place index
    def create_index(self):
        self.open_client().indices.exists(index="some-index")
        self.open_client().indices.create(
            index="airflow_test_dump",
            body={
                "settings": {"number_of_shards": 3},
                "mappings": {
                    "properties": {
                        "field1_name": {"type": "text"},
                        "field2_name": {"type": "keyword"},
                        "field3_name": {"type": "geo_point"},
                    }
                },
            },
            ignore=400,
        )


    def insert_data(self, index: str, type: str, labels: list, data: list):

        # prepare bulk and parse rows
        body = []
        for item in data:
            body.append({'index': {'_index': index, '_type': 'doc'}})
            body.append(dict(zip(labels, item)))

        logging.info(f"body: ${body}")

        insert_result = self.open_client().bulk(body=body)

        logging.info(f"Insert result: ${insert_result}")
