from google.cloud import storage


class GoogleCloudBucket:
    """
    A class that implements the functionality to download a file from a Google bucket with
    an anonymous client.

    Args:
        bucket_name (str): Google bucket ID

    Methods:
        download_blob_into_memory(blob): Reurns the blob from bucket. Blob must be blob from blobs.
    """

    def __init__(self, bucket_name: str):
        self.client = storage.Client.create_anonymous_client()
        self.bucket = self.client.get_bucket(bucket_name)
        self.blobs = list(self.bucket.list_blobs())

    def download_blob_into_memory(self, blob: storage.Blob):
        return self.bucket.get_blob(blob.name).download_as_string()
