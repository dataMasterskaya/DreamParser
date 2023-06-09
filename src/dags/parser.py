import datetime
from datetime import timedelta

from airflow.models import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.models import Variable

default_args = {
    'owner': 'Fedor Mushenok',
    'depends_on_past': False,
    'email': ['mushenokf@yandex.ru'],
    'email_on_failure': True,
    'email_on_retry': True,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    # 'end_date': datetime(2016, 1, 1),
    # 'wait_for_downstream': False,
    # 'dag': dag,
    # 'sla': timedelta(hours=2),
    # 'execution_timeout': timedelta(seconds=300),
    # 'on_failure_callback': some_function,
    # 'on_success_callback': some_other_function,
    # 'on_retry_callback': another_function,
    # 'sla_miss_callback': yet_another_function,
    # 'trigger_rule': 'all_success'
}

dag = DAG(dag_id="parser", catchup=False,
        default_args=default_args,
        start_date=datetime.datetime(2023, 5, 6),
        schedule_interval="@daily",
        tags=["parser"])

env_vars = {"AWS_ACCESS_KEY_ID": Variable.get("PARSER_AWS_ACCESS_KEY_ID"),
            "AWS_SECRET_ACCESS_KEY": Variable.get("PARSER_AWS_SECRET_ACCESS_KEY"),
            "AWS_DEFAULT_REGION": Variable.get("PARSER_AWS_DEFAULT_REGION"),
            "CH_CLUSTER_URL": Variable.get("PARSER_CH_CLUSTER_URL"),
            "CH_PASSWORD": Variable.get("PARSER_CH_PASSWORD"),
            "CH_DB": Variable.get("PARSER_CH_DB"),
            "CH_USERNAME": Variable.get("PARSER_CH_USERNAME"),
}

parse = DockerOperator(image="physci/dreamparser",
                    auto_remove=True,
                    container_name="parser",
                    tty=True,
                    task_id="parse",
                    dag=dag,
                    environment=env_vars)

upload = DockerOperator(image="physci/dreamparser:db",
                        auto_remove=True,
                        container_name="upload",
                        tty=True,
                        task_id="upload",
                        dag=dag,
                        environment=env_vars)


parse >> upload