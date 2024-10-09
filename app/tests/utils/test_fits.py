import logging
from pathlib import Path

import astropy.io.fits as afits
import pytest

from quicklook.utils.fits import stride_fits
from quicklook.utils.timeit import timeit


def test_stride_fits(example_ccd: tuple[Path, str]):
    path, ccd = example_ccd

    with timeit('stride_fits', loglevel=logging.INFO):

        def select(h: afits.Header):
            extname: str | None = h.get('EXTNAME')  # type: ignore
            if extname is not None:
                return extname.startswith('Segment')
            return False

        ranges = stride_fits(path, select)
        assert len(ranges) == 16
