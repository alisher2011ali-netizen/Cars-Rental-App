import flet as ft
from services.localization import localization
from ui.builders.base import Builder


class HomeBuilder(Builder):
    def build_home_view(self) -> ft.View:
        last_added_cars, images_dict = self.connector.get_last_added_cars()

        title = ft.AppBar(
            title=ft.Text(
                localization.app_name,
                size=40,
                weight="bold",
            )
        )

        if not last_added_cars:
            message = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(
                            ft.Icons.HOME_FILLED,
                            size=60,
                            color=ft.Colors.GREY_400,
                            align=ft.Alignment.CENTER,
                        ),
                        ft.Text(
                            localization.empty_home_message,
                            size=18,
                            width=400,
                            align=ft.Alignment.CENTER,
                        ),
                    ],
                    align=ft.Alignment.CENTER,
                    spacing=5,
                )
            )

            content = ft.Column(
                [
                    title,
                    message,
                ],
                alignment=ft.Alignment.TOP_CENTER,
                horizontal_alignment=ft.Alignment.CENTER,
                spacing=20,
            )

            return ft.View(
                route="/",
                navigation_bar=self._get_nav_bar(0),
                controls=[
                    ft.Container(
                        content=content,
                        padding=5,
                    )
                ],
            )

        cars_column = ft.Column(
            alignment=ft.Alignment.CENTER,
            horizontal_alignment=ft.Alignment.CENTER,
            spacing=20,
        )

        for car in last_added_cars:
            car_images = images_dict.get(car.id, [])
            if car_images:
                card = self._create_car_card(car, car_images)
            else:
                card = self._create_car_card(car)
            cars_column.controls.append(card)

        subtitle = ft.Text(
            localization.last_added_cars,
            size=16,
            color=ft.Colors.ON_SURFACE_VARIANT,
        )

        content = ft.Column(
            [
                title,
                subtitle,
                cars_column,
            ],
            alignment="start",
            horizontal_alignment=ft.Alignment.CENTER,
            spacing=15,
        )

        return ft.View(
            route="/",
            navigation_bar=self._get_nav_bar(0),
            controls=[
                ft.Container(
                    content=content,
                    padding=20,
                    bgcolor=ft.Colors.WHITE,
                )
            ],
        )
