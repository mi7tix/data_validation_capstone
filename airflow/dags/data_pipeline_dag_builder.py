import logging
from airflow.models import DAG, Variable
from airflow.utils import dates
from datetime import datetime, timedelta
from builder import data_pipeline_builder
import json

'''
with open('./pipelines.json') as json_file:
            pipelines = json.load(json_file)

logging.info('read json_config {}'.format(pipelines))
'''
# read airflow variable with pipeline as JSON
logging.info('read variable')

pipelines = Variable.get("pipelines", deserialize_json=True)

logging.info(f'pipelines: {pipelines}')


# pipeline resolver
for pipeline in pipelines:
    # DagID based on PROJECT-FLOW-SOURCE.TYPE
    dag_id = f"{pipelines['project']}-{pipelines['flow']}-{pipelines['source']['type']}-monitoring-dag"

    # dags default args
    dag_args = {
        'owner': pipelines['owner'],
        'depends_on_past': False,
        'start_date': dates.days_ago(10),
        'end_date': None,
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': 0
    }

    # pipeline dag dynamically created
    pipeline_dag = DAG(
        dag_id=dag_id,
        default_args=dag_args,
        catchup=False,
        schedule_interval=pipelines.get('schedule', None),
        description=pipelines['description'],
        max_active_runs=1
    )

    # build dag flow
    data_pipeline_builder.build(pipeline_dag, pipelines)

    # reg
    globals()[dag_id] = pipeline_dag
