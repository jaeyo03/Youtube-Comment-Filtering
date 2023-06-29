from transformers import AutoTokenizer, AutoModelForSequenceClassification

tokenizer = AutoTokenizer.from_pretrained("mariagrandury/roberta-base-finetuned-sms-spam-detection")

model = AutoModelForSequenceClassification.from_pretrained("mariagrandury/roberta-base-finetuned-sms-spam-detection")


import pandas as pd
import transformers
from datetime import datetime
import torch
import os 
import re
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, regexp_replace, struct, sum
from pyspark.sql.types import StringType
from pyspark.sql.functions import udf
from pyspark.ml import Transformer
from pyspark.sql.types import StructType, StructField, IntegerType, FloatType
from google.cloud import storage




# SparkSession 생성
spark = SparkSession.builder.appName("MySparkJob").getOrCreate()

# GCS에서 데이터 읽기
df = spark \
  .read \
  .option ( "inferSchema" , "true" ) \
  .option ( "header" , "true" ) \
  .csv ('gs://dbproject_comment/comment_output/*')




# 파일 이름 지정
# 불러온 데이터를 csv로 past_data에 저장
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
file_name = f"{timestamp}.csv"

# 기존 파일을 저장하려는 경로 지정
output_path_origin = f"gs://dbproject_comment/pass_data/{file_name}"


df.write.option('header', 'true') \
        .option('delimiter', ',') \
        .option('quote', '"') \
        .option('escape', '"') \
        .csv(output_path_origin)




#결측치제거
df = df.dropna()
# "댓글" 컬럼에서 이모티콘과 특수문자 제거
df = df.withColumn("댓글", regexp_replace(col("댓글"), "[^\uAC00-\uD7A3xfe0-9a-zA-Z\\s]", "").cast(StringType()))


#udf 선언
def predict_spam_udf(text):
    # 전처리
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    # 예측
    outputs = model(**inputs)
    # 결과 반환
    return int(torch.argmax(outputs.logits)), float(torch.softmax(outputs.logits,dim=1)[0][1])

# 구조체 선언
predict_spam = udf(predict_spam_udf, StructType([
    StructField("prediction", IntegerType()),
    StructField("probability", FloatType())
]))



# 데이터 프레임에 추가

predictions = predict_spam(col("댓글")).alias("predictions")
df = df.withColumn("is_spam", predictions.getField("prediction"))
df = df.withColumn("spam_probability", predictions.getField("probability"))

sum_value = df.select(sum("is_spam")).collect()[0][0]
spam_df = df.filter(col("is_spam") == 1)
#spam_df.show()



# 스팸 데이터를 csv로 past_data에 저장
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
file_name = f"{timestamp}.csv"

#  파일을 저장하려는 경로 지정
output_path_spam = f"gs://dbproject_comment/spam_output/{file_name}"


# 데이터프레임을 CSV 파일로 저장
spam_df.write.option("header", "true") \
        .option("delimiter", ",") \
        .option("quote", "\"") \
        .option("escape", "\"") \
        .csv(output_path_spam)



# 스팸 데이터를 csv로 past_data에 저장

#  파일을 저장하려는 경로 지정
output_path_process = f"gs://dbproject_comment/processing_output/{file_name}"


df.write.option('header', 'true') \
        .option('delimiter', ',') \
        .option('quote', '"') \
        .option('escape', '"') \
        .csv(output_path_process)


hdfs_output_path = "hdfs:///output/"+ timestamp
df.write.parquet(hdfs_output_path)

#이젠 불러와진 데이터를 storage에서 삭제
def delete_files_in_folder(bucket_name, folder_path):
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=folder_path)  # 폴더 내의 모든 Blob 가져오기

    for blob in blobs:
        blob.delete()  # Blob 삭제


# 제거
bucket_name = "dbproject_comment"
folder_path = "comment_output"
delete_files_in_folder(bucket_name, folder_path)



