import flet as ft
from core.models import Tenant, session_factory
from services.localization import localization
from sqlalchemy import select
from sqlalchemy.orm import Session
from ui.builders.base import Builder


class TenantBuilder(Builder):
    def build_tenants_view(self, db: Session | None = None) -> ft.View:
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

        def make_picker_callback(picker: ft.FilePicker, path_key: str):
            async def callback(e):
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
