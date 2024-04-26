'''
Utility related to storage.
'''

from boto3 import Session
from botocore.client import Config

from django.conf import settings


def get_s3_client(endpoint_url='',
    access_key='',
    secret_key='',
    bucket_name='',
    bump_head=True):
    session = Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name='us-east-1',
    )
    client = session.client(
        "s3",
        endpoint_url=endpoint_url,
        region_name='us-east-1',
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    if bump_head:
        client.head_bucket(Bucket=bucket_name)
    return client

