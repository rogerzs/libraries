import pyspark
import boto3
import json
import datetime
from pyspark.sql.functions import lit, col, year, month, dayofmonth, translate, length, size, from_json, when, concat
from pyspark.sql.types import *

class Transform:
    def __init__(self, args, spark):
        self.spark = spark
        self.source_path = args['source_path']
        self.source_bucket = args['source_bucket']
        self.query_path = args['query_key']
        self.table_name = args['table_name']
        self.destination_path = args['destination_path']

    def run(self):
        self.main()

    def getParamsFromS3(self,bucket,path):
        s3 = boto3.resource('s3')
        obj = s3.Object(bucket, path)
        body = obj.get()['Body'].read()
        return body

    def transform(self,source_bucket,query_path,table_name):
        query = self.getParamsFromS3(source_bucket,query_path)
        query_formated = query.format(table_name)
        query_formated = """{}""".format(query_formated) 
        return query_formated

    def main(self):
        now = datetime.datetime.now()

        day = now.strftime('%d')
        month = now.strftime('%m')
        year = now.strftime('%Y')

        ## Read data from S3
        source_path = self.source_path + '/' + year + '/' + month + '/' + day + '/'
        df1 = self.spark.read.parquet(source_path)

        ## Create temp view 
        df1.createOrReplaceTempView(self.table_name)

        ## Transform data 
        dataFrame = self.spark.sql(self.transform(self.source_bucket,self.query_path,self.table_name))

        ## Write to S3
        dataFrame.withColumn('__transform_created_at', lit(datetime.datetime.now())).write.parquet(self.destination_path + '/' + year + '/' + month + '/' + day)