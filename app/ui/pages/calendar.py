# app/ui/pages/calendar.py
from nicegui import ui, app
from fastapi import Depends, Request
from sqlalchemy.orm import Session
from app.auth.routes import get_db

# Import separate modules
from app.ui.pages.preferences import preferences_dialog
from app.ui.pages.meetings import open_meetings_dialog
from app.ui.pages.slots import create_slot_modal
from app.ui.pages.booking import create_meeting_model
from app.ui.pages.notifications import notification_button  # Import the notification button

@ui.page("/calendar")
def calendar_page(request: Request, db: Session = Depends(get_db)):
    # Get the async functions for dialogs
    open_preferences_dialog = preferences_dialog()

    with ui.row().classes("justify-between items-center p-5 bg-gray-100"):
        # LEFT: Calendar Title
        ui.label("📅 Meetly Calendar").classes("text-h4 font-bold")

        # RIGHT: Menu Button with Logout, Meetings, Preferences, and Notifications
        with ui.button(icon='menu').classes("bg-red-500 text-white hover:bg-red-600 absolute top-5 right-5"):
            with ui.menu().props('auto-close'):
                notification_button()  # Calling the notification button from notifications.py
                ui.menu_item("📅 Meetings", on_click=open_meetings_dialog)
                ui.menu_item("⏳ Set Preferred Time", on_click=open_preferences_dialog)
                ui.menu_item("🚪 Logout", on_click=lambda: ui.run_javascript("""
                    localStorage.removeItem('token');
                    localStorage.removeItem('role');
                    alert('✅ Logged out successfully!');
                    window.location.href = '/';
                """))

    # Authentication Check (client-side)
    ui.run_javascript("""
        if (!localStorage.getItem('token')) {
            localStorage.removeItem('role');
            alert('❌ Unauthorized: Please log in first.');
            window.location.href = '/';
        }
    """)

    # The calendar markup, scripts, etc.
    with ui.column().classes("p-5 full-height"):
        ui.html(open("app/ui/pages/calendar.html").read())
        ui.add_body_html("""
            <script src="https://cdn.jsdelivr.net/npm/@fullcalendar/core@6.1.8/index.global.min.js" defer></script>
            <script src="https://cdn.jsdelivr.net/npm/@fullcalendar/daygrid@6.1.8/index.global.min.js" defer></script>
            <script src="https://cdn.jsdelivr.net/npm/@fullcalendar/timegrid@6.1.8/index.global.min.js" defer></script>
            <script src="https://cdn.jsdelivr.net/npm/@fullcalendar/interaction@6.1.8/index.global.min.js" defer></script>
            <script src="/static/scripts.js" defer></script>
        """)

    # Initialize modals for creating and booking
    create_meeting_model()
    create_slot_modal()
