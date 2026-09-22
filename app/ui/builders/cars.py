import flet as ft
from core.models import Car, session_factory
from services.localization import localization
from sqlalchemy import select
from sqlalchemy.orm import Session
from ui.builders.base import Builder


class CarBuilder(Builder):
    def build_cars_view(self, db: Session = session_factory()) -> ft.View:
        cars_list = db.scalars(select(Car)).all()
        fab = self._build_fab("/add_car", localization.add_car)

        if not cars_list:
            empty_message = self._build_not_data_container(
                ft.Icon(
                    ft.Icons.DIRECTIONS_CAR,
                    size=60,
                    color=ft.Colors.GREY_400,
                    align=ft.Alignment.CENTER,
                ),
                localization.no_added_cars,
                localization.add_car,
                "/add_car",
            )
            return ft.View(
                route="/cars",
                navigation_bar=self._get_nav_bar(1),
                controls=[
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.AppBar(
                                    title=ft.Text(
                                        f"🚗 {localization.cars}",
                                        size=24,
                                        weight="bold",
                                    )
                                ),
                                empty_message,
                            ]
                        ),
                        alignment=ft.Alignment.CENTER,
                    )
                ],
                floating_action_button=fab,
                floating_action_button_location=ft.FloatingActionButtonLocation.END_FLOAT,
            )

        cars_column = ft.Column(
            spacing=20,
            horizontal_alignment=ft.Alignment.CENTER,
            alignment=ft.Alignment.CENTER,
        )

        for car in cars_list:
            car_images = [img.path for img in car.images]
            card = self._create_car_card(car, car_images)
            cars_column.controls.append(card)

        content = ft.Column(
            [
                ft.Text(f"🚗 {localization.cars}", size=24, weight="bold"),
                cars_column,
            ],
            spacing=20,
            horizontal_alignment=ft.Alignment.CENTER,
        )

        cars_content = ft.Container(
            content=content,
            padding=20,
            expand=True,
        )

        return ft.View(
            route="/cars",
            navigation_bar=self._get_nav_bar(1),
            controls=[cars_content],
            floating_action_button=fab,
            floating_action_button_location=ft.FloatingActionButtonLocation.END_FLOAT,
        )

    def build_add_car_view(self, db: Session = session_factory()) -> ft.View:
        selected_images_paths = []

        file_picker = ft.FilePicker()

        async def pick_image_click(e):
            files = await file_picker.pick_files(
                allow_multiple=True, file_type=ft.FilePickerFileType.IMAGE
            )
            for file in files:
                if file.path not in selected_images_paths:
                    selected_images_paths.append(file.path)

        async def save_car(e=None):
            new_car = Car(
                brand=brand_input.value,
                model=model_input.value,
                year=year_input.value,
                plate_number=plate_num_input.value,
            )
            db.add(new_car)
            db.commit()

            for image_path in selected_images_paths:
                await self.connector.save_image(
                    image_path=image_path, object_id=new_car.id, object_type="car"
                )

            self._build_complete_snack_bar()
            self.page.push_route("/cars")

        brand_input = ft.TextField(label=localization.brand, width=300)
        model_input = ft.TextField(label=localization.model, width=300)
        year_input = ft.TextField(label=localization.year_of_production, width=300)
        plate_num_input = ft.TextField(label=localization.plate_number, width=300)
        input = ft.Container(
            content=ft.Column(
                [
                    ft.Text(localization.new_car, size=24, weight="bold"),
                    brand_input,
                    model_input,
                    year_input,
                    plate_num_input,
                    ft.TextButton(
                        localization.upload_images,
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=pick_image_click,
                    ),
                    ft.ElevatedButton(
                        localization.save,
                        icon=ft.Icons.SAVE,
                        on_click=save_car,
                    ),
                    ft.ElevatedButton(
                        localization.back,
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda e: self.page.push_route("/cars"),
                    ),
                ],
                spacing=15,
            ),
            padding=40,
            alignment=ft.Alignment.CENTER,
        )

        return ft.View(
            route="/add_car",
            navigation_bar=self._get_nav_bar(1),
            controls=[input],
        )
