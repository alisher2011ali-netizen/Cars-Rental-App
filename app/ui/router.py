import logging

import flet as ft
from services.localization import localization
from ui.builders import (
    Builder,
    CarBuilder,
    FinanceBuilder,
    FirstLaunchBuilder,
    HomeBuilder,
    RentalBuilder,
    TenantBuilder,
)

logger = logging.getLogger(__name__)


class UIRouter:
    """Manage application routing, view transitions, and route-level error handling."""

    def __init__(self, page: ft.Page) -> None:
        """Initialize the router with the target root page and view builders.

        Args:
            page (ft.Page): The root page container provided by the Flet runtime.

        Returns:
            None: Initializes router components.
        """
        self.page = page
        self.builder = Builder(self.page)

    async def build(self) -> None:
        """Bootstrap page configurations, register routing handlers, and render the initial view.

        Args:
            None

        Returns:
            None: Asynchronously updates the UI view tree.
        """
        self.page.title = "Cars Rental App"
        self.page.on_route_change = self.route_change
        self.page.navigation_bar = self.builder.get_nav_bar(0)
        try:
            # Check for non-False values to treat an unset preference key (None) as a first-launch event
            if await self.builder.prefs.get("is_first_launch") != False:
                fisrt_launch_builder = FirstLaunchBuilder(self.page)
                await self.builder.prefs.set("is_first_launch", True)
                view = fisrt_launch_builder.build_first_launch_view()

            else:
                home_builder = HomeBuilder(self.page)
                view = home_builder.build_home_view()

        except Exception as ex:
            logger.exception("An error occurred while initializing.")

            view = self._build_error_view(str(ex), "/")
        self.page.views.clear()
        self.page.views.append(view)
        self.page.update()

    def route_change(self, e: ft.RouteChangeEvent) -> None:
        """Resolve route transitions and update the visible page view.

        Args:
            e (ft.RouteChangeEvent): Route change event containing the target URI.

        Returns:
            None: Dispatches route matching and replaces current views.
        """
        troute = ft.TemplateRoute(e.route)

        try:
            # Use regex pattern matching in template routes to safely extract numeric domain IDs
            if troute.match("/cars/:id(\\d+)"):
                car_builder = CarBuilder(self.page)
                view = car_builder.build_car_details_view(int(troute.id))

            elif troute.match("/tenants/:id(\\d+)"):
                tenant_builder = TenantBuilder(self.page)
                view = tenant_builder.build_tenant_details_view(int(troute.id))

            else:
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
            logger.exception(f"An error occurred while changing route to {e.route}.")
            view = self._build_error_view(str(ex), e.route)

        try:
            view.scroll = ft.ScrollMode.AUTO
            self.page.views.clear()
            self.page.views.append(view)
            self.page.update()
        except Exception:
            logger.exception("An error occurred while updating the page.")

    def _build_error_view(self, ex_str: str, route: str) -> ft.View:
        """Construct a standardized fallback view displaying routing or runtime errors.

        Args:
            ex_str (str): String representation of the captured exception.
            route (str): Target navigation route where the failure occurred.

        Returns:
            ft.View: Dedicated error view container presenting failure diagnostics.
        """
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
