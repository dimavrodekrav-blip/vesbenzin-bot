"""
Парсер gdebenz.ru.

Публичного стабильного API нет — здесь заготовка под HTTP-разбор.
Для разработки отдаёт демо-точки по Москве/МО, чтобы тестировать push и меню.
Когда найдём рабочий endpoint — дописываем fetch_live().
"""

import aiohttp

from config import logger
from parsers.base import ParseResult, ParsedStation, ParsedStatus, SourceParser
from services.status_mapper import normalize_status

AREA_BY_NETWORK = {
    "lukoil": "msk_cao",
    "rosneft": "msk_south",
    "gpn": "mo_balashiha",
    "tatneft": "msk_west",
    "other": "mo_khimki",
}


class GdebenzParser(SourceParser):
    source = "gdebenz"

    async def fetch(self) -> ParseResult:
        live = await self._fetch_live()
        if live.stations:
            return live
        return self._demo_data()

    async def _fetch_live(self) -> ParseResult:
        # TODO: подключить реальный endpoint, когда будет найден/согласован
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                async with session.get("https://gdebenz.ru/api/stations") as resp:
                    if resp.status != 200:
                        return ParseResult(self.source, [], [])
                    data = await resp.json()
                    return self._parse_json(data)
        except Exception as exc:
            logger.debug("gdebenz live fetch skipped: %s", exc)
            return ParseResult(self.source, [], [])

    def _parse_json(self, data: object) -> ParseResult:
        # Заготовка под будущий формат
        return ParseResult(self.source, [], [])

    def _demo_data(self) -> ParseResult:
        stations = [
            ParsedStation("luk-tverskaya", "Лукойл", "ул. Тверская, 12", "msk_cao", "lukoil", 55.757, 37.611),
            ParsedStation("rn-varshavka", "Роснефть", "Варшавское ш., 87", "msk_south", "rosneft", 55.652, 37.620),
            ParsedStation("gpn-mkad32", "Газпромнефть", "МКАД, 32 км", "mo_balashiha", "gpn", 55.700, 37.500),
            ParsedStation("tn-skhodnya", "Татнефть", "г. Химки, Ленинградское ш.", "mo_khimki", "tatneft", 55.889, 37.430),
        ]
        statuses = [
            ParsedStatus("luk-tverskaya", "ai95", normalize_status("есть"), "есть", queue_hint="до 5 машин"),
            ParsedStatus("luk-tverskaya", "ai92", normalize_status("лимит"), "лимит", limit_hint="20 л"),
            ParsedStatus("rn-varshavka", "ai95", normalize_status("нет"), "нет"),
            ParsedStatus("rn-varshavka", "dt", normalize_status("очередь"), "очередь", queue_hint="15–20 мин"),
            ParsedStatus("gpn-mkad32", "ai92", normalize_status("есть"), "есть"),
            ParsedStatus("gpn-mkad32", "ai95", normalize_status("есть"), "есть", queue_hint="свободно"),
            ParsedStatus("tn-skhodnya", "ai95", normalize_status("мало"), "мало", limit_hint="осталось мало"),
        ]
        return ParseResult(self.source, stations, statuses)