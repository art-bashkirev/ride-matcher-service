import asyncio
import unittest
from datetime import datetime, timezone
from typing import cast

from app.telegram.utils import filter_upcoming_departures, ScheduleDisplayItem
from services.yandex_schedules.cached_client import CachedYandexSchedules
from services.yandex_schedules.models.schedule import (
    Schedule,
    ScheduleRequest,
    ScheduleResponse,
    Station,
    Pagination,
)
from services.yandex_schedules.models.thread import Thread
from services.yandex_schedules.models.common import StationType, TransportType


def _make_schedule_item(departure_iso: str, *, arrival_iso: str | None = None) -> Schedule:
    return Schedule(
        except_days=None,
        arrival=arrival_iso,
        thread=Thread(uid="uid", title="Origin - Destination", number="A1"),
        is_fuzzy=False,
        days="daily",
        stops="",
        departure=departure_iso,
        terminal=None,
        platform=None,
    )


def _make_station() -> Station:
    return Station(
        code="s9600000",
        station_type=StationType.STATION,
        station_type_name="Station",
        title="Test Station",
        transport_type=TransportType.TRAIN,
        type="station",
    )


def _make_response(date: str, *schedule_items: Schedule) -> ScheduleResponse:
    return ScheduleResponse(
        date=date,
        pagination=Pagination(total=len(schedule_items), limit=len(schedule_items), offset=0),
        station=_make_station(),
        schedule=list(schedule_items),
    )


class FilterUpcomingDeparturesTests(unittest.TestCase):
    def test_filter_applies_window_and_flags_next_day(self):
        current_time = datetime(2025, 9, 28, 20, 0, tzinfo=timezone.utc)
        schedule_items = [
            _make_schedule_item("2025-09-28T21:00:00+00:00"),
            _make_schedule_item("2025-09-29T00:30:00+00:00"),
            _make_schedule_item("2025-09-29T04:30:00+00:00"),
            _make_schedule_item("2025-09-28T19:30:00+00:00"),
        ]

        filtered = filter_upcoming_departures(schedule_items, current_time=current_time, window_hours=6)

        self.assertEqual(len(filtered), 2)
        self.assertIsInstance(filtered[0], ScheduleDisplayItem)
        self.assertFalse(filtered[0].is_next_day)
        self.assertTrue(filtered[1].is_next_day)

        first_dt_raw = filtered[0].departure_dt
        second_dt_raw = filtered[1].departure_dt
        self.assertIsNotNone(first_dt_raw)
        self.assertIsNotNone(second_dt_raw)

        first_dt = cast(datetime, first_dt_raw)
        second_dt = cast(datetime, second_dt_raw)

        self.assertIsNotNone(first_dt.tzinfo)
        self.assertIsNotNone(second_dt.tzinfo)
        self.assertLess(first_dt, second_dt)


class GetScheduleForDatesTests(unittest.IsolatedAsyncioTestCase):
    async def test_merge_combines_multiple_days(self):
        request_today = ScheduleRequest(
            station="s9600000",
            date="2025-09-28",
            result_timezone="Europe/Moscow",
            limit=100,
        )
        request_tomorrow = request_today.model_copy(update={"date": "2025-09-29"})

        response_today = _make_response(
            "2025-09-28",
            _make_schedule_item("2025-09-28T21:00:00+00:00"),
        )

        response_tomorrow = _make_response(
            "2025-09-29",
            _make_schedule_item("2025-09-29T00:15:00+00:00"),
        )

        responses_by_date = {
            "2025-09-28": (response_today, True),
            "2025-09-29": (response_tomorrow, False),
        }

        async def fake_get_schedule(self, req: ScheduleRequest):
            await asyncio.sleep(0)
            assert req.date is not None
            return responses_by_date[req.date]

        dummy = CachedYandexSchedules.__new__(CachedYandexSchedules)
        dummy.get_schedule = fake_get_schedule.__get__(dummy, CachedYandexSchedules)

        merged_response, cache_flags, source_dates = await CachedYandexSchedules.get_schedule_for_dates(
            dummy,
            [request_today, request_tomorrow],
        )

        self.assertEqual(len(merged_response.schedule), 2)
        self.assertEqual(cache_flags, [True, False])
        self.assertEqual(source_dates, ["2025-09-28", "2025-09-29"])
        self.assertEqual(merged_response.pagination.total, 2)
        self.assertEqual(
            merged_response.schedule[0].departure,
            response_today.schedule[0].departure,
        )
        self.assertEqual(
            merged_response.schedule[1].departure,
            response_tomorrow.schedule[0].departure,
        )


if __name__ == "__main__":
    unittest.main()
