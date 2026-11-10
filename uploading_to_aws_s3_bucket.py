from botocore.exceptions import ClientError
import boto3
import logging

def sending_to_s3(file_name: str , bucket: str , bucket_key: str):
    s3_client = boto3.client("s3",region_name="ca-central-1")
    logger = logging.getLogger(f"etl.{__name__}")

    try:
        s3_client.upload_file(Filename= file_name , Bucket= bucket , Key= bucket_key)
        logger.info("file uploaded successfully")

    except ClientError as e:
        logger.error(e.response.get("Error",{}).get("Message",{}))