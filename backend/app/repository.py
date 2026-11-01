from sqlalchemy import select

from app.models import TripRow
from app.schemas.itinerary import StoredTripPayload, TripList, TripSummary


class TripRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    @staticmethod
    def payload(row: TripRow) -> StoredTripPayload:
        return StoredTripPayload.model_validate_json(row.payload_json)

    def save(self, payload: StoredTripPayload) -> StoredTripPayload:
        record = payload.record
        with self.session_factory.begin() as session:
            row = session.get(TripRow, record.id)
            values = {
                "title": record.title,
                "destination_name": record.destination.name,
                "start_date": record.request.start_date.isoformat(),
                "end_date": record.request.end_date.isoformat(),
                "generation_mode": record.generation_mode,
                "version": record.version,
                "payload_json": payload.model_dump_json(),
                "created_at": record.created_at,
                "updated_at": record.updated_at,
            }
            if row is None:
                session.add(TripRow(id=record.id, **values))
            else:
                for key, value in values.items():
                    setattr(row, key, value)
        return payload

    def get(self, trip_id: str) -> StoredTripPayload | None:
        with self.session_factory() as session:
            row = session.get(TripRow, trip_id)
            return self.payload(row) if row else None

    def get_by_idempotency(self, key: str) -> StoredTripPayload | None:
        with self.session_factory() as session:
            for row in session.scalars(select(TripRow)).all():
                payload = self.payload(row)
                if payload.idempotency_key == key:
                    return payload
        return None

    def list(self, limit: int = 50, offset: int = 0) -> TripList:
        with self.session_factory() as session:
            rows = session.scalars(
                select(TripRow).order_by(TripRow.updated_at.desc()).offset(offset).limit(limit)
            ).all()
            total = session.query(TripRow).count()
        return TripList(
            trips=[
                TripSummary(
                    id=row.id,
                    title=row.title,
                    destination_name=row.destination_name,
                    start_date=row.start_date,
                    end_date=row.end_date,
                    generation_mode=row.generation_mode,
                    version=row.version,
                    updated_at=row.updated_at,
                )
                for row in rows
            ],
            total=total,
        )

    def delete(self, trip_id: str) -> bool:
        with self.session_factory.begin() as session:
            row = session.get(TripRow, trip_id)
            if not row:
                return False
            session.delete(row)
            return True
