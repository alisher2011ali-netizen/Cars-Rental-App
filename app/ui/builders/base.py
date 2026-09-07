import flet as ft

from core.models import Car
from services.connector import Connector
from services.localization import localization


class Builder:
    def __init__(
        self,
        page: ft.Page,
    ):
        self.page = page
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
            on_change=lambda e: self._handle_nav_change(e.control.selected_index),
        )

    def _handle_nav_change(self, index: int):
        match index:
            case 0:
                self.page.go("/")
            case 1:
                self.page.go("/cars")
            case 2:
                self.page.go("/tenants")
            case 3:
                self.page.go("/rentals")
            case 4:
                self.page.go("/finances")

    def _create_car_card(self, car: Car, car_images: list[str] | None = None):
        car_images = car_images or []
        self.current_image_indices[car.id] = 0

        if car_images:
            image_container = ft.Container(
                content=ft.Image(src=car_images[0]),
                width=300,
                height=200,
            )

            def on_pan_update(e):
                if e.delta_x > 50:
                    self._prev_image(car.id, car_images, image_container)
                elif e.delta_x < -50:
                    self._next_image(car.id, car_images, image_container)

            image_with_swipe = ft.GestureDetector(
                content=image_container,
                on_pan_update=on_pan_update,
            )
            indicator = ft.Text(
                f"1/{len(car_images)}",
                size=12,
                weight="bold",
                color=ft.Colors.BLUE_700,
            )
        else:
            image_container = ft.Container(
                content=ft.Text(
                    localization.no_images,
                    size=14,
                    weight="bold",
                    color=ft.Colors.GREY_700,
                ),
                bgcolor=ft.Colors.GREY_200,
            )
            image_with_swipe = image_container
            indicator = ft.Text(
                localization.no_images,
                size=12,
                weight="bold",
                color=ft.Colors.GREY_700,
            )

        card = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        f"{car.brand} {car.model} ({car.plate_number})",
                        size=14,
                        weight="bold",
                    ),
                    image_with_swipe,
                    indicator,
                ],
                alignment=ft.Alignment.CENTER,
                horizontal_alignment=ft.Alignment.CENTER,
                spacing=10,
            ),
            padding=15,
            border_radius=12,
            bgcolor=ft.Colors.GREY_100,
        )

        card.image_container = image_container
        card.indicator = indicator
        card.car_images = car_images

        return card

    def _next_image(
        self, car_id: int, images: list[str], image_container: ft.Container
    ):
        if not images:
            return
        if car_id not in self.current_image_indices:
            self.current_image_indices[car_id] = 0

        current = self.current_image_indices[car_id]
        if current < len(images) - 1:
            self.current_image_indices[car_id] += 1
            image_container.content = ft.Image(
                src_base64=images[self.current_image_indices[car_id]]
            )
            image_container.update()

    def _prev_image(
        self, car_id: int, images: list[str], image_container: ft.Container
    ):
        if not images:
            return
        if car_id not in self.current_image_indices:
            self.current_image_indices[car_id] = 0

        current = self.current_image_indices[car_id]
        if current > 0:
            self.current_image_indices[car_id] -= 1
            image_container.content = ft.Image(
                src_base64=images[self.current_image_indices[car_id]]
            )
            image_container.update()

    def _build_complete_snack_bar(self) -> ft.SnackBar:
        return ft.SnackBar(
            content=ft.Text(localization.added_successfully),
            action=ft.SnackBarAction(label="OK"),
            duration=ft.Duration(seconds=5),
            open=True,
        )

    def _build_not_data_container(
        self, icon: ft.Icon, text: str, button_text: str, route: str
    ) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    icon,
                    ft.Text(
                        text,
                        size=18,
                        weight="bold",
                        color=ft.Colors.BLACK_87,
                        align=ft.Alignment.CENTER,
                    ),
                    ft.TextButton(
                        button_text,
                        icon=ft.Icons.ADD,
                        on_click=lambda _: self.page.go(route),
                        align=ft.Alignment.CENTER,
                    ),
                ],
            ),
            padding=40,
            alignment=ft.Alignment.CENTER,
        )

    def _build_fab(self, route: str, text: str) -> ft.FloatingActionButton:
        return ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            on_click=lambda e: self.page.go(route),
            tooltip=ft.Tooltip(text),
        )

    def _build_placeholder_view(
        self,
        route: str,
        title: str,
        description: str,
        nav_index: int,
    ) -> ft.View:
        content = ft.Column(
            [
                ft.Text(title, size=24, weight="bold"),
                ft.Text(description, size=16, color=ft.Colors.GREY_700),
            ],
            alignment=ft.Alignment.CENTER,
            horizontal_alignment=ft.Alignment.CENTER,
            spacing=20,
        )

        return ft.View(
            route=route,
            navigation_bar=self._get_nav_bar(nav_index),
            controls=[
                ft.Container(
                    content=content,
                    padding=40,
                    bgcolor=ft.Colors.WHITE,
                    width=self.page.width,
                    height=self.page.height - 80,
                    alignment=ft.Alignment.CENTER,
                )
            ],
        )
