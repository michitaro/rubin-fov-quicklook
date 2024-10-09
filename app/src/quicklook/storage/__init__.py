from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import minio

from quicklook.config import config
from quicklook.types import CcdId, Visit
from quicklook.utils.s3 import download_object_from_s3


def s3_get_visit_ccds(visit: Visit, ccd_name: str):
    bucket = config.s3_repository.bucket
    key = f'{visit.data_type}/{visit.name}/{ccd_name}.fits'
    return download_object_from_s3(s3_client(), bucket, key)


@dataclass
class S3CcdObject:
    url: str
    ccd_id: CcdId
    obj: object


def s3_list_visit_ccds(visit: Visit) -> Iterable[S3CcdObject]:
    bucket = config.s3_repository.bucket
    prefix = f'{visit.data_type}/{visit.name}/'
    for obj in s3_client().list_objects(bucket, prefix=prefix):
        yield S3CcdObject(
            url=f'{config.s3_repository.endpoint}/{bucket}/{obj.object_name}',
            ccd_id=CcdId(visit, Path(obj.object_name).stem),  # type: ignore
            obj=obj,
        )


def s3_client():
    s3_config = config.s3_repository
    return minio.Minio(
        s3_config.endpoint[0],
        access_key=s3_config.access_key,
        secret_key=s3_config.secret,
        secure=s3_config.secure,
    )
