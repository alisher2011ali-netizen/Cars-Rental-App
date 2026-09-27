import flet as ft
from core.models import Car, session_factory
from services.localization import localization
from sqlalchemy import select
from sqlalchemy.orm import Session
from ui.builders.base import Builder


class HomeBuilder(Builder):
    """Build UI views and widgets for the primary dashboard and home screen."""

    def build_home_view(self, db: Session | None = None) -> ft.View:
        """Construct the main home view displaying recent vehicles or a placeholder.

        Args:
            None

        Returns:
            ft.View: View containing the dashboard layout, navigation bar, and recent cars.
        """
        if db is None:
            db = session_factory()

        last_added_cars = db.scalars(select(Car).order_by(Car.id.desc()).limit(5)).all()

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
                    title,
                    ft.Container(
                        content=content,
                        padding=5,
                    ),
                ],
            )

        cars_column = ft.Column(
            alignment=ft.Alignment.CENTER,
            horizontal_alignment=ft.Alignment.CENTER,
            spacing=20,
        )

        for car in last_added_cars:
            car_images = [img.path for img in car.images] if car.images else []
            card = self.create_car_card(car, car_images)
            cars_column.controls.append(card)

        subtitle = ft.Text(
            localization.last_added_cars,
            size=16,
            color=ft.Colors.ON_SURFACE_VARIANT,
        )

        content = ft.Column(
            [
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
