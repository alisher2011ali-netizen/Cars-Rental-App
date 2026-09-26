import flet as ft
from core.models import Car, Tenant
from services.connector import Connector
from services.localization import localization


class Builder:
    def __init__(
        self,
        page: ft.Page,
    ):
        self.page = page
        self.prefs = ft.SharedPreferences()
        self.connector = Connector()
        self.current_image_indices = {}

    def _get_nav_bar(self, current_index: int):
        return ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.HOME, label=localization.main_menu
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.CAR_RENTAL, label=localization.cars
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.PERSON, label=localization.tenants
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.KEY, label=localization.rentals
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.ATTACH_MONEY_OUTLINED,
                    label=localization.finances,
                ),
            ],
            selected_index=current_index,
            on_change=self._handle_nav_change,
        )

    async def _handle_nav_change(self, e):
        match e.control.selected_index:
            case 0:
                await self.page.push_route("/")
            case 1:
                await self.page.push_route("/cars")
            case 2:
                await self.page.push_route("/tenants")
            case 3:
                await self.page.push_route("/rentals")
            case 4:
                await self.page.push_route("/finances")

    def _create_car_card(
        self, car: Car, car_images: list[str] | None = None
    ) -> ft.Container:
        car_images = car_images or []
        self.current_image_indices[car.id] = 0

        async def go_to_details(e):
            await self.page.push_route(f"/cars/{car.id}")

        if car_images:
            indicator = ft.Text(
                f"1/{len(car_images)}",
                size=12,
                weight="bold",
                color=ft.Colors.ON_SURFACE_VARIANT,
            )

            image_container = ft.Container(
                content=ft.Image(src=car_images[0]),
                width=300,
                height=200,
                border_radius=8,
            )

            def on_horizontal_drag_update(e: ft.DragUpdateEvent):
                if e.primary_delta > 50:
                    self._prev_image(car.id, car_images, image_container, indicator)
                elif e.primary_delta < -50:
                    self._next_image(car.id, car_images, image_container, indicator)

            image_with_swipe = ft.GestureDetector(
                content=image_container,
                on_horizontal_drag_update=on_horizontal_drag_update,
                on_tap=go_to_details,
            )

        else:
            image_container = ft.Container(
                content=ft.Text(
                    localization.no_images,
                    size=14,
                    weight="bold",
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                width=300,
                height=200,
                bgcolor=ft.Colors.SURFACE_CONTAINER,
                alignment=ft.Alignment.CENTER,
                border_radius=8,
            )
            image_with_swipe = ft.GestureDetector(
                content=image_container,
                on_tap=go_to_details,
            )
            indicator = ft.Text()

        card = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        f"{car.brand} {car.model} ({car.plate_number})",
                        size=16,
                        weight="bold",
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    image_with_swipe,
                    indicator,
                ],
                alignment=ft.Alignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            padding=15,
            border_radius=12,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            on_click=go_to_details,
        )

        return card

    def _next_image(
        self,
        car_id: int,
        images: list[str],
        image_container: ft.Container,
        indicator: ft.Text,
    ):
        if not images:
            return

        current = self.current_image_indices.get(car_id, 0)

        if current < len(images) - 1:
            self.current_image_indices[car_id] = current + 1
            image_container.content.src = images[current + 1]
            image_container.update()

            indicator.value = f"{current + 2}/{len(images)}"
            indicator.update()

    def _prev_image(
        self,
        car_id: int,
        images: list[str],
        image_container: ft.Container,
        indicator: ft.Text,
    ):
        if not images:
            return

        current = self.current_image_indices.get(car_id, 0)
        if current > 0:
            self.current_image_indices[car_id] = current - 1
            image_container.content.src = images[current - 1]
            image_container.update()

            indicator.value = f"{current}/{len(images)}"
            indicator.update()

    def _build_complete_snack_bar(self) -> ft.SnackBar:
        return ft.SnackBar(
            content=ft.Text(localization.added_successfully),
            action=ft.SnackBarAction(label="OK"),
            duration=ft.Duration(seconds=5),
            open=True,
        )

    def _build_not_data_view(
        self,
        title: ft.Control,
        icon: ft.Icon,
        text: str,
        button_text: str,
        button_route: str,
        route: str,
        nav_bar_idx: int,
        fab: ft.FloatingActionButton,
    ) -> ft.Container:
        return ft.View(
            route=route,
            navigation_bar=self._get_nav_bar(nav_bar_idx),
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            title,
                            ft.Container(
                                content=ft.Column(
                                    [
                                        icon,
                                        ft.Text(
                                            text,
                                            size=18,
                                            weight="bold",
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                            align=ft.Alignment.CENTER,
                                        ),
                                        ft.TextButton(
                                            button_text,
                                            icon=ft.Icons.ADD,
                                            on_click=lambda _: self.page.run_task(
                                                self.page.push_route, button_route
                                            ),
                                            align=ft.Alignment.CENTER,
                                        ),
                                    ],
                                ),
                                padding=40,
                                alignment=ft.Alignment.CENTER,
                            ),
                        ]
                    ),
                    alignment=ft.Alignment.CENTER,
                ),
            ],
            floating_action_button=fab,
            floating_action_button_location=ft.FloatingActionButtonLocation.END_FLOAT,
        )

    def _build_fab(self, route: str, text: str) -> ft.FloatingActionButton:
        return ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            on_click=lambda _: self.page.run_task(self.page.push_route, route),
            tooltip=ft.Tooltip(text),
        )

    def _create_tenant_card(self, tenant: Tenant) -> ft.Container:
        def on_phone_number_tap(tenant_phone: str):
            self.page.clipboard.set(tenant_phone)
            snack = ft.SnackBar(localization.copied, open=True)
            self.page.overlay.append(snack)

        if not tenant.avatar:
            avatar = ft.CircleAvatar(
                content=ft.Text(tenant.name[0].upper(), size=50, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.BLUE_GREY_400,
                radius=65,
                expand=False,
            )
        else:
            avatar = ft.CircleAvatar(
                content=ft.Image(src=tenant.avatar.path, align=ft.Alignment.CENTER),
                radius=65,
                expand=False,
            )
        card = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        controls=[
                            ft.Container(
                                ft.Column(
                                    [
                                        ft.Text(
                                            tenant.name[:20],
                                            size=20,
                                            weight="bold",
                                            width=200,
                                        ),
                                        ft.Text(
                                            tenant.phone_number,
                                            size=20,
                                            on_tap=lambda _, phone_number=tenant.phone_number: (
                                                on_phone_number_tap(phone_number)
                                            ),
                                        ),
                                        ft.TextButton(
                                            ft.Text(localization.details, size=16),
                                            on_click=lambda _, t_id: self.page.run_task(
                                                self.page.push_route,
                                                f"/tenants/{t_id}",
                                            ),
                                        ),
                                    ],
                                ),
                            ),
                            avatar,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    )
                ],
                spacing=5,
            ),
            padding=10,
            alignment=ft.Alignment.CENTER_LEFT,
            bgcolor=ft.Colors.GREY_100,
        )
        return card
