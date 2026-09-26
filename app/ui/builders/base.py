import flet as ft
from core.models import Car, Payment, PaymentType, Rental, Tenant
from services.connector import Connector
from services.localization import localization


class Builder:
    """Provide reusable UI component builders and layout scaffolds for views."""

    def __init__(
        self,
        page: ft.Page,
    ) -> None:
        """Initialize the builder with the root page, preferences, and data connectors.

        Args:
            page (ft.Page): The root page container provided by the Flet runtime.

        Returns:
            None: Initializes UI construction utilities.
        """
        self.page = page
        self.prefs = ft.SharedPreferences()
        self.connector = Connector()
        self.current_image_indices = {}

    def get_nav_bar(self, current_index: int) -> ft.NavigationBar:
        """Build the global bottom navigation bar with localized destination tabs.

        Args:
            current_index (int): Index of the currently active navigation item.

        Returns:
            ft.NavigationBar: Configured bottom navigation bar control.
        """
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
                    icon=ft.Icons.ATTACH_MONEY,
                    label=localization.finances,
                ),
            ],
            selected_index=current_index,
            on_change=self._handle_nav_change,
        )

    async def _handle_nav_change(self, e: ft.ControlEvent) -> None:
        """Dispatch route navigation corresponding to the selected navigation destination.

        Args:
            e (ft.ControlEvent): Navigation bar item selection event.

        Returns:
            None: Asynchronously pushes the matched route onto the navigation stack.
        """
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

    def create_car_card(
        self, car: Car, car_images: list[str] | None = None
    ) -> ft.Container:
        """Render a vehicle summary card featuring swipeable photos and plate badges.

        Args:
            car (Car): Vehicle model instance containing attributes to display.
            car_images (list[str] | None): Base64-encoded image sources for carousel display. Defaults to None.

        Returns:
            ft.Container: Configured interactive container card for the vehicle.
        """
        car_images = car_images or []
        self.current_image_indices[car.id] = 0

        async def go_to_details(e: ft.ControlEvent) -> None:
            """Navigate to the detailed inspection view of the current car.

            Args:
                e (ft.ControlEvent): Interaction event from card tap or button click.

            Returns:
                None: Asynchronously routes to the detail view.
            """
            await self.page.push_route(f"/cars/{car.id}")

        plate_badge = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        car.plate_number.upper(),
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLACK,
                    ),
                    ft.Container(
                        width=1,
                        height=16,
                        bgcolor=ft.Colors.BLACK54,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                str(getattr(car, "region_code", "") or "RUS"),
                                size=10,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BLACK,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=0,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
            ),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1.5, ft.Colors.BLACK87),
            border_radius=4,
            padding=ft.padding.symmetric(horizontal=8, vertical=2),
        )

        if car_images:
            indicator = ft.Text(
                f"1/{len(car_images)}",
                size=12,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.ON_SURFACE_VARIANT,
            )

            image_container = ft.Container(
                content=ft.Image(
                    src=car_images[0],
                    fit=ft.BoxFit.COVER,
                ),
                aspect_ratio=4 / 3,
                border_radius=8,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            )

            # Track accumulated drag offset and lock further triggers until the gesture ends to avoid rapid multi-skips
            drag_state = {"accumulated_delta": 0.0, "swiped": False}
            threshold = 40.0

            def on_horizontal_drag_start(e: ft.DragStartEvent) -> None:
                """Reset drag accumulation and gesture lock on touch contact.

                Args:
                    e (ft.DragStartEvent): Gesture start event parameters.

                Returns:
                    None: Resets internal drag tracking state.
                """
                drag_state["accumulated_delta"] = 0.0
                drag_state["swiped"] = False

            def on_horizontal_drag_update(e: ft.DragUpdateEvent) -> None:
                """Accumulate swipe travel and trigger image change once the threshold is crossed.

                Args:
                    e (ft.DragUpdateEvent): Drag update event containing step delta.

                Returns:
                    None: Mutates current slide index and updates display controls.
                """
                if drag_state["swiped"]:
                    return

                drag_state["accumulated_delta"] += e.primary_delta or 0.0

                if drag_state["accumulated_delta"] > threshold:
                    self._prev_image(car.id, car_images, image_container, indicator)
                    drag_state["swiped"] = True
                elif drag_state["accumulated_delta"] < -threshold:
                    self._next_image(car.id, car_images, image_container, indicator)
                    drag_state["swiped"] = True

            def on_horizontal_drag_end(e: ft.DragEndEvent) -> None:
                """Clean up swipe lock when the pointer leaves the control surface.

                Args:
                    e (ft.DragEndEvent): Drag completion event.

                Returns:
                    None: Clears gesture lock.
                """
                drag_state["accumulated_delta"] = 0.0
                drag_state["swiped"] = False

            image_with_swipe = ft.GestureDetector(
                content=image_container,
                on_horizontal_drag_start=on_horizontal_drag_start,
                on_horizontal_drag_update=on_horizontal_drag_update,
                on_horizontal_drag_end=on_horizontal_drag_end,
                on_tap=go_to_details,
            )

        else:
            image_container = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(
                            ft.Icons.DIRECTIONS_CAR,
                            size=48,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Text(
                            localization.no_images,
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6,
                ),
                aspect_ratio=4 / 3,
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                alignment=ft.Alignment.CENTER,
                border_radius=8,
            )
            image_with_swipe = ft.GestureDetector(
                content=image_container,
                on_tap=go_to_details,
            )
            indicator = ft.Text()

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                f"{car.brand} {car.model}",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.ON_SURFACE,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                expand=True,
                            ),
                            plate_badge,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    image_with_swipe,
                    ft.Row(
                        [indicator],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                spacing=8,
            ),
            margin=ft.margin.symmetric(horizontal=8, vertical=4),
            padding=12,
            border_radius=12,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            on_click=go_to_details,
        )

    def build_complete_snack_bar(self) -> ft.SnackBar:
        """Construct a standardized success notification snackbar.

        Args:
            None

        Returns:
            ft.SnackBar: Preconfigured visible snackbar control.
        """
        return ft.SnackBar(
            content=ft.Text(localization.added_successfully),
            action=ft.SnackBarAction(label="OK"),
            duration=ft.Duration(seconds=5),
            open=True,
        )

    def build_not_data_view(
        self,
        title: ft.Control,
        icon: ft.Icon,
        text: str,
        button_text: str,
        button_route: str,
        route: str,
        nav_bar_idx: int,
        fab: ft.FloatingActionButton,
    ) -> ft.View:
        """Assemble an empty-state scaffold view prompting user creation actions.

        Args:
            title (ft.Control): Header or app bar title control.
            icon (ft.Icon): Central descriptive placeholder icon.
            text (str): Localized empty-state prompt text.
            button_text (str): Localized label for the call-to-action button.
            button_route (str): Target route navigated upon action button click.
            route (str): Current view navigation route identifier.
            nav_bar_idx (int): Selected navigation bar item index.
            fab (ft.FloatingActionButton): Contextual action button control.

        Returns:
            ft.View: Configured empty-state view.
        """
        return ft.View(
            route=route,
            navigation_bar=self.get_nav_bar(nav_bar_idx),
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
                                            weight=ft.FontWeight.BOLD,
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

    def build_fab(self, route: str, text: str) -> ft.FloatingActionButton:
        """Construct a standardized Floating Action Button triggering route navigation.

        Args:
            route (str): Target route to navigate to on button click.
            text (str): Tooltip text explaining the button's action.

        Returns:
            ft.FloatingActionButton: Ready-to-attach floating action button.
        """
        return ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            on_click=lambda _: self.page.run_task(self.page.push_route, route),
            tooltip=ft.Tooltip(text),
        )

    def create_tenant_card(self, tenant: Tenant) -> ft.Container:
        """Build an interactive contact card displaying tenant details and avatar.

        Args:
            tenant (Tenant): Tenant entity instance containing profile information.

        Returns:
            ft.Container: Configured tenant presentation card.
        """

        def on_phone_number_tap(tenant_phone: str) -> None:
            """Copy the tenant's contact phone number into the host clipboard buffer.

            Args:
                tenant_phone (str): Target phone number string.

            Returns:
                None: Writes to clipboard and triggers a toast notification.
            """
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

        return ft.Container(
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
                                            weight=ft.FontWeight.BOLD,
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
                                            on_click=lambda _, t_id=tenant.id: (
                                                self.page.run_task(
                                                    self.page.push_route,
                                                    f"/tenants/{t_id}",
                                                )
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

    def create_payment_card(self, payment: Payment) -> ft.Container:
        """Format and construct a transaction card tailored to parsing provenance.

        Args:
            payment (Payment): Payment entity with financial and provenance attributes.

        Returns:
            ft.Container: Configured transaction presentation card.
        """
        payment_type = "+" if payment.type == PaymentType.income else "-"

        text_color = (
            ft.Colors.PRIMARY if payment.type == PaymentType.income else ft.Colors.ERROR
        )

        # Strip redundant decimal zeros to show compact currency amounts (e.g. 1500 instead of 1500.00)
        formatted_amount = f"{abs(payment.amount):.2f}".rstrip("0").rstrip(".")

        if not payment.is_parsed:
            payment_card = self._create_not_parsed_payment_card(
                payment, payment_type, formatted_amount, text_color
            )

        elif payment.is_parsed:
            payment_card = self._create_parsed_payment_card(
                payment, payment_type, formatted_amount, text_color
            )

        return payment_card

    def _create_not_parsed_payment_card(
        self,
        payment: Payment,
        payment_type: str,
        formatted_amount: str,
        text_color: ft.ColorValue,
    ) -> ft.Container:
        """Render a financial card for manually entered payment records.

        Args:
            payment (Payment): Transaction data source model.
            payment_type (str): Sign indicator symbol ('+' or '-').
            formatted_amount (str): Formatted monetary amount string.
            text_color (ft.ColorValue): Design token representing flow direction.

        Returns:
            ft.Container: Finished card layout control.
        """
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        f"{payment_type}{formatted_amount}",
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color=text_color,
                                    ),
                                    ft.Text(
                                        localization.currency,
                                        size=14,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                    ),
                                ],
                                spacing=5,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text(
                        f"{localization.notes}:\n{payment.notes}",
                        size=14,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ],
                spacing=5,
            ),
            bgcolor=ft.Colors.SECONDARY_CONTAINER,
            padding=10,
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        )

    def _create_parsed_payment_card(
        self,
        payment: Payment,
        payment_type: str,
        formatted_amount: str,
        text_color: ft.ColorValue,
    ) -> ft.Container:
        """Render a specialized financial card displaying bank statement metadata.

        Args:
            payment (Payment): Statement payment model instance.
            payment_type (str): Sign indicator symbol ('+' or '-').
            formatted_amount (str): Formatted monetary amount string.
            text_color (ft.ColorValue): Design token representing flow direction.

        Returns:
            ft.Container: Bank-specialized transaction card layout.
        """
        op_date_str = (
            payment.operation_date.strftime("%d.%m.%Y %H:%M")
            if payment.operation_date
            else ""
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        f"{payment_type}{formatted_amount}",
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color=text_color,
                                    ),
                                    ft.Text(
                                        localization.currency,
                                        size=14,
                                        color=ft.Colors.ON_SECONDARY_CONTAINER,
                                    ),
                                ],
                                spacing=5,
                            ),
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.ACCOUNT_BALANCE,
                                        size=14,
                                        color=ft.Colors.ON_SECONDARY_CONTAINER,
                                    ),
                                    ft.Text(
                                        localization.sberbank,
                                        size=12,
                                        color=ft.Colors.ON_SECONDARY_CONTAINER,
                                    ),
                                ],
                                spacing=2,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text(
                        payment.description or localization.no_description,
                        size=14,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        color=ft.Colors.ON_SECONDARY_CONTAINER,
                    ),
                    ft.Row(
                        [
                            ft.Text(
                                payment.category or "",
                                size=12,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                            ft.Text(
                                op_date_str,
                                size=12,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=5,
            ),
            bgcolor=ft.Colors.SECONDARY_CONTAINER,
            padding=10,
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        )

    def create_rental_card(self, rental: Rental) -> ft.Container:
        """Render a comprehensive contractual lease summary card.

        Args:
            rental (Rental): Active or historical rental record.

        Returns:
            ft.Container: Stylized lease card control.
        """
        match rental.status.value:
            case "active":
                status_text = localization.active
                status_color = ft.Colors.GREEN_500
            case "completed":
                status_text = localization.completed
                status_color = ft.Colors.BLACK_87
            case "cancelled":
                status_text = localization.cancelled
                status_color = ft.Colors.RED_500
            case _:
                status_text = localization.other
                status_color = ft.Colors.GREY_500

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        f"{localization.status}: {status_text}",
                        size=16,
                        color=status_color,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        f"{localization.car}: {rental.car.brand} {rental.car.model} ({rental.car.plate_number})",
                        size=14,
                    ),
                    ft.Text(
                        f"{localization.tenant}: {rental.tenant.name} ({rental.tenant.phone_number})",
                        size=14,
                    ),
                    ft.Text(
                        f"{localization.income_in_total}: {rental.total_cost} {localization.currency}"
                    ),
                    ft.Text(
                        f"{localization.start}: {rental.start_date}",
                        size=14,
                    ),
                    ft.Text(f"{localization.end}: {rental.end_date}", size=14),
                ],
                spacing=5,
            ),
            padding=15,
            border_radius=12,
            bgcolor=ft.Colors.GREY_100,
            shadow=True,
        )
