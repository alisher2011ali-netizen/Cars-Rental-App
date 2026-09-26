from datetime import datetime, timedelta, timezone

import flet as ft
from core.models import Car, Rental, Tenant, session_factory
from services.localization import localization
from sqlalchemy import select
from sqlalchemy.orm import Session
from ui.builders.base import Builder


class RentalBuilder(Builder):
    """Build UI views and workflows for managing car rental contracts."""

    def build_rentals_view(self, db: Session | None = None) -> ft.View:
        """Construct the rentals list view displaying active and historical leases.

        Args:
            db (Session | None): Optional active database session. Defaults to None.

        Returns:
            ft.View: View containing rental cards or an empty-state screen.
        """
        if db is None:
            db = session_factory()

        rentals_list = db.scalars(select(Rental)).all()
        fab = self.build_fab("/add_rental", localization.add_rental)
        title = ft.AppBar(
            leading=ft.Icon(
                icon=ft.Icons.KEY,
                size=40,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            title=ft.Text(
                localization.rentals,
                size=30,
                weight=ft.FontWeight.BOLD,
            ),
        )

        if not rentals_list:
            return self.build_not_data_view(
                title=title,
                icon=ft.Icon(
                    ft.Icons.KEY,
                    size=60,
                    color=ft.Colors.GREY_400,
                    align=ft.Alignment.CENTER,
                ),
                text=localization.no_rentals_history,
                button_text=localization.add_rental,
                button_route="/add_rental",
                route="/rental",
                nav_bar_idx=3,
                fab=fab,
            )

        rentals_content = ft.Container(
            content=ft.Column([title], spacing=20),
            padding=40,
            bgcolor=ft.Colors.WHITE,
            expand=True,
        )

        for rental in rentals_list:
            rental_card = self.create_rental_card(rental)
            rentals_content.content.controls.append(rental_card)

        return ft.View(
            route="/rentals",
            navigation_bar=self.get_nav_bar(3),
            controls=[rentals_content],
            floating_action_button=fab,
            floating_action_button_location=ft.FloatingActionButtonLocation.END_FLOAT,
        )

    def build_add_rental_view(self, db: Session | None = None) -> ft.View:
        """Construct the lease agreement creation view with dynamic tariff calculators.

        Args:
            db (Session | None): Optional active database session. Defaults to None.

        Returns:
            ft.View: View containing form fields for calculating and creating leases.
        """
        if db is None:
            db = session_factory()

        selected_car_id = None
        selected_tenant_id = None

        def on_car_select(e: ft.ControlEvent) -> None:
            """Track selected vehicle identifier from dropdown changes.

            Args:
                e (ft.ControlEvent): Dropdown selection event.

            Returns:
                None: Mutates selected_car_id in outer closure scope.
            """
            nonlocal selected_car_id
            selected_car_id = e.control.value

        def on_tenant_select(e: ft.ControlEvent) -> None:
            """Track selected tenant identifier from dropdown changes.

            Args:
                e (ft.ControlEvent): Dropdown selection event.

            Returns:
                None: Mutates selected_tenant_id in outer closure scope.
            """
            nonlocal selected_tenant_id
            selected_tenant_id = e.control.value

        cars = db.scalars(select(Car)).all()
        tenants = db.scalars(select(Tenant)).all()

        if not cars or not tenants:
            snack = ft.SnackBar(
                ft.Text(localization.no_cars_or_tenants),
                bgcolor=ft.Colors.RED_500,
                open=True,
            )
            self.page.overlay.append(snack)
            return self.build_rentals_view()

        car_options = [
            ft.DropdownOption(
                key=car.id, text=f"{car.brand} {car.model} ({car.plate_number})"
            )
            for car in cars
        ]
        car_dropdown = ft.Dropdown(
            options=car_options,
            value=car_options[0].key if car_options else None,
            width=300,
            on_select=on_car_select,
        )

        tenant_options = [
            ft.DropdownOption(
                key=tenant.id,
                text=f"{tenant.name} ({tenant.phone_number})",
            )
            for tenant in tenants
        ]
        tenant_dropdown = ft.Dropdown(
            options=tenant_options,
            value=tenant_options[0].key if tenant_options else None,
            width=300,
            on_select=on_tenant_select,
        )

        dates_info_text = ft.Text(
            f"{localization.term}: 0 {localization.days}",
            size=16,
            weight=ft.FontWeight.BOLD,
        )
        total_price_text = ft.Text(
            f"{localization.total_to_be_paid}: 0 {localization.currency}",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.GREEN_700,
        )

        period_field = ft.TextField(
            label=localization.payment_period,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda _: recalculate_total(),
        )

        error_text = ft.Text(
            value=localization.invalid_input_greater_than_zero,
            color=ft.Colors.RED,
            size=14,
            visible=False,
        )

        period_column = ft.Column([period_field, error_text], spacing=5, visible=False)

        price_field = ft.TextField(
            label=localization.cost_per_week,
            value="0",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=400,
            on_change=lambda _: recalculate_total(),
        )

        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        start_picker = ft.DatePicker(
            value=datetime.now(timezone.utc), on_change=lambda _: recalculate_total()
        )
        end_picker = ft.DatePicker(
            value=tomorrow, on_change=lambda _: recalculate_total()
        )

        manual_date_row = ft.Row(
            [
                ft.Button(
                    localization.start,
                    icon=ft.Icons.CALENDAR_MONTH,
                    on_click=lambda _: self.page.show_dialog(start_picker),
                ),
                ft.Button(
                    localization.end,
                    icon=ft.Icons.CALENDAR_MONTH,
                    on_click=lambda _: self.page.show_dialog(end_picker),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            visible=True,
        )

        def recalculate_total() -> None:
            """Recalculate rental duration cycles and aggregate cost according to active tariff rules.

            Args:
                None

            Returns:
                None: Updates pricing, date duration text, and validation hints in-place.
            """
            tariff = tariff_radio.value
            try:
                entered_price = float(price_field.value or 0)
            except ValueError:
                entered_price = 0

            total_amount = 0
            error_text.visible = False

            if tariff == "weekly":
                start_date = start_picker.value
                difference = end_picker.value - start_date
                # Integer division truncates uncompleted week intervals
                weeks = difference.days // 7
                end_date = start_date + timedelta(weeks=weeks)
                total_amount = entered_price * weeks
                dates_info_text.value = f"{localization.term}: {weeks} {localization.weeks_short} ({start_date.strftime('%d.%m')} - {end_date.strftime('%d.%m')})"

            elif tariff == "monthly":
                start_date = start_picker.value
                difference = end_picker.value - start_date
                # Standardize contractual billing month to fixed 30-day blocks
                months = difference.days // 30
                end_date = start_date + timedelta(days=months * 30)
                total_amount = entered_price * months
                dates_info_text.value = f"{localization.term}: {months} {localization.months_short} ({start_date.strftime('%d.%m')} - {end_date.strftime('%d.%m')})"

            elif tariff == "custom":
                if not period_field.value:
                    dates_info_text.value = localization.enter_period
                elif not period_field.value.isdigit() or int(period_field.value) <= 0:
                    error_text.visible = True
                    error_text.update()
                    return
                else:
                    start_date = start_picker.value
                    difference = end_picker.value - start_date
                    period = int(period_field.value)

                    periods_count = difference.days // period
                    end_date = start_date + timedelta(days=periods_count * period)
                    total_amount = entered_price * periods_count

                    dates_info_text.value = f"{localization.term}: {periods_count} {localization.times_by} {period} {localization.days_short} ({start_date.strftime('%d.%m')} - {end_date.strftime('%d.%m')})"

            total_price_text.value = f"{localization.total_to_be_paid}: {total_amount:.2f} {localization.currency}"

            error_text.update()
            dates_info_text.update()
            total_price_text.update()

        def on_tariff_change(e: ft.ControlEvent) -> None:
            """Adjust visible form controls and recompute totals when changing billing tariffs.

            Args:
                e (ft.ControlEvent): Radio group selection change event.

            Returns:
                None: Updates label text, toggles custom inputs, and triggers recalculation.
            """
            tariff = e.control.value
            if tariff == "weekly":
                price_field.label = localization.cost_per_week
                period_column.visible = False
            elif tariff == "monthly":
                price_field.label = localization.cost_per_month
                period_column.visible = False
            elif tariff == "custom":
                price_field.label = localization.cost_per_period
                period_column.visible = True

            price_field.update()
            period_column.update()
            recalculate_total()

        tariff_radio = ft.RadioGroup(
            content=ft.Column(
                [
                    ft.Radio(value="weekly", label=localization.weekly),
                    ft.Radio(value="monthly", label=localization.monthly),
                    ft.Radio(value="custom", label=localization.another_term),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            value="weekly",
            on_change=on_tariff_change,
        )

        def on_click_save(e: ft.ControlEvent) -> None:
            """Persist the entered rental attributes.

            Args:
                e (ft.ControlEvent): Save button click event.

            Returns:
                None: Commits record to database and navigates back to the inventory list.
            """

        # TODO: save rental to database

        save_button = ft.Button(
            localization.save, icon=ft.Icons.SAVE, on_click=on_click_save
        )

        content = ft.Column(
            [
                ft.Text(
                    f"📋 {localization.add_rental}",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                car_dropdown,
                tenant_dropdown,
                tariff_radio,
                period_column,
                price_field,
                dates_info_text,
                total_price_text,
                manual_date_row,
                save_button,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
        )
        return ft.View(
            route="/add_rental",
            navigation_bar=self.get_nav_bar(3),
            controls=[
                ft.Container(content=content, padding=20, alignment=ft.Alignment.CENTER)
            ],
        )
