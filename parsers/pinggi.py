"""Парсер pinggi.ru (бэкенд «Где бензин?» / benzrf.ru)."""

import aiohttp

from config import logger
from parsers.base import ParseResult, ParsedStation, ParsedStatus, SourceParser
from services.status_mapper import normalize_status


class PinggiParser(SourceParser):
    source = "pinggi"

    async def fetch(self) -> ParseResult:
        live = await self._fetch_live()
        if live.stations:
            return live
        return self._demo_data()

    async def _fetch_live(self) -> ParseResult:
        # TODO: подключить реальный endpoint pinggi.ru после реверса API
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=25)) as session:
                async with session.get("https://pinggi.ru/api/stations") as resp:
                    if resp.status != 200:
                        return ParseResult(self.source, [], [])
                    data = await resp.json()
                    return self._parse_json(data)
        except Exception as exc:
            logger.debug("pinggi live fetch skipped: %s", exc)
            return ParseResult(self.source, [], [])

    def _parse_json(self, data: object) -> ParseResult:
        return ParseResult(self.source, [], [])

    def _demo_data(self) -> ParseResult:
        stations = [
            ParsedStation(
                "pg-kashirka",
                "Независимая АЗС",
                "Каширское ш., 23",
                "msk_south",
                "other",
                55.655,
                37.705,
            ),
            ParsedStation(
                "pg-volgogradka",
                "Лукойл",
                "Волгоградский пр-т, 45",
                "msk_south",
                "lukoil",
                55.708,
                37.748,
            ),
        ]
        statuses = [
            ParsedStatus("pg-kashirka", "ai92", normalize_status("есть"), "есть"),
            ParsedStatus(
                "pg-volgogradka",
                "ai95",
                normalize_status("есть"),
                "есть",
                queue_hint="до 10 машин",
            ),
        ]
        return ParseResult(self.source, stations, statuses)