from collections.abc import Callable, Coroutine
from typing import Any

import flet as ft
from core.models import Tenant, session_factory
from services.localization import localization
from sqlalchemy import select
from sqlalchemy.orm import Session
from ui.builders.base import Builder


class TenantBuilder(Builder):
    """Build UI views and controls for tenant directory browsing and creation."""

    def build_tenants_view(self, db: Session | None = None) -> ft.View:
        """Construct the primary tenants listing view.

        Args:
            db (Session | None): Optional active database session. Defaults to None.

        Returns:
            ft.View: View containing the list of registered tenants or an empty placeholder.
        """
        if db is None:
            db = session_factory()

        tenants_list = db.scalars(select(Tenant)).all()
        fab = self.build_fab("/add_tenant", localization.add_tenant)
        title = ft.AppBar(
            leading=ft.Icon(
                icon=ft.Icons.PERSON,
                size=40,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            title=ft.Text(
                localization.tenants,
                size=30,
                weight=ft.FontWeight.BOLD,
            ),
        )

        if not tenants_list:
            return self.build_not_data_view(
                title=title,
                icon=ft.Icon(
                    ft.Icons.PERSON,
                    size=60,
                    color=ft.Colors.GREY_400,
                    align=ft.Alignment.CENTER,
                ),
                text=localization.no_added_tenants,
                button_text=localization.add_tenant,
                button_route="/add_tenant",
                route="/tenants",
                nav_bar_idx=2,
                fab=fab,
            )

        tenants_content = ft.Column(
            controls=[],
            expand=True,
        )

        for tenant in tenants_list:
            tenant_card = self.create_tenant_card(tenant)
            tenants_content.controls.append(tenant_card)

        return ft.View(
            route="/tenants",
            navigation_bar=self.get_nav_bar(2),
            controls=[title, ft.Container(content=tenants_content)],
            floating_action_button=fab,
            floating_action_button_location=ft.FloatingActionButtonLocation.END_FLOAT,
        )

    def build_add_tenant_view(self, db: Session | None = None) -> ft.View:
        """Construct the tenant creation form view with document upload handlers.

        Args:
            db (Session | None): Optional active database session. Defaults to None.

        Returns:
            ft.View: View containing input fields and file picker actions for registering a tenant.
        """
        if db is None:
            db = session_factory()

        paths = {
            "avatar": None,
            "passport": None,
            "sub_passport": None,
            "drive_license": None,
        }

        avatar_picker = ft.FilePicker()
        passport_picker = ft.FilePicker()
        sub_passport_picker = ft.FilePicker()
        drive_license_picker = ft.FilePicker()

        def make_picker_callback(
            picker: ft.FilePicker, path_key: str
        ) -> Callable[[ft.ControlEvent], Coroutine[Any, Any, None]]:
            """Generate an asynchronous file picker handler for a designated document category.

            Args:
                picker (ft.FilePicker): The target file picker control instance.
                path_key (str): The state dictionary key where the picked file path should be stored.

            Returns:
                Callable[[ft.ControlEvent], Coroutine[Any, Any, None]]: An async event handler.
            """

            async def callback(e: ft.ControlEvent) -> None:
                files = await picker.pick_files(
                    allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE
                )
                if files:
                    paths[path_key] = files[0].path

            return callback

        pick_avatar_click = make_picker_callback(avatar_picker, "avatar")
        pick_passport_click = make_picker_callback(passport_picker, "passport")
        pick_sub_passport_click = make_picker_callback(
            sub_passport_picker, "sub_passport"
        )
        pick_drive_license_click = make_picker_callback(
            drive_license_picker, "drive_license"
        )

        async def save_tenant(e: ft.ControlEvent | None = None) -> None:
            """Persist the new tenant and copy all chosen identity documents to local storage.

            Args:
                e (ft.ControlEvent | None): Optional event triggered by the form submission button. Defaults to None.

            Returns:
                None: Commits records and redirects to the tenants catalog.
            """
            new_tenant = Tenant(
                name=name_input.value.strip(),
                phone_number=phone_input.value,
                debt_sum=float(debt_sum_input.value) if debt_sum_input.value else 0.0,
            )
            db.add(new_tenant)
            db.commit()
            # Refresh to load server-generated identity columns required for child image links
            db.refresh(new_tenant)

            for img_category in ["avatar", "passport", "sub_passport", "drive_license"]:
                img_path = paths.get(img_category)

                if img_path:
                    await self.connector.save_image(
                        image_path=img_path,
                        object_id=new_tenant.id,
                        object_type="tenant",
                        category=img_category,
                        db=db,
                    )

            self.build_complete_snack_bar()
            await self.page.push_route("/tenants")

        name_input = ft.TextField(label=localization.fullname, width=300)

        phone_input = ft.TextField(label=localization.phone, width=300)
        debt_sum_input = ft.TextField(label=localization.debt_in_total, width=300)
        input = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        localization.new_tenant, size=24, weight=ft.FontWeight.BOLD
                    ),
                    name_input,
                    phone_input,
                    debt_sum_input,
                    ft.TextButton(
                        localization.upload_avatar,
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=pick_avatar_click,
                        margin=5,
                    ),
                    ft.TextButton(
                        localization.upload_passport,
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=pick_passport_click,
                        margin=5,
                    ),
                    ft.TextButton(
                        localization.upload_subpassport,
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=pick_sub_passport_click,
                        margin=5,
                    ),
                    ft.TextButton(
                        localization.upload_driver_license,
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=pick_drive_license_click,
                        margin=5,
                    ),
                    ft.Button(
                        localization.save,
                        icon=ft.Icons.SAVE,
                        on_click=save_tenant,
                    ),
                    ft.Button(
                        localization.back,
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda _: self.page.run_task(
                            self.page.push_route, "/tenants"
                        ),
                    ),
                ],
                spacing=15,
            ),
            padding=40,
        )

        return ft.View(
            route="/add_tenant",
            navigation_bar=self.get_nav_bar(2),
            controls=[input],
        )

    def build_tenant_details_view(
        self, tenant_id: int, db: Session | None = None
    ) -> ft.View:
        """Build a comprehensive tenant details view.

        Displays avatar, personal data, phone with clipboard copy,
        debt status, next rental payment info, documents gallery with fullscreen mode,
        and a direct navigation link to the active rental.

        Args:
            tenant_id (int): Identifier of the tenant to display.
            db (Session | None, optional): Database session instance. Defaults to None.

        Returns:
            ft.View: Configured Flet View instance.
        """
        if db is None:
            db = session_factory()

        tenant = db.get(Tenant, tenant_id)
        if not tenant:
            return ft.View(
                route=f"/tenants/{tenant_id}",
                controls=[
                    ft.AppBar(
                        title=ft.Text(localization.error),
                        leading=ft.IconButton(
                            ft.Icons.ARROW_BACK,
                            on_click=lambda _: self.page.run_task(
                                self.page.push_route, "/tenants"
                            ),
                        ),
                    ),
                    ft.Container(
                        content=ft.Text(
                            localization.tenant_not_found,
                            color=ft.Colors.ERROR,
                            size=18,
                            weight=ft.FontWeight.BOLD,
                        ),
                        alignment=ft.Alignment.CENTER,
                        padding=20,
                    ),
                ],
            )

        # --- 1. Аватар (если нет — блок пустой) ---
        avatar_img = getattr(tenant, "avatar", None)
        if not avatar_img and hasattr(tenant, "images"):
            avatar_img = next(
                (
                    img
                    for img in tenant.images
                    if getattr(img, "category", "") == "avatar"
                ),
                None,
            )

        if avatar_img:
            avatar_control = ft.Container(
                content=ft.CircleAvatar(
                    foreground_image_src=avatar_img.path,
                    radius=55,
                ),
                alignment=ft.Alignment.CENTER,
                margin=ft.Margin.only(top=10, bottom=15),
            )
        else:
            avatar_control = ft.Container()

        # --- 2. Документы и полноэкранная галерея ---
        doc_images = []
        if hasattr(tenant, "images"):
            doc_images = [
                img
                for img in tenant.images
                if img != avatar_img and getattr(img, "category", "") != "avatar"
            ]

        current_index = [0]
        gallery_img = ft.Image(
            src=doc_images[0].path if doc_images else "",
            fit=ft.BoxFit.CONTAIN,
            expand=True,
        )
        gallery_counter = ft.Text(
            size=16, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD
        )

        def update_gallery() -> None:
            if doc_images:
                gallery_img.src = doc_images[current_index[0]].path
                gallery_counter.value = f"{current_index[0] + 1} / {len(doc_images)}"
                gallery_img.update()
                gallery_counter.update()

        def close_gallery(e) -> None:
            gallery_overlay.visible = False
            self.page.update()

        def next_img(e) -> None:
            if current_index[0] < len(doc_images) - 1:
                current_index[0] += 1
                update_gallery()

        def prev_img(e) -> None:
            if current_index[0] > 0:
                current_index[0] -= 1
                update_gallery()

        def delete_img(e) -> None:
            # TODO: логика удаления документа из БД и ФС
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
            bgcolor=ft.Colors.with_opacity(0.95, ft.Colors.SURFACE),
            visible=False,
            expand=True,
            left=0,
            top=0,
            right=0,
            bottom=0,
        )

        if gallery_overlay not in self.page.overlay:
            self.page.overlay.append(gallery_overlay)

        def open_gallery(idx: int) -> None:
            if not doc_images:
                return
            current_index[0] = idx
            update_gallery()
            gallery_overlay.visible = True
            self.page.update()

        # --- 3. Информация о водителе ---
        def copy_phone(e) -> None:
            self.page.clipboard.set(tenant.phone_number)
            snack = ft.SnackBar(ft.Text(localization.copied), open=True)
            self.page.overlay.append(snack)

        phone_row = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.PHONE, size=18, color=ft.Colors.PRIMARY),
                    ft.Text(
                        tenant.phone_number,
                        size=16,
                        weight=ft.FontWeight.W_500,
                        color=ft.Colors.ON_SURFACE,
                    ),
                    ft.IconButton(
                        ft.Icons.COPY,
                        icon_color=ft.Colors.ON_SURFACE_VARIANT,
                        on_click=copy_phone,
                    ),
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            tooltip=localization.click_to_copy,
            padding=ft.Padding.symmetric(vertical=4, horizontal=10),
            border_radius=8,
        )

        debt_value = getattr(tenant, "debt_sum", 0) or 0
        has_debt = debt_value > 0
        debt_badge = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        f"{localization.debt}:",
                        size=14,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.Text(
                        f"{abs(debt_value):.2f} {localization.currency}",
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ERROR if has_debt else ft.Colors.GREEN_600,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border_radius=8,
        )

        # Поиск активной аренды
        active_rental = None
        if hasattr(tenant, "rentals") and tenant.rentals:
            active_rental = next(
                (
                    r
                    for r in tenant.rentals
                    if getattr(getattr(r, "status", None), "value", str(r.status))
                    == "active"
                ),
                None,
            )

        # Расчет / вывод следующей выплаты
        next_payment_control = ft.Container()
        if active_rental:
            next_date = getattr(active_rental, "next_payment_date", None) or getattr(
                active_rental, "end_date", None
            )
            next_date_str = (
                next_date.strftime("%d.%m.%Y")
                if hasattr(next_date, "strftime")
                else str(next_date or "—")
            )
            next_payment_control = ft.Container(
                content=ft.Row(
                    [
                        ft.Text(
                            f"{localization.next_payment}:",
                            size=14,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Text(
                            next_date_str,
                            size=15,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.PRIMARY,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                border_radius=8,
            )

        tenant_info_card = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        tenant.name,
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ON_SURFACE,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    phone_row,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    debt_badge,
                    next_payment_control,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
            ),
            padding=16,
            border_radius=12,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            margin=ft.Margin.symmetric(horizontal=5),
        )

        # --- 4. Список фото документов ---
        docs_row = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=10)
        if doc_images:
            for i, doc in enumerate(doc_images):
                docs_row.controls.append(
                    ft.GestureDetector(
                        content=ft.Container(
                            content=ft.Image(
                                src=doc.path,
                                width=110,
                                height=110,
                                fit=ft.BoxFit.COVER,
                                border_radius=8,
                            ),
                            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                            border_radius=8,
                        ),
                        on_tap=lambda _, idx=i: open_gallery(idx),
                    )
                )
        else:
            docs_row.controls.append(
                ft.Text(
                    localization.no_documents,
                    size=14,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                )
            )

        documents_block = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        localization.documents,
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ON_SURFACE,
                    ),
                    docs_row,
                ],
                spacing=10,
            ),
            padding=14,
            border_radius=12,
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            margin=ft.Margin.symmetric(horizontal=5),
        )

        # --- 5. Ссылка на активную аренду ---
        active_rental_btn = ft.Container()
        if active_rental:
            active_rental_btn = ft.Container(
                content=ft.Button(
                    f"{localization.current_rental} #{active_rental.id}",
                    icon=ft.Icons.KEY,
                    on_click=lambda _: self.page.run_task(
                        self.page.push_route, f"/rentals/{active_rental.id}"
                    ),
                    icon_color=ft.Colors.PRIMARY,
                ),
                margin=ft.Margin.symmetric(horizontal=5),
                alignment=ft.Alignment.CENTER,
            )

        # --- Диалог и кнопка удаления водителя ---
        def close_tenant_dialog(e):
            confirm_tenant_dialog.open = False
            self.page.update()

        async def delete_tenant_confirm(e):
            confirm_tenant_dialog.open = False
            db.delete(tenant)
            db.commit()
            self.page.update()
            await self.page.push_route("/tenants")

        confirm_tenant_dialog = ft.AlertDialog(
            title=ft.Text("Удалить профиль?"),
            content=ft.Text(f"Вы точно хотите удалить водителя {tenant.name}?"),
            actions=[
                ft.TextButton(localization.back, on_click=close_tenant_dialog),
                ft.TextButton(
                    "Удалить",
                    on_click=delete_tenant_confirm,
                    style=ft.ButtonStyle(color=ft.Colors.ERROR),
                ),
            ],
        )

        def open_tenant_delete_dialog(e):
            if confirm_tenant_dialog not in self.page.overlay:
                self.page.overlay.append(confirm_tenant_dialog)
            confirm_tenant_dialog.open = True
            self.page.update()

        delete_tenant_button = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_color=ft.Colors.ERROR,
            tooltip="Удалить водителя",
            on_click=open_tenant_delete_dialog,
        )

        return ft.View(
            route=f"/tenants/{tenant_id}",
            controls=[
                ft.AppBar(
                    leading=ft.IconButton(
                        ft.Icons.ARROW_BACK,
                        on_click=lambda _: self.page.run_task(
                            self.page.push_route, "/tenants"
                        ),
                    ),
                    title=ft.Text(
                        localization.tenant_details,
                        size=20,
                        weight=ft.FontWeight.BOLD,
                    ),
                    actions=[delete_tenant_button],
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            avatar_control,
                            tenant_info_card,
                            documents_block,
                            active_rental_btn,
                        ],
                        spacing=12,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    padding=ft.Padding.symmetric(vertical=10),
                    expand=True,
                ),
            ],
        )
