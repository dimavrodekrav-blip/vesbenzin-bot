from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ParsedStation:
    external_id: str
    name: str
    address: str
    area_key: str
    network_key: str
    lat: float | None = None
    lon: float | None = None


@dataclass
class ParsedStatus:
    station_external_id: str
    fuel_key: str
    status_key: str
    source_status: str = ""
    queue_hint: str = ""
    limit_hint: str = ""


@dataclass
class ParseResult:
    source: str
    stations: list[ParsedStation]
    statuses: list[ParsedStatus]


class SourceParser(ABC):
    """Адаптер источника данных — реализуйте fetch() для каждого сайта/карты."""

    source: str

    @abstractmethod
    async def fetch(self) -> ParseResult:
        ...