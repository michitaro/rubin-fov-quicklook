import asyncio
from contextlib import contextmanager
from dataclasses import dataclass
from functools import cache
from typing import AsyncGenerator, Iterable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from quicklook.models import QuicklookRecord
from quicklook.types import GeneratorPod, GeneratorProgress, Visit
from quicklook.utils.broadcastqueue import BroadcastQueue
from quicklook.utils.event import WatchEvent


@dataclass
class Quicklook:
    # Quicklookを表すクラス
    # DBのラッパー

    visit: Visit
    phase: QuicklookRecord.Phase
    ccd_generator_map: dict[str, GeneratorPod] | None = None
    generating_progress: dict[str, GeneratorProgress] | None = None
    transferreing_progress: dict[str, GeneratorProgress] | None = None

    @classmethod
    def records(cls, db: Session) -> Iterable[QuicklookRecord]:
        stmt = select(QuicklookRecord)
        return db.execute(stmt).scalars().all()

    @classmethod
    def enqueue(cls, db: Session, visit: Visit):
        stmt = select(QuicklookRecord).filter(QuicklookRecord.id == visit.id)
        r = db.execute(stmt).scalar_one_or_none()
        if r is None:  # pragma: no branch
            r = QuicklookRecord(id=visit.id, phase='queued')
            db.add(r)
            db.commit()

    @classmethod
    def dequeue(cls, db: Session):
        stmt = select(QuicklookRecord).filter(QuicklookRecord.phase == 'queued').order_by(QuicklookRecord.created_at)
        with db:
            r = db.execute(stmt).scalar_one_or_none()
            if r:  # pragma: no branch
                ql = cls.from_record(r)
                ql.phase = 'processing'
                ql.save(db)
                return ql

    @classmethod
    def from_record(cls, r: QuicklookRecord) -> 'Quicklook':
        return cls._manager().from_record(r)

    @classmethod
    async def delete_all(cls, db: Session):
        records = cls.records(db)
        for r in records:
            ql = cls.from_record(r)
            ql.delete(db)

    @classmethod
    def get(cls, db: Session, visit: Visit):
        stmt = select(QuicklookRecord).filter(QuicklookRecord.id == visit.id)
        r = db.execute(stmt).scalar_one_or_none()
        if r:  # pragma: no branch
            return cls.from_record(r)

    @classmethod
    @cache
    def _manager(cls) -> '_QuicklookManager':
        return _QuicklookManager()

    @classmethod
    def subscribe(cls) -> AsyncGenerator[list[WatchEvent['Quicklook']], None]:
        return cls._manager().subscribe()

    def save(self, db: Session) -> None:
        stmt = select(QuicklookRecord).filter(QuicklookRecord.id == self.visit.id)
        r = db.execute(stmt).scalar_one()
        r.phase = self.phase
        db.commit()

    @property
    def id(self):
        return self.visit.id

    def notify(self):
        self._manager().notify_modified(self)

    def delete(self, db: Session):
        stmt = delete(QuicklookRecord).filter(QuicklookRecord.id == self.visit.id)
        db.execute(stmt)
        db.commit()
        self._manager().unregister(self)

    @classmethod
    @contextmanager
    def enable_subscription(cls):
        yield


@dataclass
class CacheEntry:
    ql: Quicklook


class _QuicklookManager:
    def __init__(self):
        self._entries: dict[Visit, CacheEntry] = {}
        self._event_queue = BroadcastQueue[WatchEvent[Quicklook]]()

    def unregister(self, ql: Quicklook):
        self._entries.pop(ql.visit)
        self._event_queue.put(WatchEvent(ql, 'deleted'))

    def has(self, visit: Visit):
        return visit in self._entries

    def notify_modified(self, ql: Quicklook):
        self._event_queue.put(WatchEvent(ql, 'modified'))

    def from_record(self, r: QuicklookRecord) -> Quicklook:
        visit = Visit.from_id(r.id)
        if visit not in self._entries:
            ql = Quicklook(visit=visit, phase=r.phase)
            self._entries[visit] = CacheEntry(ql)
            self._event_queue.put(WatchEvent(ql, 'added'))
        return self._entries[visit].ql

    async def subscribe(self) -> AsyncGenerator[list[WatchEvent[Quicklook]], None]:
        yield [WatchEvent(e.ql, 'added') for e in self._entries.values()]
        with self._event_queue.subscribe() as events:
            while True:
                yield [await events.get()]
