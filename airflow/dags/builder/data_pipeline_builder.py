from airflow import AirflowException
from airflow.operators.dummy_operator import DummyOperator
from pipelines.pipeline_postgress_operator import PostgresElasticsearchPipelineOperator



def build(dag, pipeline):

    #
    start_pipeline = DummyOperator(
        task_id='start-pipeline',
        dag=dag
    )

    chainer = start_pipeline

    # matching
    if pipeline['source']['type'] == 'postgres':
        if pipeline['target']['type'] == 'elasticsearch':
            pipeline_operator = PostgresElasticsearchPipelineOperator(
                dag=dag,
                task_id='pipeline',
                pipeline=pipeline
            )

            chainer >> pipeline_operator
            chainer = pipeline_operator

    # check on natched operator
    if chainer == start_pipeline:
        raise AirflowException("Pipeline has not been matched to any possible PipelineOperator")

    #
    finish_pipeline = DummyOperator(
        task_id='finish-pipeline',
        dag=dag
    )

    #
    chainer >> finish_pipeline
