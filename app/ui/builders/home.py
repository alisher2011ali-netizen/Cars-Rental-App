import flet as ft
from services.localization import localization
from ui.builders.base import Builder


class HomeBuilder(Builder):
    """Build UI views and widgets for the primary dashboard and home screen."""

    def build_home_view(self) -> ft.View:
        """Construct the main home view displaying recent vehicles or a placeholder.

        Args:
            None

        Returns:
            ft.View: View containing the dashboard layout, navigation bar, and recent cars.
        """
        last_added_cars, images_dict = self.connector.get_last_added_cars()

        title = ft.AppBar(
            title=ft.Text(
                localization.app_name,
                size=40,
                weight=ft.FontWeight.BOLD,
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
                [message],
                alignment=ft.Alignment.TOP_CENTER,
                horizontal_alignment=ft.Alignment.CENTER,
                spacing=20,
            )

            return ft.View(
                route="/",
                navigation_bar=self.get_nav_bar(0),
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
                card = self.create_car_card(car, car_images)
            else:
                card = self.create_car_card(car)
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
            navigation_bar=self.get_nav_bar(0),
            controls=[
                title,
                ft.Container(
                    content=content,
                    padding=20,
                ),
            ],
        )
