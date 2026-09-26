import flet as ft
from services.localization import localization
from ui.builders.base import Builder


class FirstLaunchBuilder(Builder):
    """Build the initial setup and onboarding view for first-time application launches."""

    def __init__(self, page: ft.Page) -> None:
        """Initialize the onboarding builder with default language and currency configurations.

        Args:
            page (ft.Page): The root page container provided by the Flet runtime.

        Returns:
            None: Sets initial state for language and currency selections.
        """
        super().__init__(page)
        self.language = "ru"
        self.currency = "RUB"

    def build_first_launch_view(self) -> ft.View:
        """Construct the first-launch onboarding view with language and currency selectors.

        Args:
            None

        Returns:
            ft.View: View control housing the onboarding form elements.
        """

        def on_language_change(e: ft.ControlEvent) -> None:
            """Update selected language, persist choice, and reload the active view.

            Args:
                e (ft.ControlEvent): Selection event emitted by the language dropdown.

            Returns:
                None: Re-renders the onboarding view with updated localization strings.
            """
            selected_language = e.control.value
            self.prefs.set("language_code", selected_language)
            self.language = selected_language
            localization.load_lang(selected_language)

            # Rebuild the current view immediately so the newly loaded translation strings take effect across all labels
            self.page.views.clear()
            self.page.views.append(self.build_first_launch_view())

        def on_currency_change(e: ft.ControlEvent) -> None:
            """Update and persist the preferred transaction display currency.

            Args:
                e (ft.ControlEvent): Selection event emitted by the currency dropdown.

            Returns:
                None: Updates local and global localization state in-place.
            """
            selected_currency = e.control.value
            self.prefs.set("currency", selected_currency)
            self.currency = selected_currency
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
                            value=self.language,
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
                                ft.DropdownOption(key="RUB", text="RUB  ₽"),
                                ft.DropdownOption(key="USD", text="USD  $"),
                                ft.DropdownOption(key="CNY", text="CNY  ¥"),
                                ft.DropdownOption(key="KGS", text="KGS"),
                            ],
                            value=self.currency,
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
        """Mark onboarding as complete and route the user to the main vehicle catalog.

        Args:
            e (ft.ControlEvent): Action button click event.

        Returns:
            None: Persists state flag and asynchronously triggers navigation.
        """
        await self.prefs.set("is_first_launch", False)
        await self.page.push_route("/cars")
