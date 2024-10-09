import asyncio
import traceback
from functools import cache
from typing import Annotated

import aiohttp
import numpy
from fastapi import APIRouter, Depends, HTTPException, Response

from quicklook.config import config
from quicklook.coordinator.quicklook import Quicklook
from quicklook.deps.visit_from_path import visit_from_path
from quicklook.frontend.api.remotequicklook import remote_quicklook
from quicklook.tileinfo import TileInfo
from quicklook.types import GeneratorPod, Visit
from quicklook.utils import zstd
from quicklook.utils.numpyutils import ndarray2npybytes, npybytes2ndarray

router = APIRouter()


@router.get('/api/quicklooks/{id}/tiles/{z}/{y}/{x}')
async def get_tile(
    visit: Annotated[Visit, Depends(visit_from_path)],
    z: int,
    y: int,
    x: int,
) -> Response:
    ql = remote_quicklook(visit)
    if ql is None:
        raise HTTPException(status_code=404, detail='Quicklook not found')
    return await gather_tiles(ql, visit, z, y, x)
    # if ql.phase == 'ready':
    #     raise NotImplementedError(f'Phase {ql.phase} not implemented')
    # elif ql.phase == 'processing' and ql.transferreing_progress:
    #     return await gather_tiles(visit, z, y, x)
    raise HTTPException(status_code=503, detail='Quicklook is not ready')


async def gather_tiles(ql: Quicklook, visit: Visit, z: int, y: int, x: int) -> Response:
    ccd_generator_map = ql.ccd_generator_map

    if ccd_generator_map is None:  # pragma: no cover
        raise HTTPException(status_code=503, detail='Quicklook is not ready')

    ccd_names = TileInfo.of(z, y, x).ccd_names
    generators = set(ccd_generator_map[ccd_name] for ccd_name in ccd_names if ccd_name in ccd_generator_map)

    async def get_npy(generator: GeneratorPod) -> numpy.ndarray:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://{generator.name}/quicklooks/{visit.id}/tiles/{z}/{y}/{x}') as response:
                response.raise_for_status()
                return npybytes2ndarray(await response.read())

    pool: numpy.ndarray | None = None
    for fut in asyncio.as_completed([get_npy(g) for g in generators]):
        try:
            arr = await fut
        except:  # pragma: no cover
            traceback.print_exc()
            continue
        if pool is None:
            pool = arr
        else:
            pool += arr
    if pool is not None:
        return Response(ndarray2npybytes(pool), media_type='application/npy')
    return Response(blank_npy_zstd(), media_type='application/npy+zstd')


@cache
def blank_npy_zstd():
    arr = numpy.zeros((config.tile_size, config.tile_size), dtype=numpy.float32)
    return zstd.compress(ndarray2npybytes(arr))
