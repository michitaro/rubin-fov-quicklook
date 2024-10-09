import asyncio
from dataclasses import asdict

import aiohttp
from fastapi import APIRouter

from quicklook.coordinator.api.generators import get_generators
from quicklook.coordinator.quicklook import Quicklook
from quicklook.coordinator.tasks import GeneratorTask, make_generator_tasks
from quicklook.db import db_context
from quicklook.generator.progress import GeneratorProgress
from quicklook.types import MessageFromGeneratorToCoordinator
from quicklook.utils.message import message_from_async_reader

router = APIRouter()


async def run_next_job():
    with db_context() as db:
        ql = Quicklook.dequeue(db)
    if ql:  # pragma: no branch
        await run_generators(ql)
        await run_transfers(ql)
        ql.phase = 'ready'
        ql.notify()
        with db_context() as db:
            ql.save(db)


async def run_generators(ql: Quicklook):
    visit = ql.visit
    nodes: dict[str, GeneratorProgress] = {}
    tasks = make_generator_tasks(visit, get_generators())
    assert len(get_generators()) > 0
    ql.ccd_generator_map = tasks[0].ccd_generator_map

    async def run_1_generator(task: GeneratorTask):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'http://{task.generator.host}:{task.generator.port}/quicklooks',
                json=asdict(task),
                raise_for_status=True,
            ) as res:

                async def reader(n: int):
                    return await res.content.readexactly(n)

                while True:
                    msg: MessageFromGeneratorToCoordinator = await message_from_async_reader(reader)
                    match msg:
                        case None:
                            break
                        case BaseException():
                            raise msg
                        case GeneratorProgress():
                            nodes[task.generator.name] = msg
                            ql.generating_progress = nodes
                            ql.notify()
                        case _:
                            raise TypeError(f'Unexpected message: {msg}')

    await asyncio.gather(*[run_1_generator(task) for task in tasks])


async def run_transfers(ql: Quicklook): ...
