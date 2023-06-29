from google.cloud import dataproc_v1 as dataproc
import time

def run_dataproc(bucket_name, file_name):
    # Dataproc 작업 설정
    project_id = 'db-project-381514'
    region = 'us-central1'
    cluster_name = 'cluster-9bf0'

    job_client = dataproc.JobControllerClient(client_options={"api_endpoint": f"{region}-dataproc.googleapis.com:443"})

    timestamp = str(int(time.time()))  # 타임스탬프 생성
    job = {
        'reference': {
            'project_id': project_id,
            'job_id': timestamp
        },
        'placement': {
            'cluster_name': cluster_name
        },
        'pyspark_job': {
            'main_python_file_uri': 'gs://dbproject_comment/new_gcs.py',
            'args': ['gs://' + bucket_name + '/' + file_name]
        }
    }

    # Dataproc 작업 실행
    response = job_client.submit_job_as_operation(request={"project_id": project_id, "region": region, "job": job})
    print('Dataproc job submitted:', response.operation.name)


def gcs_trigger(event, context):
    # 파일 생성 트리거 이벤트 처리
    if event['name'] and event['contentType'] == 'text/csv':
        bucket_name = event['bucket']
        file_name = event['name']

        # 파일이 comment_output 폴더에 저장된 경우에만 실행
        if 'comment_output/' in file_name:
            run_dataproc(bucket_name, file_name)

    return 'Success'
