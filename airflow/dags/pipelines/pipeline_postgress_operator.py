import logging

import psycopg2
from airflow.hooks.postgres_hook import PostgresHook
from airflow.models import BaseOperator
from urllib.parse import urlparse

from hooks.elasticsearch import ElasticsearchHook

class PostgresElasticsearchPipelineOperator(BaseOperator):

    template_fields = ['pipeline']

    def __init__(self,
                 pipeline: dict,
                 *args,
                 **kwargs):
        super(PostgresElasticsearchPipelineOperator, self).__init__(*args, **kwargs)
        self.pipeline = pipeline


    def execute(self, context):

        logging.info(f"Pipeline: {self.pipeline}")

        # create PostgresHook
        source_connection = self.pipeline['source']['connection']

        if source_connection['declaration'] == 'implicit':
            source_hook = PostgresHook()
            source_hook.conn_name_attr = self.pipeline['source']['connection']['id']
            source_hook.run(sql=self.pipeline['source']['sqlQuery'])
            source_client = source_hook.get_cursor()
        else:
            if 'url' in source_connection:
                url = urlparse(source_connection['url'])
                logging.info(f"url: {url}")
                username = url.username
                password = url.password
                database = url.path[1:]
                hostname = url.hostname
                port = 5432
            else:
                username = source_connection['username']
                password = source_connection['password']
                database = source_connection['database']
                hostname = source_connection['hostname']
                port = source_connection['port']

            source_connect = psycopg2.connect(
                host=hostname,
                port=port,
                database=database,
                user=username,
                password=password
            )
            source_client = source_connect.cursor()
            source_client.execute(query=self.pipeline['source']['sqlQuery'])

        labels = [column[0] for column in source_client.description]
    
        # create ElasticsearchHook (destination)
        target_connection = self.pipeline['target']['connection']

        if target_connection['declaration'] == 'implicit':
            target_hook = ElasticsearchHook(conn_id=target_connection['id'])
            target_hook.open_client()


        # chain source_client and target_client together
        while True:
            source_data = source_client.fetchmany(1000)
            if source_data:
                target_hook.insert_data(
                    index=self.pipeline['target']['index'],
                    type=self.pipeline['target']['index-type'],
                    labels=labels,
                    data=source_data
                )
            else:
                break

        #source_hook.close()
        source_client.close()
