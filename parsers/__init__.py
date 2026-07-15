from parsers.gdebenz import GdebenzParser
from parsers.pinggi import PinggiParser


def all_parsers():
    """Реестр адаптеров — добавляйте новые источники сюда."""
    return [GdebenzParser(), PinggiParser()]