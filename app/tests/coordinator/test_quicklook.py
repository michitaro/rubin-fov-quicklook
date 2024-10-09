import asyncio

from quicklook.coordinator.quicklook import Quicklook
from quicklook.db import db_context
from quicklook.models import QuicklookRecord
from quicklook.utils.event import WatchEvent
import pytest


async def test_quicklook_subscribe():
    events: list[WatchEvent[Quicklook]] = []
    gather_ready = asyncio.Event()
    generate_done = asyncio.Event()

    async def gather_events():
        nonlocal events
        async for _ in Quicklook.subscribe():
            gather_ready.set()
            events = [*events, *_]
            if len(_) > 0 and _[-1].type == 'deleted':
                break

    async def generate_events():
        await gather_ready.wait()
        ql = Quicklook.from_record(QuicklookRecord(id='raw:broccoli', phase='ready'))
        ql.notify()
        with db_context() as db:
            ql.delete(db)

    async with asyncio.TaskGroup() as tg:
        tg.create_task(gather_events())
        tg.create_task(generate_events())

    assert len(events) == 3
