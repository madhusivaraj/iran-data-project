import boto3
import datetime
import logging
from threading import RLock

class S3DocumentStore(object):

    def __init__(self, code_tracker, aws_session, bucket_name="iran-article-html"):
        self.logger = logging.getLogger(__name__).getChild(repr(self))

        self.bucket_name = bucket_name
        self.code_tracker = code_tracker
        # Any clients created from this session will use credentials
        # from the [default] section of ~/.aws/credentials.
        self.s3 = aws_session.resource('s3')

        self.lock = RLock()

    # Not really necessary, useful for debugging
    def get(self, code):
        pass

    # Failed to fetch article, probably because of network issue
    def put_error(self, code, reason):
        with self.lock:
            self.code_tracker.put_error(code)

    def put(self, code, document, is_old):
        with self.lock:
            if document is None:
                key = self.get_s3_filename(code, new=(not is_old), empty=True)
                self.put_s3(key, '')
            else:
                key = self.get_s3_filename(code, new=(not is_old))
                self.put_s3(key, document)

    def put_s3(self, key, body):
        with self.lock:
            self.s3.Bucket(self.bucket_name).put_object(Key=key, Body=body)

    def get_s3_filename(self, code, new=True, empty=False):
        with self.lock:
            filename = datetime.datetime.today().strftime('%Y-%m-%d-%H') + "/"
            if empty:
                filename += "empty/"
            if new:
                filename += "new/"
            else:
                filename += "old/"
            filename += str(code) + ".html"
            return filename

    def next_code(self):
        with self.lock:
            return self.code_tracker.next_code()
