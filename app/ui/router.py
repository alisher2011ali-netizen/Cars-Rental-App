import flet as ft
import logging

from ui.builders import (
    Builder,
    HomeBuilder,
    CarBuilder,
    TenantBuilder,
    RentalBuilder,
    FinanceBuilder,
    FirstLaunchBuilder,
)
from services.localization import localization


class UIRouter:
    def __init__(self, page: ft.Page):
        self.page = page
        self.builder = Builder(self.page)

    async def build(self):
        self.page.title = "Cars Rental App"
        self.page.on_route_change = self.route_change
        self.page.navigation_bar = self.builder._get_nav_bar(0)
        try:
            if await self.page.shared_preferences.get("is_first_launch") != False:
                fisrt_launch_builder = FirstLaunchBuilder(self.page)
                await self.page.shared_preferences.set("is_first_launch", True)
                view = fisrt_launch_builder.build_first_launch_view()

            else:
                home_builder = HomeBuilder(self.page)
                view = home_builder.build_home_view()

        except Exception as ex:
            logging.exception("An error occurred while initializing.")

            view = self._build_error_view(str(ex), "/")
        self.page.views.clear()
        self.page.views.append(view)
        self.page.update()

    def route_change(self, e):
        """Handler for route change events. Updates the page view based on the new route.
        :params
        e: RouteChangeEvent"""

        try:
            match e.route:
                case "/":
                    home_builder = HomeBuilder(self.page)
                    view = home_builder.build_home_view()
                case "/first_launch":
                    first_launch_builder = FirstLaunchBuilder(self.page)
                    view = first_launch_builder.build_first_launch_view()
                case "/cars":
                    car_builder = CarBuilder(self.page)
                    view = car_builder.build_cars_view()
                case "/tenants":
                    tenant_builder = TenantBuilder(self.page)
                    view = tenant_builder.build_tenants_view()
                case "/rentals":
                    rental_builder = RentalBuilder(self.page)
                    view = rental_builder.build_rentals_view()
                case "/finances":
                    finance_builder = FinanceBuilder(self.page)
                    view = finance_builder.build_finances_view()
                case "/add_car":
                    car_builder = CarBuilder(self.page)
                    view = car_builder.build_add_car_view()
                case "/add_tenant":
                    tenant_builder = TenantBuilder(self.page)
                    view = tenant_builder.build_add_tenant_view()
                case "/add_rental":
                    rental_builder = RentalBuilder(self.page)
                    view = rental_builder.build_add_rental_view()
                case "/add_payment":
                    finance_builder = FinanceBuilder(self.page)
                    view = finance_builder.build_add_payment_view()
                case _:
                    home_builder = HomeBuilder(self.page)
                    view = home_builder.build_home_view()
        except Exception as ex:
            logging.exception(f"An error occurred while changing route to {e.route}.")
            view = self._build_error_view(str(ex), e.route)

        # Only after we have the view, we try to update the page. This way we avoid clearing the page if view creation fails.
        try:
            view.scroll = ft.ScrollMode.AUTO
            self.page.views.clear()
            self.page.views.append(view)
            self.page.update()
        except Exception as ex:
            logging.exception(f"An error occurred while updating the page: {ex}")

    def _build_error_view(self, ex_str: str, route: str) -> ft.View:
        error_content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        localization.error_loading,
                        size=20,
                        weight="bold",
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
                alignment="center",
                horizontal_alignment="center",
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
