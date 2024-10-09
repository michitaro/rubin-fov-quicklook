import io
import multiprocessing
import multiprocessing.pool
from dataclasses import dataclass
from multiprocessing.shared_memory import SharedMemory
from pathlib import Path
from typing import Any, Callable

import astropy.io.fits as afits
import numpy


def preload_afits_compression_code():
    # このコードを１度実行しておくと以降の展開が速くなる。
    # ベンチマーク用
    hdu = afits.CompImageHDU(numpy.array([[0.0]]))
    hdu.writeto(io.BytesIO(), output_verify='fix')


@dataclass
class HduPosition:
    hdu_index: int
    start: int
    end: int


def stride_fits(path: Path, select: Callable[[afits.Header], bool] | None = None):
    ranges: list[HduPosition] = []
    start = 0
    hdu_index = 0
    with open(path, 'rb') as f:
        while True:
            try:
                header = afits.Header.fromfile(f)
            except EOFError:
                break
            next_offset = f.tell() + header.data_size_padded
            if select is None or select(header):
                ranges.append(HduPosition(hdu_index, start, next_offset))
            f.seek(next_offset)
            start = next_offset
            hdu_index += 1
    return ranges
