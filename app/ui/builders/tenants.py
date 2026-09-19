import flet as ft
from sqlalchemy.orm import Session
from sqlalchemy import select
import logging

from core.models import session_factory, Tenant
from services.localization import localization
from ui.builders.base import Builder


class TenantBuilder(Builder):
    def build_tenants_view(self, db: Session = session_factory()) -> ft.View:
        tenants_list = db.scalars(select(Tenant)).all()
        fab = self._build_fab("/add_tenant", localization.add_tenant)

        if not tenants_list:
            empty_message = self._build_not_data_container(
                ft.Icon(
                    ft.Icons.PERSON,
                    size=60,
                    color=ft.Colors.GREY_400,
                    align=ft.Alignment.CENTER,
                ),
                localization.no_added_tenants,
                localization.add_tenant,
                "/add_tenant",
            )
            return ft.View(
                route="/tenants",
                navigation_bar=self._get_nav_bar(2),
                controls=[
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.AppBar(
                                    title=ft.Text(
                                        f"👤 {localization.tenants}",
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

        def on_phone_number_tap(tenant_phone: str):
            self.page.clipboard.set(tenant_phone)
            snack = ft.SnackBar(localization.copied, open=True)
            self.page.overlay.append(snack)

        tenants_content = ft.Column(
            controls=[],
            expand=True,
        )

        for tenant in tenants_list:
            if not tenant.avatar:
                avatar = ft.CircleAvatar(
                    content=ft.Text(
                        tenant.last_name[0].upper(), size=50, color=ft.Colors.WHITE
                    ),
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
            tenant_card = ft.Container(
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
                                                weight="bold",
                                                width=200,
                                            ),
                                            ft.Text(
                                                tenant.phone_number,
                                                size=20,
                                                on_tap=lambda e: on_phone_number_tap(
                                                    tenant.phone_number
                                                ),
                                            ),
                                            ft.TextButton(
                                                ft.Text(localization.details, size=16),
                                                on_click=lambda e, t_id: self.page.go(
                                                    f"/tenants/{t_id}"
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
            tenants_content.controls.append(tenant_card)

        return ft.View(
            route="/tenants",
            navigation_bar=self._get_nav_bar(2),
            controls=[ft.Container(content=tenants_content)],
            floating_action_button=fab,
            floating_action_button_location=ft.FloatingActionButtonLocation.END_FLOAT,
        )

    def build_add_tenant_view(self, db: Session = session_factory()) -> ft.View:
        paths = {
            "avatar": None,
            "passport": None,
            "sub_passport": None,
            "drive_license": None
        }

        avatar_picker = ft.FilePicker()
        passport_picker = ft.FilePicker()
        sub_passport_picker = ft.FilePicker()
        drive_license_picker = ft.FilePicker()

        def make_picker_callback(picker: ft.FilePicker, path_key: str):
            async def callback(e):
                files = await picker.pick_files(
                    allow_multiple=False,
                    file_type=ft.FilePickerFileType.IMAGE
                )
                if files:
                    paths[path_key] = files[0].path
                    logging.info(f"Файл для {path_key} успешно сохранен: {paths[path_key]}")
            return callback

        pick_avatar_click = make_picker_callback(avatar_picker, "avatar")
        pick_passport_click = make_picker_callback(passport_picker, "passport")
        pick_sub_passport_click = make_picker_callback(sub_passport_picker, "sub_passport")
        pick_drive_license_click = make_picker_callback(drive_license_picker, "drive_license")

        async def save_tenant(e=None):
            new_tenant = Tenant(
                name=name_input.value.strip(),
                phone_number=phone_input.value,
                debt_sum=float(debt_sum_input.value) if debt_sum_input.value else 0.0,
            )
            db.add(new_tenant)
            db.commit()
            db.refresh(new_tenant)

            for img_category in ["avatar", "passport", "sub_passport", "drive_license"]:
                img_path = paths.get(img_category)

                if img_path:
                    await self.connector.save_image(
                        image_path=img_path,
                        object_id=new_tenant.id,
                        object_type="tenant",
                        category=img_category,
                        db=db
                    )

            self._build_complete_snack_bar()
            self.page.go("/tenants")

        name_input = ft.TextField(label=localization.fullname, width=300)

        phone_input = ft.TextField(label=localization.phone, width=300)
        debt_sum_input = ft.TextField(label=localization.debt_in_total, width=300)
        input = ft.Container(
            content=ft.Column(
                [
                    ft.Text(localization.new_tenant, size=24, weight="bold"),
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
                    ft.ElevatedButton(
                        localization.save,
                        icon=ft.Icons.SAVE,
                        on_click=save_tenant,
                    ),
                    ft.ElevatedButton(
                        localization.back,
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda e: self.page.go("/tenants"),
                    ),
                ],
                spacing=15,
            ),
            padding=40,
        )

        return ft.View(
            route="/add_tenant",
            navigation_bar=self._get_nav_bar(2),
            controls=[input],
        )
