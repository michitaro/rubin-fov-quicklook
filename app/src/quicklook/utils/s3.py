import minio


def download_object_from_s3(
    client: minio.Minio,
    bucket: str,
    key: str,
) -> bytes:
    response = None
    try:
        response = client.get_object(
            bucket,
            key,
        )
        return response.read()

    finally:
        if response:  # pragma: no branch
            response.close()
            response.release_conn()
