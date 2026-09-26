import flet as ft
from core.models import Car, session_factory
from services.localization import localization
from sqlalchemy import select
from sqlalchemy.orm import Session
from ui.builders.base import Builder


class CarBuilder(Builder):
    """Build UI views and controls for car inventory management and detailed displays."""

    def build_cars_view(self, db: Session | None = None) -> ft.View:
        """Construct the primary vehicles catalog view.

        Args:
            db (Session | None): Optional active database session. Defaults to None.

        Returns:
            ft.View: View displaying the list of registered vehicles or an empty placeholder.
        """
        if db is None:
            db = session_factory()

        cars_list = db.scalars(select(Car)).all()
        fab = self.build_fab("/add_car", localization.add_car)
        title = ft.AppBar(
            leading=ft.Icon(
                icon=ft.Icons.DIRECTIONS_CAR,
                size=40,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            title=ft.Text(
                f"{localization.cars}",
                size=30,
                weight=ft.FontWeight.BOLD,
            ),
        )

        if not cars_list:
            return self.build_not_data_view(
                title=title,
                icon=ft.Icon(
                    ft.Icons.DIRECTIONS_CAR,
                    size=60,
                    color=ft.Colors.GREY_400,
                    align=ft.Alignment.CENTER,
                ),
                text=localization.no_added_cars,
                button_text=localization.add_car,
                button_route="/add_car",
                route="/cars",
                nav_bar_idx=1,
                fab=fab,
            )

        cars_column = ft.Column(
            spacing=20,
            horizontal_alignment=ft.Alignment.CENTER,
            alignment=ft.Alignment.CENTER,
        )

        for car in cars_list:
            car_images = [img.path for img in car.images]
            card = self.create_car_card(car, car_images)
            cars_column.controls.append(card)

        content = ft.Column(
            [cars_column],
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
            navigation_bar=self.get_nav_bar(1),
            controls=[title, cars_content],
            floating_action_button=fab,
            floating_action_button_location=ft.FloatingActionButtonLocation.END_FLOAT,
        )

    def build_add_car_view(self, db: Session | None = None) -> ft.View:
        """Construct the registration form view for adding a new vehicle.

        Args:
            db (Session | None): Optional active database session. Defaults to None.

        Returns:
            ft.View: View containing input fields and file upload triggers for vehicle creation.
        """
        if db is None:
            db = session_factory()

        selected_images_paths = []

        file_picker = ft.FilePicker()

        async def pick_image_click(e: ft.ControlEvent) -> None:
            """Launch the system file picker to select vehicle images.

            Args:
                e (ft.ControlEvent): Button click interaction event.

            Returns:
                None: Appends picked file paths to the local staging list.
            """
            files = await file_picker.pick_files(
                allow_multiple=True, file_type=ft.FilePickerFileType.IMAGE
            )
            for file in files:
                if file.path not in selected_images_paths:
                    selected_images_paths.append(file.path)

        async def save_car(e: ft.ControlEvent | None = None) -> None:
            """Persist the entered vehicle attributes and copy associated photos to storage.

            Args:
                e (ft.ControlEvent | None): Optional triggering control event. Defaults to None.

            Returns:
                None: Commits record to database and navigates back to the inventory list.
            """
            new_car = Car(
                brand=brand_input.value,
                model=model_input.value,
                year=year_input.value,
                plate_number=plate_num_input.value,
                region_code=region_code_input.value,
            )
            db.add(new_car)
            db.commit()

            for image_path in selected_images_paths:
                await self.connector.save_image(
                    image_path=image_path, object_id=new_car.id, object_type="car"
                )

            self.build_complete_snack_bar()
            await self.page.push_route("/cars")

        brand_input = ft.TextField(label=localization.brand, width=300)
        model_input = ft.TextField(label=localization.model, width=300)
        year_input = ft.TextField(label=localization.year_of_production, width=300)
        plate_num_input = ft.TextField(label=localization.plate_number, width=150)
        region_code_input = ft.TextField(
            label="Регион",
            width=100,
        )
        num_input_row = ft.Row([plate_num_input, region_code_input])
        input = ft.Container(
            content=ft.Column(
                [
                    ft.Text(localization.new_car, size=24, weight=ft.FontWeight.BOLD),
                    brand_input,
                    model_input,
                    year_input,
                    num_input_row,
                    ft.TextButton(
                        localization.upload_images,
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=pick_image_click,
                    ),
                    ft.Button(
                        localization.save,
                        icon=ft.Icons.SAVE,
                        on_click=save_car,
                    ),
                    ft.Button(
                        localization.back,
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda _: self.page.run_task(
                            self.page.push_route, "/cars"
                        ),
                    ),
                ],
                spacing=15,
            ),
            padding=40,
            alignment=ft.Alignment.CENTER,
        )

        return ft.View(
            route="/add_car",
            navigation_bar=self.get_nav_bar(1),
            controls=[input],
        )

    def build_car_details_view(self, car_id: int, db: Session | None = None) -> ft.View:
        """Construct the detailed vehicle view with full-screen gallery inspection.

        Args:
            car_id (int): Primary key of the car to display.
            db (Session | None): Optional active database session. Defaults to None.

        Returns:
            ft.View: View containing vehicle specs, media carousel, and active rental shortcuts.
        """
        if db is None:
            db = session_factory()

        car = db.get(Car, car_id)
        if not car:
            return ft.View(
                route=f"/cars/{car_id}",
                controls=[
                    ft.AppBar(title=ft.Text("Ошибка")),
                    ft.Text("Автомобиль не найден", color=ft.Colors.ERROR),
                    ft.Button(
                        "Назад",
                        icon=ft.Icons.ARROW_BACK,
                        on_click=self.page.run_task(self.page.push_route, "/"),
                        align=ft.Alignment.CENTER,
                    ),
                ],
            )

        car_images = car.images
        # Use a single-item list to enable state mutation across nested closure scopes
        current_index = [0]

        gallery_img = ft.Image(
            src=car_images[0].path if car_images else "",
            fit=ft.BoxFit.CONTAIN,
            expand=True,
        )
        gallery_counter = ft.Text(
            size=16, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD
        )

        def update_gallery() -> None:
            """Synchronize gallery image source and counter text with current index.

            Args:
                None

            Returns:
                None: Updates gallery controls on the screen.
            """
            if car_images:
                gallery_img.src = car_images[current_index[0]].path
                gallery_counter.value = f"{current_index[0] + 1} / {len(car_images)}"
                gallery_img.update()
                gallery_counter.update()

        def close_gallery(e: ft.ControlEvent) -> None:
            """Hide the full-screen gallery overlay.

            Args:
                e (ft.ControlEvent): Control interaction event.

            Returns:
                None: Sets overlay visibility to False and updates the page.
            """
            gallery_overlay.visible = False
            self.page.update()

        def next_img(e: ft.ControlEvent) -> None:
            """Advance to the next image in the full-screen gallery.

            Args:
                e (ft.ControlEvent): Forward button interaction event.

            Returns:
                None: Increments index within bounds and updates display.
            """
            if current_index[0] < len(car_images) - 1:
                current_index[0] += 1
                update_gallery()

        def prev_img(e: ft.ControlEvent) -> None:
            """Step back to the preceding image in the full-screen gallery.

            Args:
                e (ft.ControlEvent): Backward button interaction event.

            Returns:
                None: Decrements index within bounds and updates display.
            """
            if current_index[0] > 0:
                current_index[0] -= 1
                update_gallery()

        def delete_img(e: ft.ControlEvent) -> None:
            """Trigger the image removal flow and close the overlay.

            Args:
                e (ft.ControlEvent): Delete button click event.

            Returns:
                None: Dismisses gallery overlay pending deletion implementation.
            """
            close_gallery(e)

        gallery_overlay = ft.Container(
            content=ft.Stack(
                [
                    ft.Container(
                        content=gallery_img,
                        alignment=ft.Alignment.CENTER,
                        on_click=close_gallery,
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.IconButton(
                            ft.Icons.DELETE,
                            icon_color=ft.Colors.WHITE,
                            on_click=delete_img,
                        ),
                        bgcolor=ft.Colors.with_opacity(0.6, ft.Colors.RED),
                        border_radius=8,
                        top=20,
                        right=20,
                    ),
                    ft.Container(
                        content=ft.IconButton(
                            ft.Icons.CLOSE,
                            icon_color=ft.Colors.WHITE,
                            on_click=close_gallery,
                        ),
                        top=20,
                        left=20,
                    ),
                    ft.Row(
                        [
                            ft.IconButton(
                                ft.Icons.ARROW_BACK_IOS,
                                icon_color=ft.Colors.WHITE,
                                on_click=prev_img,
                            ),
                            gallery_counter,
                            ft.IconButton(
                                ft.Icons.ARROW_FORWARD_IOS,
                                icon_color=ft.Colors.WHITE,
                                on_click=next_img,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        bottom=40,
                        left=20,
                        right=20,
                    ),
                ],
                expand=True,
            ),
            bgcolor=ft.Colors.with_opacity(0.95, ft.Colors.BLACK),
            visible=False,
            expand=True,
            left=0,
            top=0,
            right=0,
            bottom=0,
        )

        # Attach overlay only once to prevent duplicate controls accumulation in the root page tree
        if gallery_overlay not in self.page.overlay:
            self.page.overlay.append(gallery_overlay)

        def open_gallery(e: ft.ControlEvent, index: int) -> None:
            """Display the modal gallery starting at the targeted image index.

            Args:
                e (ft.ControlEvent): Tap event from thumbnail.
                index (int): Position of the selected image.

            Returns:
                None: Opens modal overlay and redraws host page.
            """
            if not car_images:
                return
            current_index[0] = index
            update_gallery()
            gallery_overlay.visible = True
            self.page.update()

        images_row = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=10)
        if car_images:
            for i, img in enumerate(car_images):
                images_row.controls.append(
                    ft.GestureDetector(
                        content=ft.Image(
                            src=img.path,
                            width=120,
                            height=120,
                            fit=ft.BoxFit.COVER,
                            border_radius=8,
                        ),
                        # Bind the current iteration index as a default argument to prevent late-binding loop capture
                        on_tap=lambda e, idx=i: open_gallery(e, idx),
                    )
                )
        else:
            images_row.controls.append(
                ft.Text("Нет фото", color=ft.Colors.ON_SURFACE_VARIANT)
            )

        add_photo_btn = ft.Button(
            "Добавить фото",
            icon=ft.Icons.ADD,
        )

        car_info = ft.Column(
            [
                ft.Text(f"{car.brand} {car.model}", size=24, weight=ft.FontWeight.BOLD),
                ft.Text(f"Год выпуска: {car.year}", size=16),
                ft.Text(f"Гос. номер: {car.plate_number}", size=16),
                ft.Text(
                    f"Статус: {localization.__getattr__(car.status.value)}", size=16
                ),
                ft.Text(f"Заметки: {car.notes or 'Без заметок'}", size=16),
            ],
            spacing=5,
        )

        active_rental_btn = ft.Container()
        if hasattr(car, "rentals") and car.rentals:
            # Select the most recent lease chronologically assuming list preserves append order
            active_rental = car.rentals[-1]
            active_rental_btn = ft.Button(
                f"Текущая аренда #{active_rental.id}",
                icon=ft.Icons.KEY,
                on_click=lambda _: self.page.run_task(
                    self.page.push_route, f"/rentals/{active_rental.id}"
                ),
                icon_color=ft.Colors.PRIMARY,
            )

        return ft.View(
            route=f"/cars/{car_id}",
            controls=[
                ft.AppBar(
                    title=ft.Text(f"Детали авто #{car_id}"),
                    leading=ft.IconButton(
                        ft.Icons.ARROW_BACK,
                        on_click=lambda _: self.page.run_task(
                            self.page.push_route, "/cars"
                        ),
                    ),
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            images_row,
                            add_photo_btn,
                            ft.Divider(height=30),
                            car_info,
                            ft.Container(height=10),
                            active_rental_btn,
                        ],
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    padding=20,
                    expand=True,
                ),
            ],
        )
