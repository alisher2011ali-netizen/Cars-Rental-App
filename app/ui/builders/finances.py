import flet as ft
from core.models import Payment, PaymentType, session_factory
from services.localization import localization
from sqlalchemy import select
from sqlalchemy.orm import Session
from ui.builders.base import Builder


class FinanceBuilder(Builder):
    """Build UI views and workflows for financial records and statement processing."""

    def build_finances_view(self, db: Session | None = None) -> ft.View:
        """Construct the financial transactions overview screen with PDF import capabilities.

        Args:
            db (Session | None): Optional active database session. Defaults to None.

        Returns:
            ft.View: View containing the list of parsed/manual payments or an empty state.
        """
        if db is None:
            db = session_factory()

        payments_list = db.scalars(select(Payment)).all()
        title = ft.AppBar(
            leading=ft.Icon(
                icon=ft.Icons.ATTACH_MONEY,
                size=40,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            title=ft.Text(
                localization.finances,
                size=30,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
        )
        fab = self.build_fab("/add_payment", localization.add_operation)

        file_picker = ft.FilePicker()

        async def pick_pdf_click(e: ft.ControlEvent) -> None:
            """Open file picker to ingest a PDF bank statement and refresh the view on success.

            Args:
                e (ft.ControlEvent): Button click interaction event.

            Returns:
                None: Triggers parsing and refreshes finances view if parsing succeeded.
            """
            files = await file_picker.pick_files(
                allow_multiple=False,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["pdf"],
            )
            if not files:
                return
            file = files[0]
            # Refresh current view only on successful parse to reflect newly created transactions
            if self.connector.save_statement(file.path):
                await self.page.push_route("/finances")

        upload_button = ft.Button(
            "Загрузить выписку",
            icon=ft.Icons.UPLOAD_FILE,
            on_click=pick_pdf_click,
            align=ft.Alignment.TOP_RIGHT,
        )

        if not payments_list:
            return self.build_not_data_view(
                title=ft.Column([title, upload_button]),
                icon=ft.Icon(
                    ft.Icons.ATTACH_MONEY,
                    size=60,
                    color=ft.Colors.GREY_400,
                    align=ft.Alignment.CENTER,
                ),
                text=localization.no_operations_history,
                button_text=localization.add_operation,
                button_route="/add_payment",
                route="/finances",
                nav_bar_idx=4,
                fab=fab,
            )

        payments_content = ft.Container(
            content=ft.Column([upload_button], spacing=20),
            padding=5,
            expand=True,
        )

        for payment in payments_list:
            payment_card = self.create_payment_card(payment)
            payments_content.content.controls.append(payment_card)

        return ft.View(
            route="/finances",
            navigation_bar=self.get_nav_bar(4),
            controls=[title, payments_content],
            floating_action_button=fab,
            floating_action_button_location=ft.FloatingActionButtonLocation.END_FLOAT,
        )

    def build_add_payment_view(self, db: Session | None = None) -> ft.View:
        """Construct the manual payment logging screen with input validation.

        Args:
            db (Session | None): Optional active database session. Defaults to None.

        Returns:
            ft.View: View containing form fields for logging transactions.
        """
        if db is None:
            db = session_factory()

        async def save_payment(e: ft.ControlEvent) -> None:
            """Validate monetary inputs and persist a new payment transaction.

            Args:
                e (ft.ControlEvent): Form submit button interaction event.

            Returns:
                None: Validates input, writes to database, and navigates back.
            """
            # Reject non-digit inputs before database persistence to prevent cast exceptions
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
                notes=notes_input.value,
                type=payment_type,
            )
            db.add(new_payment)
            db.commit()

            self.page.overlay.append(self.build_complete_snack_bar())
            await self.page.push_route("/finances")

        amount_input = ft.TextField(label=localization.amount, width=300)
        notes_input = ft.TextField(label=localization.notes, width=300, multiline=True)
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
                        weight=ft.FontWeight.BOLD,
                    ),
                    amount_input,
                    notes_input,
                    type_dropdown,
                    error_container,
                    save_button,
                ],
            ),
            padding=40,
        )
        return ft.View(
            route="/add_payment",
            navigation_bar=self.get_nav_bar(4),
            controls=[ft.Container(content=content, alignment=ft.Alignment.CENTER)],
        )
