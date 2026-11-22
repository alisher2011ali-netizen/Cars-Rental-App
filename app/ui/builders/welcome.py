import flet as ft
from services.localization import localization
from ui.builders.base import Builder


class WelcomeBuilder(Builder):
    """Build UI views for WELCOME SCREEN."""

    def __init__(self, page: ft.Page) -> None:
        super().__init__(page)

    def build_welcome_view(self) -> ft.View:
        def on_language_change(e: ft.ControlEvent) -> None:
            selected_language = e.control.value
            self.prefs.set("language_code", selected_language)
            localization.language = selected_language
            localization.load_lang(selected_language)

            # Rebuild the current view immediately so the newly loaded translation strings take effect across all labels
            self.page.views.clear()
            self.page.views.append(self.build_welcome_view())

        def on_currency_change(e: ft.ControlEvent) -> None:
            selected_currency = e.control.value
            self.prefs.set("currency", selected_currency)
            localization.currency = selected_currency
            localization.currency = selected_currency

        content = ft.Column(
            [
                ft.AppBar(
                    leading=ft.Icon(
                        icon=ft.Icons.CAR_RENTAL,
                        size=100,
                        align=ft.Alignment.CENTER,
                    ),
                    title=ft.Text(
                        localization.app_name,
                        size=28,
                        weight=ft.FontWeight.BOLD,
                    ),
                ),
                ft.Text(
                    localization.hello_text,
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.Alignment.CENTER,
                ),
                ft.Column(
                    [
                        ft.Text(
                            localization.choose_language,
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
                            localization.choose_currency,
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
                ft.Button(
                    ft.Text(localization.continue_text, size=20),
                    icon=ft.Icon(ft.Icons.ARROW_FORWARD, size=20),
                    align=ft.Alignment.CENTER,
                    on_click=self._on_continue,
                ),
            ],
            alignment=ft.Alignment.CENTER,
            horizontal_alignment=ft.Alignment.CENTER,
            spacing=20,
        )
        return ft.View(
            route="/first_launch", controls=[content], scroll=ft.ScrollMode.AUTO
        )

    async def _on_continue(self, e: ft.ControlEvent) -> None:
        await self.prefs.set("is_first_launch", False)
        await self.page.push_route("/cars")
