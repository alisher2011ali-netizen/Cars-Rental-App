import flet as ft
from core.models import Payment, PaymentType, session_factory
from services.localization import localization
from sqlalchemy import select
from sqlalchemy.orm import Session
from ui.builders.base import Builder


class FinanceBuilder(Builder):
    def build_finances_view(self, db: Session | None = None) -> ft.View:
        if db is None:
            db = session_factory()

        payments_list = db.scalars(select(Payment)).all()
        title = ft.Text(
            f"💰 {localization.finances}",
            size=24,
            weight="bold",
            color=ft.Colors.BLACK,
        )
        fab = self._build_fab("/add_payment", localization.add_operation)

        file_picker = ft.FilePicker()

        async def pick_pdf_click(e):
            files = await file_picker.pick_files(
                allow_multiple=False, file_type=ft.FilePickerFileType.ANY
            )
            file = files[0]
            if self.connector.save_statement(file.path):
                self.page.update()

        upload_button = ft.TextButton(
            "Импортировать выписку PDF",
            icon=ft.Icons.UPLOAD_FILE,
            on_click=pick_pdf_click,
            align=ft.Alignment.TOP_RIGHT,
        )

        if not payments_list:
            empty_message = self._build_not_data_container(
                ft.Icon(
                    ft.Icons.ATTACH_MONEY,
                    size=60,
                    color=ft.Colors.GREY_400,
                    align=ft.Alignment.CENTER,
                ),
                localization.no_operations_history,
                localization.add_operation,
                "/add_payment",
            )
            return ft.View(
                route="/finances",
                navigation_bar=self._get_nav_bar(4),
                controls=[
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.AppBar(
                                    title=ft.Text(
                                        f"💰 {localization.finances}",
                                        size=24,
                                        weight="bold",
                                    )
                                ),
                                upload_button,
                                empty_message,
                            ]
                        ),
                        alignment=ft.Alignment.CENTER,
                    )
                ],
                floating_action_button=fab,
                floating_action_button_location=ft.FloatingActionButtonLocation.END_FLOAT,
            )

        payments_content = ft.Container(
            content=ft.Column([title, upload_button], spacing=20),
            padding=5,
            expand=True,
        )

        for payment in payments_list:
            payment_type = "+" if payment.type == PaymentType.income else "-"

            text_color = (
                ft.Colors.PRIMARY
                if payment.type == PaymentType.income
                else ft.Colors.ERROR
            )

            # 1. Избавляемся от двойных минусов с помощью abs()
            # 2. Форматируем до 2 знаков после запятой и отрезаем пустые нули на конце
            formatted_amount = f"{abs(payment.amount):.2f}".rstrip("0").rstrip(".")

            if not payment.is_parsed:
                payment_card = ft.Container(
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
                                f"{localization.comment}:\n{payment.comment}",
                                size=14,
                                color=ft.Colors.ON_SURFACE_VARIANT,  # Теперь текст не сольется с фоном
                            ),
                        ],
                        spacing=5,
                    ),
                    bgcolor=ft.Colors.SECONDARY_CONTAINER,
                    padding=10,
                    border_radius=8,
                    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                )
                payments_content.content.controls.append(payment_card)

            elif payment.is_parsed:
                op_date_str = (
                    payment.operation_date.strftime("%d.%m.%Y %H:%M")
                    if payment.operation_date
                    else ""
                )

                payment_card = ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Row(
                                        [
                                            ft.Text(
                                                f"{payment_type}{formatted_amount}",  # Используем отформатированную сумму
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
                                                "Сбербанк",
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
                                payment.description or "Без описания",
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
                payments_content.content.controls.append(payment_card)

        return ft.View(
            route="/finances",
            navigation_bar=self._get_nav_bar(4),
            controls=[payments_content],
            floating_action_button=fab,
            floating_action_button_location=ft.FloatingActionButtonLocation.END_FLOAT,
        )

    def build_add_payment_view(self, db: Session | None = None) -> ft.View:
        if db is None:
            db = session_factory()

        def save_payment(e):
            if not amount_input.value.isdigit():
                amount_input.value = ""
                error_text.value = f"{localization.amount_only_can_be_digit}!"
                error_container.visible = True
                self.page.update()
                return

            payment_type = (
                PaymentType.income
                if type_dropdown.value == "income"
                else PaymentType.expense
            )
            new_payment = Payment(
                amount=amount_input.value,
                comment=comment_input.value,
                type=payment_type,
            )
            db.add(new_payment)
            db.commit()

            self.page.overlay.append(self._build_complete_snack_bar())
            self.page.push_route("/finances")

        amount_input = ft.TextField(label=localization.amount, width=300)
        comment_input = ft.TextField(label=localization.comment, width=300)
        type_dropdown = ft.Dropdown(
            options=[
                ft.DropdownOption(key="income", text=localization.income),
                ft.DropdownOption(key="expense", text=localization.expense),
            ],
            value="income",
            width=200,
        )
        error_text = ft.Text(
            value="",
            color=ft.Colors.WHITE,
            size=13,
            expand=True,
        )

        error_container = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.WHITE, size=20),
                    error_text,
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            width=300,
            bgcolor=ft.Colors.RED_400,
            border_radius=8,
            padding=8,
            visible=False,
        )
        save_button = ft.Button(
            localization.save,
            icon=ft.Icons.SAVE,
            on_click=save_payment,
        )

        content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        f"💰 {localization.new_operation}",
                        size=24,
                        weight="bold",
                    ),
                    amount_input,
                    comment_input,
                    type_dropdown,
                    error_container,
                    save_button,
                ],
            ),
            padding=40,
        )
        return ft.View(
            route="/add_payment",
            navigation_bar=self._get_nav_bar(4),
            controls=[ft.Container(content=content, alignment=ft.Alignment.CENTER)],
        )
