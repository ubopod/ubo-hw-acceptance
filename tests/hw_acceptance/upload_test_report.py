import logging
import boto3
from botocore.exceptions import ClientError
import os
import threading
import sys

class ProgressPercentage(object):

    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        # To simplify, assume this is hooked up to a single filename
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            # lcd.progress_wheel(self._filename, (percentage/100)*360, "green")
            sys.stdout.write(
                "\r%s  %s / %s  (%.2f%%)" % (
                    self._filename, self._seen_so_far, self._size,
                    percentage))
            sys.stdout.flush()

def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    access_key = os.environ.get("AWS_ACCESS_KEY_ID", "")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    if not access_key or not secret_key:
        logging.warning("AWS credentials not found — skipping S3 upload")
        return False

    # Upload the file
    s3_client = boto3.client(
    's3',
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    )
    try:
        response = s3_client.upload_file(
                        file_name,
                        bucket,
                        object_name,
                        Callback=ProgressPercentage(file_name))
    except ClientError as e:
        logging.error(e)
        return False
    return True


# bucket_name = "ubo-hw-test-logs"
# upload_file("test_ir_codes.txt", bucket_name)
