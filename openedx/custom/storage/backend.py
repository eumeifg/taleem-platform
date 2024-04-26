'''
Custom storage backend based on s3boto3.
'''
import os
from boto3 import Session
from botocore.client import Config
from boto3.s3.transfer import TransferConfig

from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


KB = 1024
MB = KB * KB

class S3TA3Storage(S3Boto3Storage):
    def _save_content(self, obj, content, parameters):
        # head bucket before save
        session = Session(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region_name,
        )
        client = session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )
        client.head_bucket(Bucket=self.bucket_name)

        # only pass backwards incompatible arguments if they vary from the default
        put_parameters = parameters.copy() if parameters else {}
        if self.encryption:
            put_parameters['ServerSideEncryption'] = 'AES256'
        if self.reduced_redundancy:
            put_parameters['StorageClass'] = 'REDUCED_REDUNDANCY'
        if self.default_acl:
            put_parameters['ACL'] = self.default_acl
        content.seek(0, os.SEEK_SET)

        transfer_config = TransferConfig(multipart_threshold=500*MB)
        client.upload_fileobj(content, obj.bucket_name, obj.key,
            ExtraArgs=put_parameters, Config=transfer_config)


    # URL considering public endpoint
    def url(self, name, parameters=None, expire=None):
        # Preserve the trailing slash after normalizing the path.
        name = self._normalize_name(self._clean_name(name))
        if self.custom_domain:
            return "%s//%s/%s" % (self.url_protocol,
                                  self.custom_domain, filepath_to_uri(name))
        if expire is None:
            expire = self.querystring_expire

        params = parameters.copy() if parameters else {}
        params['Bucket'] = self.bucket.name
        params['Key'] = self._encode_name(name)
        read_url = getattr(settings, "AWS_S3_READ_URL", None)
        url = self.bucket.meta.client.generate_presigned_url('get_object', Params=params,
                                                             ExpiresIn=expire, ReadURL=read_url)
        if self.querystring_auth:
            return url
        return self._strip_signing_parameters(url)
