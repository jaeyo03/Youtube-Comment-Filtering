import pandas as pd
from googleapiclient.discovery import build
import time
import os
import datetime

# gcs
from google.cloud import storage

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="db-project-381514-6612cc127860.json"


video_id = 'cwLXqtVMbVs'
comments = list()
api_obj = build('youtube', 'v3', developerKey='AIzaSyB0yxCBhji8ygtCWUDaxs7wV6hdVcy5gR0')


# GCS 버킷 설정
bucket_name = 'dbproject_comment'  # GCS 버킷 이름
blob_name = 'comment_data'  # GCS 버킷에 저장될 Blob 이름



while True:
    response = api_obj.commentThreads().list(part='snippet,replies', videoId=video_id, maxResults=100).execute()
    new_comments = []

    for item in response['items']:
        comment = item['snippet']['topLevelComment']['snippet']
        if [comment['textDisplay'], comment['authorDisplayName'], comment['publishedAt'], comment['likeCount']] not in comments:
            new_comments.append([comment['textDisplay'], comment['authorDisplayName'], comment['publishedAt'], comment['likeCount']])

        if item['snippet']['totalReplyCount'] > 0:
            for reply_item in item['replies']['comments']:
                reply = reply_item['snippet']
                if [reply['textDisplay'], reply['authorDisplayName'], reply['publishedAt'], reply['likeCount']] not in comments:
                    new_comments.append([reply['textDisplay'], reply['authorDisplayName'], reply['publishedAt'], reply['likeCount']])

    if new_comments:
        df = pd.DataFrame(new_comments, columns=['댓글','작성자','작성시간','좋아요수'])
        print(df)
        comments += new_comments

# GCS 클라이언트 생성
    client = storage.Client()

# 존재하는 버킷의 이름
    bucket_name = 'dbproject_comment'

# 폴더 경로와 현재 시간을 포함한 파일 이름 생성
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder_name = 'comment_output'
    blob_name = f"{folder_name}/{current_time}.csv"

# 데이터프레임을 GCS 버킷에 업로드
    csv_string = df.to_csv(index=False)

# Blob 객체 생성
    blob = client.bucket(bucket_name).blob(blob_name)

    blob.upload_from_string(csv_string.encode(), content_type='text/csv')

    print(f'Dataframe uploaded to {bucket_name}/{blob_name}.')

    time.sleep(300) # 1분 대기 후 반복


