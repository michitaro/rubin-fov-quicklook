import io
import pickle
from pathlib import Path

import minio
import pytest

from quicklook.config import config
from quicklook.generator.preprocess_ccd import preprocess_ccd
from quicklook.types import CcdId, PreProcessedCcd, Visit
from quicklook.utils.s3 import download_object_from_s3
from quicklook.utils.timeit import timeit



@pytest.fixture(scope='session')
def preprocessed_ccd() -> PreProcessedCcd:
    cache_path = Path('./example/preprocessed_ccd.pkl')
    
    if cache_path.exists():
        return pickle.loads(cache_path.read_bytes())

    s3_config = config.s3_repository
    client = minio.Minio(
        s3_config.endpoint[0],
        access_key=s3_config.access_key,
        secret_key=s3_config.secret,
        secure=s3_config.secure,
    )

    visit = Visit(name='broccoli', data_type='raw')
    
    with timeit('load-fits'):
        file_contents = download_object_from_s3(client, s3_config.bucket, f'raw/broccoli/R00_SG0.fits')
        with timeit('preprocess'):
            ppccd = preprocess_ccd(CcdId(visit, 'R00_SG0'), io.BytesIO(file_contents))

    with timeit('pickle'):
        cache_path.write_bytes(pickle.dumps(ppccd))

    return ppccd
