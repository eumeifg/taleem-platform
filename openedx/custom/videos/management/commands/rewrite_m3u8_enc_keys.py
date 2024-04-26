"""
Change URL of enc key in m3u8 files.

How to run?
python manage.py lms rewrite_m3u8_enc_keys
"""
import json
import requests

from django.core.management.base import BaseCommand
from django.conf import settings
from openedx.custom.storage.utils import get_s3_client


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Endpoints/URLs
        # "https://s3.staging.ta3leem.creativeadvtech.ml"
        storage_url = settings.VIDEO_DOWNLOAD_PIPELINE['STORAGE_ENDPOINT']
        print("Example VDS URL: https://vds.tal3eem.staging.env.creativeadvtech.ml")
        vds_url = input("Please enter VDS URL:")
        bucket_name = settings.VIDEO_DOWNLOAD_PIPELINE['BUCKET']
        print("On production enter root path: ta3leem/")
        root_path = input("If you are on prod enter ta3leem/ or Press Enter to leave blank:")

        client = get_s3_client(
            endpoint_url=storage_url,
            access_key=settings.VIDEO_DOWNLOAD_PIPELINE['STORAGE_ACCESS_KEY'],
            secret_key=settings.VIDEO_DOWNLOAD_PIPELINE['STORAGE_SECRET_KEY'],
            bucket_name=bucket_name,
            bump_head=False,
        )
        token = None
        more = True
        object_keys = []
        while(more):
            if token:
                res = client.list_objects_v2(Bucket=bucket_name,
                    Prefix=root_path+"processed",
                    ContinuationToken=token)
            else:
                res = client.list_objects_v2(Bucket=bucket_name,
                    Prefix=root_path+"processed")
            more = res.get('IsTruncated')
            token = res.get('NextContinuationToken')
            object_keys += [
                obj_meta['Key'] for obj_meta in res['Contents']
                if obj_meta['Key'].endswith(".m3u8")
            ]
        print("Sit back and relax ! Number of files to be modified: {}".format(len(object_keys)))
        failed = []
        for object_key in object_keys:
            try:
                response = client.get_object(Bucket=bucket_name, Key=object_key)
                m3u8_str = response['Body'].read().decode()
                find_str = 'METHOD=AES-128,URI="{storage_url}'.format(storage_url=storage_url)
                replace_str = 'METHOD=AES-128,URI="{vds_url}'.format(vds_url=vds_url)
                updated_m3u8 = m3u8_str.replace(find_str, replace_str).encode()
            except Exception as e:
                failed.append({'key': object_key, 'error': str(e)})
                continue
            client.put_object(Body=updated_m3u8, Bucket=bucket_name, Key=object_key)

        if failed:
            print("Failed:")
            print(json.dumps(failed, sort_keys=True, indent=4))
        else:
            print("Done !")
