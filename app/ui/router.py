import logging

import flet as ft
from services.localization import localization
from ui.builders import (
    Builder,
    CarBuilder,
    FinanceBuilder,
    RentalBuilder,
    SettingsBuilder,
    TenantBuilder,
    WelcomeBuilder,
)

logger = logging.getLogger(__name__)


class UIRouter:
    """Manage application routing, view transitions, and route-level error handling."""

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.builder = Builder(self.page)
        self.ROOT_ROUTES = {
            "/welcome",
            "/cars",
            "/tenants",
            "/rentals",
            "/finances",
            "/settings",
        }

    async def build(self) -> None:
        """Bootstrap page configurations, register routing handlers, and render the initial view."""

        self.page.title = "Cars Rental App"
        self.page.on_route_change = self.route_change
        self.page.navigation_bar = self.builder.get_nav_bar(0)
        try:
            # Check for non-False values to treat an unset preference key (None) as a first-launch event
            if await self.builder.prefs.get("is_first_launch") != False:
                fisrt_launch_builder = WelcomeBuilder(self.page)
                await self.builder.prefs.set("is_first_launch", True)
                view = fisrt_launch_builder.build_first_launch_view()

            else:
                view = RentalBuilder(self.page).build_rentals_view()

        except Exception as ex:
            logger.exception("An error occurred while initializing.")

            view = self._build_error_view(str(ex), "/")
        self.page.views.clear()
        self.page.views.append(view)
        self.page.update()

    def route_change(self, e: ft.RouteChangeEvent) -> None:
        """Catch route transitions and update the visible page view."""

        if self.page.views and self.page.views[-1].route == e.route:
            self.page.update()
            return

        troute = ft.TemplateRoute(e.route)
        is_root_route = e.route in self.ROOT_ROUTES

        try:
            if troute.match("/cars/:id(\\d+)"):
                view = CarBuilder(self.page).build_car_details_view(int(troute.id))
            elif troute.match("/tenants/:id(\\d+)"):
                view = TenantBuilder(self.page).build_tenant_details_view(
                    int(troute.id)
                )
            elif troute.match("/rentals/:id(\\d+)"):
                view = RentalBuilder(self.page).build_rental_details_view(
                    int(troute.id)
                )
            else:
                match e.route:
                    case "/welcome":
                        view = WelcomeBuilder(self.page).build_welcome_view()
                    case "/settings":
                        view = SettingsBuilder(self.page).build_settings_view()
                    case "/cars":
                        view = CarBuilder(self.page).build_cars_view()
                    case "/tenants":
                        view = TenantBuilder(self.page).build_tenants_view()
                    case "/rentals":
                        view = RentalBuilder(self.page).build_rentals_view()
                    case "/finances":
                        view = FinanceBuilder(self.page).build_finances_view()
                    # Экраны создания записей (вложенные)
                    case "/add_car":
                        view = CarBuilder(self.page).build_add_car_view()
                    case "/add_tenant":
                        view = TenantBuilder(self.page).build_add_tenant_view()
                    case "/add_rental":
                        view = RentalBuilder(self.page).build_add_rental_view()
                    case "/add_payment":
                        view = FinanceBuilder(self.page).build_add_payment_view()
                    case _:
                        is_root_route = True
                        view = RentalBuilder(self.page).build_rentals_view()
        except Exception as ex:
            logger.exception(f"An error occurred while changing route to {e.route}.")
            view = self._build_error_view(str(ex), e.route)

        try:
            view.route = e.route  # Обязательно сохраняем маршрут внутри самого View
            view.scroll = ft.ScrollMode.AUTO

            # Если перешли на вкладку нижнего меню — очищаем историю,
            # иначе — кладем новый экран поверх предыдущего в стек
            if is_root_route:
                self.page.views.clear()

            self.page.views.append(view)
            self.page.update()
        except Exception:
            logger.exception("An error occurred while updating the page.")

    def view_pop(self, e: ft.ViewPopEvent) -> None:
        """Handle Android system Back button / edge swipe."""
        if len(self.page.views) > 1:
            self.page.views.pop()
            top_view = self.page.views[-1]
            self.page.go(top_view.route)

    def _build_error_view(self, ex_str: str, route: str) -> ft.View:
        """Build the error view with information about exception."""

        error_content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        localization.error_loading,
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED,
                    ),
                    ft.Text(
                        f"{localization.route}: {route}",
                        size=12,
                        color=ft.Colors.BLACK_87,
                    ),
                    ft.Text(
                        f"{localization.error}: {ex_str}",
                        size=12,
                        color=ft.Colors.RED_800,
                    ),
                ],
                alignment=ft.Alignment.CENTER,
                horizontal_alignment=ft.MainAxisAlignment.CENTER,
                spacing=15,
            ),
            padding=40,
            bgcolor=ft.Colors.WHITE,
            expand=True,
        )
        return ft.View(
            route="/error",
            controls=[error_content],
        )
