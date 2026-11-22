import flet as ft
from services.localization import localization
from ui.builders.base import Builder


class SettingsBuilder(Builder):
    """Build the settings view covering language, currency, theme and data options."""

    def __init__(self, page: ft.Page) -> None:
        super().__init__(page)

    def build_settings_view(self) -> ft.View:
        """Construct the settings view with grouped preference blocks.

        Returns:
            ft.View: Settings view with a global navigation bar.
        """

        async def on_language_change(e: ft.ControlEvent) -> None:
            selected_language = e.control.value
            await self.prefs.set("language_code", selected_language)
            localization.language = selected_language
            localization.load_lang(selected_language)

            # Rebuild the current view immediately so the newly loaded translation strings take effect across all labels
            self.page.views.clear()
            self.page.views.append(self.build_settings_view())

        async def on_currency_change(e: ft.ControlEvent) -> None:
            selected_currency = e.control.value
            await self.prefs.set("currency", selected_currency)
            localization.currency = selected_currency
            localization.currency = selected_currency

        title = ft.AppBar(
            leading=ft.Icon(
                icon=ft.Icons.SETTINGS,
                size=40,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            title=ft.Text(
                localization.settings,
                size=30,
                weight=ft.FontWeight.BOLD,
            ),
        )

        content = ft.Column(
            [
                title,
                ft.Column(
                    [
                        ft.Text(
                            localization.word_language,
                            size=20,
                            text_align=ft.Alignment.CENTER,
                        ),
                        ft.Dropdown(
                            options=[
                                ft.DropdownOption(key="ru", text="Русский"),
                                ft.DropdownOption(key="en", text="English"),
                                ft.DropdownOption(key="zh", text="中文"),
                            ],
                            value=localization.language,
                            width=200,
                            on_select=on_language_change,
                        ),
                    ],
                    spacing=5,
                ),
                ft.Column(
                    [
                        ft.Text(
                            localization.word_currency,
                            size=20,
                            text_align=ft.Alignment.CENTER,
                        ),
                        ft.Dropdown(
                            options=[
                                ft.DropdownOption(key="₽", text="RUB ₽"),
                                ft.DropdownOption(key="$", text="USD $"),
                                ft.DropdownOption(key="¥", text="CNY ¥"),
                                ft.DropdownOption(key="KGS", text="KGS"),
                            ],
                            value=localization.currency,
                            width=200,
                            on_select=on_currency_change,
                        ),
                    ],
                    spacing=5,
                ),
            ],
            alignment=ft.Alignment.CENTER,
            horizontal_alignment=ft.Alignment.CENTER,
            spacing=20,
        )

        return ft.View(
            route="/settings",
            navigation_bar=self.get_nav_bar(4),
            controls=[
                ft.Container(content=content, padding=20),
            ],
        )
