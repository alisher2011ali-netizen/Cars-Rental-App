import flet as ft

from services.localization import localization
from ui.builders.base import Builder


class FirstLaunchBuilder(Builder):
    def build_first_launch_view(self) -> ft.View:
        def on_language_change(e):
            selected_language = e.control.value
            self.page.shared_preferences.set("language_code", selected_language)
            localization.load_lang(selected_language)

            self.page.views.clear()
            self.page.views.append(self.build_first_launch_view())

        def on_currency_change(e):
            selected_currency = e.control.value
            self.page.shared_preferences.set("currency", selected_currency)
            localization.currency = selected_currency

        content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(
                            icon=ft.Icons.CAR_RENTAL,
                            size=100,
                            color=ft.Colors.PRIMARY,
                            align=ft.Alignment.CENTER,
                        ),
                        ft.Text(
                            localization.app_name,
                            size=28,
                            weight="bold",
                        ),
                    ],
                ),
                ft.Text(
                    localization.hello_text,
                    size=24,
                    weight="bold",
                    text_align="center",
                ),
                ft.Column(
                    [
                        ft.Text(
                            localization.choose_language,
                            size=20,
                            text_align="center",
                        ),
                        ft.Dropdown(
                            options=[
                                ft.DropdownOption(key="ru", text="Русский"),
                                ft.DropdownOption(key="en", text="English"),
                                ft.DropdownOption(key="zh", text="中文"),
                            ],
                            value="ru",
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
                            text_align="center",
                        ),
                        ft.Dropdown(
                            options=[
                                ft.DropdownOption(key="RUB", text="RUB  ₽"),
                                ft.DropdownOption(key="USD", text="USD  $"),
                                ft.DropdownOption(key="CNY", text="CNY  ¥"),
                                ft.DropdownOption(key="KGS", text="KGS"),
                            ],
                            value="RUB",
                            width=200,
                            on_select=on_currency_change,
                        ),
                    ],
                    spacing=5,
                ),
                ft.ElevatedButton(
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

    async def _on_continue(self, e):
        await self.page.shared_preferences.set("is_first_launch", False)
        self.page.go("/cars")
