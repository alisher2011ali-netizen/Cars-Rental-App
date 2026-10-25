from datetime import date, datetime, timedelta

import flet as ft
from core.models import Car, Payment, Rental, Tenant, session_factory
from services.localization import localization
from sqlalchemy import func, select
from ui.builders.base import Builder


class RentalBuilder(Builder):
    """Build UI views and workflows for managing car rental contracts."""

    def build_rentals_view(self) -> ft.View:
        """Construct the rentals list view displaying active and historical leases.

        Args:
            None

        Returns:
            ft.View: View containing rental cards or an empty-state screen.
        """
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
            content=ft.Column(spacing=20),
            expand=True,
        )

        for rental in rentals_list:
            rental_card = self.create_rental_card(rental)
            rentals_content.content.controls.append(rental_card)

        return ft.View(
            route="/rentals",
            navigation_bar=self.get_nav_bar(3),
            controls=[title, rentals_content],
            floating_action_button=fab,
            floating_action_button_location=ft.FloatingActionButtonLocation.END_FLOAT,
        )

    def build_add_rental_view(self) -> ft.View:
        """Construct the lease agreement creation view with dynamic tariff calculators.

        Args:
            None

        Returns:
            ft.View: View containing form fields for calculating and creating leases.
        """

        # Загружаем данные и сразу закрываем сессию: в замыканиях держим только простые значения
        db = session_factory()
        cars = [
            (car.id, f"{car.brand} {car.model} ({car.plate_number})")
            for car in db.scalars(select(Car)).all()
        ]
        tenants = [
            (t.id, f"{t.name} ({t.phone_number})")
            for t in db.scalars(select(Tenant)).all()
        ]

        if not cars or not tenants:
            snack = ft.SnackBar(
                ft.Text(localization.no_cars_or_tenants),
                bgcolor=ft.Colors.RED_500,
                open=True,
            )
            self.page.overlay.append(snack)
            return self.build_rentals_view()

        car_dropdown = ft.Dropdown(
            options=[ft.DropdownOption(key=str(cid), text=text) for cid, text in cars],
            value=str(cars[0][0]),
            width=300,
        )
        tenant_dropdown = ft.Dropdown(
            options=[
                ft.DropdownOption(key=str(tid), text=text) for tid, text in tenants
            ],
            value=str(tenants[0][0]),
            width=300,
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

        # Одна общая строка ошибки формы (вне period_column, чтобы не пряталась)
        form_error = ft.Text(color=ft.Colors.RED, size=14, visible=False)

        period_field = ft.TextField(
            label=localization.payment_period,
            value="7",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda _: recalculate_total(),
        )
        period_column = ft.Column([period_field], spacing=5, visible=False)

        price_field = ft.TextField(
            label=localization.cost_per_week,
            value="0",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=400,
            on_change=lambda _: recalculate_total(),
        )

        notes_field = ft.TextField(
            label=localization.notes,  # добавь ключ в локали
            multiline=True,
            min_lines=2,
            max_lines=4,
            width=400,
        )

        def to_date(value: datetime | date) -> date:
            return value.date() if isinstance(value, datetime) else value

        now = datetime.now()
        start_picker = ft.DatePicker(value=now, on_change=lambda _: on_date_change())
        end_picker = ft.DatePicker(
            value=now + timedelta(days=7), on_change=lambda _: on_date_change()
        )

        start_button = ft.Button(
            f"{localization.start}: {to_date(start_picker.value):%d.%m.%Y}",
            icon=ft.Icons.CALENDAR_MONTH,
            on_click=lambda _: self.page.show_dialog(start_picker),
        )
        end_button = ft.Button(
            f"{localization.end}: {to_date(end_picker.value):%d.%m.%Y}",
            icon=ft.Icons.CALENDAR_MONTH,
            on_click=lambda _: self.page.show_dialog(end_picker),
        )
        manual_date_row = ft.Row(
            [start_button, end_button], alignment=ft.MainAxisAlignment.CENTER
        )

        def calculate() -> dict | None:
            """Единый расчёт для экрана и для сохранения. None — если ввод некорректен."""
            tariff = tariff_radio.value
            if tariff == "weekly":
                period = 7
            elif tariff == "monthly":
                period = 30  # расчётный месяц = 30 дней
            else:
                raw = period_field.value or ""
                if not raw.isdigit() or int(raw) <= 0:
                    return None
                period = int(raw)

            raw_price = (price_field.value or "").strip()
            if not raw_price.isdigit():
                return None
            price = int(raw_price)

            start = to_date(start_picker.value)
            end = to_date(end_picker.value)
            count = (end - start).days // period  # неполный период отбрасываем
            return {
                "period": period,
                "price": price,
                "count": count,
                "start": start,
                # реальный конец = только полные периоды
                "end": start + timedelta(days=max(count, 0) * period),
                "total": price * max(count, 0),
            }

        def show_error(text: str) -> None:
            form_error.value = text
            form_error.visible = True
            form_error.update()

        def recalculate_total() -> None:
            form_error.visible = False
            data = calculate()

            if data is None:
                dates_info_text.value = localization.enter_period
                total_price_text.value = (
                    f"{localization.total_to_be_paid}: 0 {localization.currency}"
                )
            else:
                unit = {
                    "weekly": localization.weeks_short,
                    "monthly": localization.months_short,
                }.get(tariff_radio.value)
                if unit:
                    label = f"{data['count']} {unit}"
                else:
                    label = f"{data['count']} {localization.times_by} {data['period']} {localization.days_short}"
                dates_info_text.value = (
                    f"{localization.term}: {label} "
                    f"({data['start']:%d.%m} - {data['end']:%d.%m})"
                )
                total_price_text.value = f"{localization.total_to_be_paid}: {data['total']:.2f} {localization.currency}"

            form_error.update()
            dates_info_text.update()
            total_price_text.update()

        def on_date_change() -> None:
            start_button.text = (
                f"{localization.start}: {to_date(start_picker.value):%d.%m.%Y}"
            )
            end_button.text = (
                f"{localization.end}: {to_date(end_picker.value):%d.%m.%Y}"
            )
            start_button.update()
            end_button.update()
            recalculate_total()

        def on_tariff_change(e: ft.ControlEvent) -> None:
            tariff = e.control.value
            if tariff == "weekly":
                price_field.label = localization.cost_per_week
            elif tariff == "monthly":
                price_field.label = localization.cost_per_month
            else:
                price_field.label = localization.cost_per_period
            period_column.visible = tariff == "custom"

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

        async def on_click_save(e: ft.ControlEvent) -> None:
            data = calculate()
            if data is None:
                show_error(localization.invalid_input_greater_than_zero)
                return
            if data["count"] < 1:
                show_error(localization.rental_shorter_than_period)  # новый ключ
                return

            car_id = int(car_dropdown.value)
            tenant_id = int(tenant_dropdown.value)
            # Проверка пересечения с существующими арендами этой машины
            clash = db.scalars(
                select(Rental).where(
                    Rental.car_id == car_id,
                    Rental.start_date < data["end"],
                    Rental.end_date > data["start"],
                )
            ).first()
            if clash:
                show_error(localization.car_already_rented)  # новый ключ
                return

            db.add(
                Rental(
                    car_id=car_id,
                    tenant_id=tenant_id,
                    start_date=data["start"],
                    end_date=data["end"],
                    period=data["period"],
                    price_per_period=data["price"],
                    total_cost=data["total"],
                    notes=notes_field.value or None,
                )
            )
            db.commit()

            self.build_complete_snack_bar()
            await self.page.push_route("/rentals")

        save_button = ft.Button(
            localization.save, icon=ft.Icons.SAVE, on_click=on_click_save
        )

        content = ft.Column(
            [
                ft.Text(
                    f"📋 {localization.add_rental}", size=24, weight=ft.FontWeight.BOLD
                ),
                car_dropdown,
                tenant_dropdown,
                tariff_radio,
                period_column,
                price_field,
                manual_date_row,
                dates_info_text,
                total_price_text,
                notes_field,
                form_error,
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

    def build_rental_details_view(self, rental_id: int) -> ft.View:
        """Construct the rental details view with car, tenant and finance blocks.

        Args:
            rental_id (int): Primary key of the rental to display.

        Returns:
            ft.View: Details view, or the rentals list if the record does not exist.
        """
        with session_factory() as db:
            rental = db.get(Rental, rental_id)
            if rental is None:
                snack = ft.SnackBar(
                    ft.Text(localization.rental_not_found),  # новый ключ
                    bgcolor=ft.Colors.RED_500,
                    open=True,
                )
                self.page.overlay.append(snack)
                return self.build_rentals_view()

            car = db.get(Car, rental.car_id)
            tenant = db.get(Tenant, rental.tenant_id)

            # ASSUMPTION: модель платежей Payment с полями rental_id, tenant_id, amount
            paid = db.scalar(
                select(func.coalesce(func.sum(Payment.amount), 0)).where(
                    Payment.rental_id == rental.id
                )
            )

            # Долг водителя = сумма долгов по всем его арендам
            tenant_rentals = db.scalars(
                select(Rental).where(Rental.tenant_id == tenant.id)
            ).all()
            tenant_debt = 0
            for r in tenant_rentals:
                r_paid = db.scalar(
                    select(func.coalesce(func.sum(Payment.amount), 0)).where(
                        Payment.rental_id == r.id
                    )
                )
                tenant_debt += max(self._amount_due(r) - r_paid, 0)

            # Забираем всё нужное в простые значения, пока сессия открыта
            data = {
                "car_title": f"{car.brand} {car.model}",
                "plate": car.plate_number,
                "images": car.images,  # ASSUMPTION: имя поля с фото
                "tenant_name": tenant.name,
                "tenant_phone": tenant.phone_number,
                "start": rental.start_date,
                "end": rental.end_date,
                "period": rental.period,
                "price": rental.price_per_period,
                "total": rental.total_cost,
                "notes": rental.notes,
                "car_id": car.id,
                "tenant_id": tenant.id,
            }

        today = date.today()
        start = (
            data["start"].date()
            if isinstance(data["start"], datetime)
            else data["start"]
        )
        end = data["end"].date() if isinstance(data["end"], datetime) else data["end"]

        # Статус по датам
        if today < start:
            status_text, status_color = localization.status_upcoming, ft.Colors.BLUE_700
        elif today <= end:
            status_text, status_color = localization.status_active, ft.Colors.GREEN_700
        else:
            status_text, status_color = localization.status_finished, ft.Colors.GREY_700

        # Баланс: оплачено минус начислено на сегодня (минус = долг)
        balance = paid - self._amount_due(rental)

        # Дата следующего платежа: следующий период после полностью оплаченных
        next_payment = None
        if data["price"] > 0 and today <= end:
            paid_periods = paid // data["price"]
            candidate = start + timedelta(days=(paid_periods) * data["period"])
            if candidate < end:
                next_payment = candidate

        def info_row(label: str, value: str, color: str | None = None) -> ft.Row:
            return ft.Row(
                [
                    ft.Text(label, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Text(value, weight=ft.FontWeight.BOLD, color=color),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )

        # ---- Карточка автомобиля ----
        car_card = self.create_car_card(car, car.images)

        # car_card = ft.Card(
        #     content=ft.Container(
        #         padding=15,
        #         on_click=lambda _: self.page.run_task(
        #             self.page.push_route, f"/cars/{data['car_id']}"
        #         ),
        #         content=ft.Row(
        #             [
        #                 ft.Image(
        #                     src=data["photo"],
        #                     width=90,
        #                     height=90,
        #                     fit=ft.BoxFit.COVER,
        #                     border_radius=10,
        #                     error_content=ft.Icon(ft.Icons.DIRECTIONS_CAR, size=48),
        #                 )
        #                 if data["photo"]
        #                 else ft.Icon(ft.Icons.DIRECTIONS_CAR, size=48),
        #                 ft.Column(
        #                     [
        #                         ft.Text(
        #                             data["car_title"],
        #                             size=18,
        #                             weight=ft.FontWeight.BOLD,
        #                         ),
        #                         ft.Text(data["plate"], size=16),
        #                     ],
        #                     spacing=4,
        #                 ),
        #             ],
        #             spacing=15,
        #         ),
        #     )
        # )

        # ---- Карточка водителя ----
        tenant_card = self.create_tenant_card(tenant)

        # debt_color = ft.Colors.RED_700 if tenant_debt > 0 else ft.Colors.GREEN_700
        # tenant_card = ft.Card(
        #     content=ft.Container(
        #         padding=15,
        #         content=ft.Column(
        #             [
        #                 ft.Row(
        #                     [
        #                         ft.Icon(ft.Icons.PERSON, size=32),
        #                         ft.Text(
        #                             data["tenant_name"],
        #                             size=18,
        #                             weight=ft.FontWeight.BOLD,
        #                         ),
        #                     ]
        #                 ),
        #                 ft.TextButton(
        #                     data["tenant_phone"],
        #                     icon=ft.Icons.PHONE,
        #                     url=f"tel:{data['tenant_phone']}",
        #                 ),
        #                 info_row(
        #                     localization.current_debt,  # новый ключ
        #                     f"{tenant_debt:.2f} {localization.currency}",
        #                     debt_color,
        #                 ),
        #             ],
        #             spacing=6,
        #         ),
        #     )
        # )

        # ---- Финансы ----
        balance_color = ft.Colors.GREEN_700 if balance >= 0 else ft.Colors.RED_700
        finance_card = ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column(
                    [
                        info_row(localization.status, status_text, status_color),
                        info_row(localization.start, f"{start:%d.%m.%Y}"),
                        info_row(localization.end, f"{end:%d.%m.%Y}"),
                        info_row(
                            localization.balance,  # новый ключ
                            f"{balance:+.2f} {localization.currency}",
                            balance_color,
                        ),
                        info_row(
                            localization.total_cost,  # новый ключ
                            f"{data['total']:.2f} {localization.currency}",
                        ),
                        info_row(
                            localization.next_payment,  # новый ключ
                            f"{next_payment:%d.%m.%Y}" if next_payment else "—",
                        ),
                    ],
                    spacing=8,
                ),
            )
        )

        notes_block = (
            ft.Text(data["notes"], italic=True) if data["notes"] else ft.Container()
        )

        # ---- Удаление с подтверждением ----
        async def confirm_delete(e: ft.ControlEvent) -> None:
            with session_factory() as db:
                rental_to_delete = db.get(Rental, rental_id)
                if rental_to_delete:
                    db.delete(rental_to_delete)
                    db.commit()
            self.page.pop_dialog()
            self.build_complete_snack_bar()
            await self.page.push_route("/rentals")

        def close_dialog(e: ft.ControlEvent) -> None:
            self.page.pop_dialog()

        delete_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(localization.delete_rental_title),  # новый ключ
            content=ft.Text(localization.delete_rental_confirm),  # новый ключ
            actions=[
                ft.TextButton(localization.cancel, on_click=close_dialog),
                ft.TextButton(
                    localization.delete,
                    on_click=confirm_delete,
                    style=ft.ButtonStyle(color=ft.Colors.RED_500),
                ),
            ],
        )

        delete_button = ft.Button(
            localization.delete,
            icon=ft.Icons.DELETE,
            bgcolor=ft.Colors.RED_500,
            color=ft.Colors.WHITE,
            on_click=lambda _: self.page.show_dialog(delete_dialog),
        )

        content = ft.Column(
            [
                ft.Text(
                    f"📋 {localization.rental}", size=24, weight=ft.FontWeight.BOLD
                ),
                car_card,
                tenant_card,
                finance_card,
                notes_block,
                delete_button,
            ],
            spacing=15,
        )
        return ft.View(
            route=f"/rentals/{rental_id}",
            navigation_bar=self.get_nav_bar(3),
            controls=[ft.Container(content=content, padding=20)],
        )

    @staticmethod
    def _amount_due(rental: Rental) -> int:
        """Amount that should have been paid by today under the rental tariff.

        Counts every period that has already started, capped by the rental term.
        """
        today = date.today()
        start = (
            rental.start_date.date()
            if isinstance(rental.start_date, datetime)
            else rental.start_date
        )
        end = (
            rental.end_date.date()
            if isinstance(rental.end_date, datetime)
            else rental.end_date
        )
        if today < start or rental.period <= 0:
            return 0
        total_periods = max((end - start).days // rental.period, 0)
        started = (today - start).days // rental.period + 1
        return rental.price_per_period * min(started, total_periods)
