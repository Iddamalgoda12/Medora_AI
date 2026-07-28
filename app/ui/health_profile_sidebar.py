"""
health_profile_sidebar.py  (UI helper)
-------------------------------
Renders the patient health profile in the Chainlit sidebar.
Reads the current data from ``data/health_profile.json`` via the
health_profile_manager, falling back gracefully if the file is absent.
"""

import chainlit as cl

from app.ui.health_profile_manager import (
    load_health_profile,
    format_profile_for_sidebar,
)


async def show_health_profile_sidebar() -> None:
    """Fetch the current profile from disk and refresh the sidebar panel."""
    profile = load_health_profile()
    markdown = format_profile_for_sidebar(profile)

    await cl.ElementSidebar.set_elements(
        [
            cl.Text(
                name="health_profile",
                content=markdown,
                display="inline",
            )
        ]
    )
