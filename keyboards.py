from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from constants import AREAS, FUELS, NETWORKS, STATUSES


def _mark(selected: bool, label: str) -> str:
    return f"{'✅ ' if selected else ''}{label}"


class Keyboards:
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⚙️ Настроить поиск", callback_data="menu:settings")],
                [InlineKeyboardButton(text="📋 Текущий статус", callback_data="menu:status")],
                [
                    InlineKeyboardButton(text="🔔 Уведомления", callback_data="menu:notify"),
                    InlineKeyboardButton(text="❓ Справка", callback_data="menu:help"),
                ],
                [
                    InlineKeyboardButton(text="👥 Пригласить друга", callback_data="menu:invite"),
                    InlineKeyboardButton(text="☕ Поблагодарить", callback_data="menu:donate"),
                ],
            ]
        )

    @staticmethod
    def settings_root() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📍 Районы / города", callback_data="set:area")],
                [InlineKeyboardButton(text="⛽ Топливо", callback_data="set:fuel")],
                [InlineKeyboardButton(text="⚠️ Статусы", callback_data="set:status")],
                [InlineKeyboardButton(text="🏪 Сети АЗС", callback_data="set:network")],
                [InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:main")],
            ]
        )

    @staticmethod
    def captcha(options: list[str]) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=e, callback_data=f"captcha:{i}") for i, e in enumerate(options)]
            ]
        )

    @staticmethod
    def filter_list(
        prefix: str,
        items: list[tuple[str, str]],
        selected: set[str],
        back: str = "menu:settings",
    ) -> InlineKeyboardMarkup:
        rows = [
            [InlineKeyboardButton(text=_mark(k in selected, label), callback_data=f"toggle:{prefix}:{k}")]
            for k, label in items
        ]
        rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data=back)])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    def area_picker(selected: set[str]) -> InlineKeyboardMarkup:
        return Keyboards.filter_list("area", AREAS, selected)

    @staticmethod
    def fuel_picker(selected: set[str]) -> InlineKeyboardMarkup:
        return Keyboards.filter_list("fuel", FUELS, selected)

    @staticmethod
    def status_picker(selected: set[str]) -> InlineKeyboardMarkup:
        return Keyboards.filter_list("status", STATUSES, selected)

    @staticmethod
    def network_picker(selected: set[str]) -> InlineKeyboardMarkup:
        return Keyboards.filter_list("network", NETWORKS, selected)

    @staticmethod
    def back_main() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:main")]]
        )

    @staticmethod
    def push_actions(station_id: str, fuel_key: str) -> InlineKeyboardMarkup:
        enc = station_id.replace(":", "__", 1)
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Была заправка", callback_data=f"push:ok:{enc}:{fuel_key}"),
                    InlineKeyboardButton(text="❌ Уже нет", callback_data=f"push:no:{enc}:{fuel_key}"),
                ],
                [InlineKeyboardButton(text="⏸ Не сейчас (24ч)", callback_data=f"push:snooze:{enc}:{fuel_key}")],
            ]
        )