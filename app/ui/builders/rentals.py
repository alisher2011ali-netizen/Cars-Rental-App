import flet as ft
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select
from core.models import session_factory, Car, Rental, Tenant
from services.localization import localization
from ui.builders.base import Builder


class RentalBuilder(Builder):
    def build_rentals_view(self, db: Session = session_factory()) -> ft.View:
        rentals_list = db.scalars(select(Rental)).all()
        fab = self._build_fab("/add_rental", "Добавить аренду")

        if not rentals_list:
            empty_message = self._build_not_data_container(
                ft.Icon(
                    ft.Icons.KEY,
                    size=60,
                    color=ft.Colors.GREY_400,
                    align=ft.Alignment.CENTER,
                ),
                localization.no_rentals_history,
                localization.add_rental,
                "/add_rental",
            )
            return ft.View(
                route="/tenants",
                navigation_bar=self._get_nav_bar(3),
                controls=[
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.AppBar(
                                    title=ft.Text(
                                        f"📋 {localization.rentals}",
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

        rentals_content = ft.Container(
            content=ft.Column([], spacing=20),
            padding=40,
            bgcolor=ft.Colors.WHITE,
            expand=True,
        )

        for rental in rentals_list:
            match rental.status:
                case "active":
                    status_text = localization.active
                    status_color = ft.Colors.GREEN_500
                case "completed":
                    status_text = localization.completed
                    status_color = ft.Colors.BLACK_87
                case "cancelled":
                    status_text = localization.cancelled
                    status_color = ft.Colors.RED_500

            rental_card = ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            f"{localization.status}: {status_text}",
                            size=16,
                            color=status_color,
                            weight="bold",
                        ),
                        ft.Text(
                            f"{localization.car}: {rental.car.brand} {rental.car.model} ({rental.car.plate_number})",
                            size=14,
                        ),
                        ft.Text(
                            f"{localization.tenant}: {rental.tenant.last_name} {rental.tenant.first_name} ({rental.tenant.phone_number})",
                            size=14,
                        ),
                        ft.Text(
                            f"{localization.income_in_total}: {rental.total_cost} руб."
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
            rentals_content.content.controls.append(rental_card)

        return ft.View(
            route="/rentals",
            navigation_bar=self._get_nav_bar(3),
            controls=[rentals_content],
            floating_action_button=fab,
            floating_action_button_location=ft.FloatingActionButtonLocation.END_FLOAT,
        )

    def build_add_rental_view(self, db: Session = session_factory()) -> ft.View:
        selected_car_id = None
        selected_tenant_id = None

        def on_car_select(e):
            nonlocal selected_car_id
            selected_car_id = e.control.value

        def on_tenant_select(e):
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
                text=f"{tenant.last_name} {tenant.first_name} ({tenant.phone_number})",
            )
            for tenant in tenants
        ]
        tenant_dropdown = ft.Dropdown(
            options=tenant_options,
            value=tenant_options[0].key if tenant_options else None,
            width=300,
            on_select=on_tenant_select,
        )

        dates_info_text = ft.Text("Срок: 0 дней", size=16, weight="bold")
        total_price_text = ft.Text(
            f"{localization.total_to_be_paid}: 0 руб.",
            size=20,
            weight="bold",
            color=ft.Colors.GREEN_700,
        )

        period_field = ft.TextField(
            label="Период платежа",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: recalculate_total(),
        )

        error_text = ft.Text(
            value="Неправильный ввод! Только числа больше нуля",
            color=ft.Colors.RED,
            size=14,
            visible=False,
        )

        period_column = ft.Column([period_field, error_text], spacing=5, visible=False)

        price_field = ft.TextField(
            label="Стоимость за неделю",
            value="0",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=400,
            on_change=lambda e: recalculate_total(),
        )

        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        start_picker = ft.DatePicker(
            value=datetime.now(timezone.utc), on_change=lambda e: recalculate_total()
        )
        end_picker = ft.DatePicker(
            value=tomorrow, on_change=lambda e: recalculate_total()
        )

        manual_date_row = ft.Row(
            [
                ft.Button(
                    localization.start,
                    icon=ft.Icons.CALENDAR_MONTH,
                    on_click=lambda e: self.page.show_dialog(start_picker),
                ),
                ft.Button(
                    localization.end,
                    icon=ft.Icons.CALENDAR_MONTH,
                    on_click=lambda e: self.page.show_dialog(end_picker),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            visible=True,
        )

        def recalculate_total():
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
                weeks = difference.days // 7
                end_date = start_date + timedelta(weeks=weeks)
                total_amount = entered_price * weeks
                dates_info_text.value = f"Срок: {weeks} нед. ({start_date.strftime('%d.%m')} - {end_date.strftime('%d.%m')})"

            elif tariff == "monthly":
                start_date = start_picker.value
                difference = end_picker.value - start_date
                months = difference.days // 30
                end_date = start_date + timedelta(days=months * 30)
                total_amount = entered_price * months
                dates_info_text.value = f"Срок: {months} мес. ({start_date.strftime('%d.%m')} - {end_date.strftime('%d.%m')})"

            elif tariff == "custom":
                if not period_field.value:
                    dates_info_text.value = "Введите период"
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

                    dates_info_text.value = f"Срок: {periods_count} раз(а) по {period} дн. ({start_date.strftime('%d.%m')} - {end_date.strftime('%d.%m')})"

            total_price_text.value = (
                f"{localization.total_to_be_paid}: {total_amount:.2f} руб."
            )

            error_text.update()
            dates_info_text.update()
            total_price_text.update()

        def on_tariff_change(e):
            tariff = e.control.value
            if tariff == "weekly":
                price_field.label = "Стоимость за неделю"
                period_column.visible = False
            elif tariff == "monthly":
                price_field.label = "Стоимость за месяц"
                period_column.visible = False
            elif tariff == "custom":
                price_field.label = "Стоимость за период"
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

        def on_click_save(e):
            pass

        save_button = ft.Button(
            localization.save, icon=ft.Icons.SAVE, on_click=on_click_save
        )

        content = ft.Column(
            [
                ft.Text(
                    f"📋 {localization.add_rental}",
                    size=24,
                    weight="bold",
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
            navigation_bar=self._get_nav_bar(3),
            controls=[
                ft.Container(content=content, padding=20, alignment=ft.Alignment.CENTER)
            ],
        )
