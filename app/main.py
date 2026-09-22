import logging
import os

import flet as ft
from core.logging import setup_logging
from core.models import init_db
from ui.router import UIRouter


async def main(page: ft.Page):
    try:
        logger = logging.getLogger(__name__)

        init_db()

        current_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(
            current_dir, "assets", "fonts", "NotoSansSC-Regular.ttf"
        )

        page.fonts = {"NotoSansSC": font_path}
        page.theme = ft.Theme(
            font_family="NotoSansSC",
            page_transitions=ft.PageTransitionsTheme(
                android=ft.PageTransitionTheme.NONE, linux=ft.PageTransitionTheme.NONE
            ),
        )
        page.window.width = 360
        page.window.height = 780
        ui = UIRouter(page)
        await ui.build()

    except Exception:
        logger.exception("An unexpected error occurred while running the app.")


if __name__ == "__main__":
    setup_logging()
    print("The app has been setup")
    ft.run(main=main)
