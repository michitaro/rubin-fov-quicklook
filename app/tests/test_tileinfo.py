import pytest

from quicklook.tileinfo import TileInfo

# pytestmark = pytest.mark.focus


def test_tileinfo():
    ti = TileInfo.of(7, 0, 0)
    assert len([*ti.ccd_names]) == 59
