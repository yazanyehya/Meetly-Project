from nicegui import ui, app
from fastapi import Depends, Request
from sqlalchemy.orm import Session
from app.auth.routes import get_db

# Import separate modules
from app.ui.pages.preferences import preferences_dialog
from app.ui.pages.meetings import open_meetings_dialog
from app.ui.pages.slots import create_slot_modal  # Function to open the slot modal
from app.ui.pages.booking import create_meeting_model as meeting_model_func  # Updated to accept parameters
from app.ui.pages.notifications import notification_button  # Notification button

import httpx

# Global container for modals; this will be set in the UI context
modal_container = None

# Add custom CSS for buttons
ui.add_head_html("""
<style>
.custom-btn {
  width: 100%;
  text-align: left;
  padding: 0.7rem 1rem;
  border: none;
  font-weight: 600;
  color: white;
  background: white;
  transition: all 0.3s ease;
}

.custom-btn:hover {
  background: rgba(255, 255, 255, 0.25); /* Slightly lighter on hover */
}
</style>
""")

@ui.page("/calendar")
def calendar_page(request: Request, db: Session = Depends(get_db)):
    global modal_container  # make available for endpoint use

    # Initialize the preferences dialog.
    open_preferences_dialog = preferences_dialog()

    ui.run_javascript("""
        if (!localStorage.getItem('token')) {
            localStorage.removeItem('role');
            alert('❌ Unauthorized: Please log in first.');
            window.location.href = '/';
        }
    """)

    with ui.row().classes("flex flex-row h-screen"):
        # Sidebar with creative design: gradient background and a welcome message.
        with ui.column().classes("bg-gradient-to-b from-blue-500 to-purple-600 text-white relative z-20 flex flex-col justify-between")\
            .style("margin-left: -2vw; padding: 1vw; margin-top: -2vw; height: 102vh; width: 22vw"):
            with ui.column():
                ui.label("Meetly Dashboard").classes("text-xl font-extrabold mb-6 text-center")
                with ui.column().classes("space-y-4"):
                    notification_button()
                    ui.colors(accent='transparent')
                    ui.button("🗓️ View Your Meetings", on_click=open_meetings_dialog)\
                        .props('flat color=transparent text-color=white')\
                        .classes("w-full text-left custom-btn rounded-lg ").style("border: 1px solid #ffffff;")
                    ui.button("⏳ Set Your Preferred Time", on_click=open_preferences_dialog).props('flat color=transparent text-color=white')\
                        .classes("w-full text-left custom-btn rounded-lg ").style("border: 1px solid #ffffff;")
                    ui.button("🚪 Sign Out", on_click=lambda: ui.run_javascript("""
                        localStorage.removeItem('token');
                        localStorage.removeItem('role');
                        window.location.href = '/';
                    """)).props('flat color=transparent text-color=white').classes("w-full text-left custom-btn rounded-lg ").style("border: 1px solid #ffffff;")
            # Welcome message and image in the sidebar.
            ui.image("https://media-hosting.imagekit.io//0cc37fdd83ca4138/Virtual-Meeting-Transparent-Computer-PNG.png?Expires=1836771514&Key-Pair-Id=K2ZIVPTIP2VGHC&Signature=i40Z-y4fh8ApFfVIy~rSsckx2VsllOigrd83tpl3mxQOygmIEaxPxrkZB4Un7ACWFlqzG5ryA1KrlontV2inMgPFmzrPPDVVwiDkorjZEWG8-iawqhDla41WLRWpa7xAS0RrEdjuXLaLvBfnaq9Yhaa4x1guGGQTYb0P-tv4EuA5tg6SHJnpL36AnLyEfnmfcmu-rVNbMaVZGlEjGd4y9~2euXfuTOdf-NXlty4R20GHv64d~gjKg7pEcgcupMpVGiVMtG0AUocsPQG3dun5f~fA8xtoJtc~iWgWPF2ayPMcIr8WQlYWmY-8kcnH74h3TBomxrZNer86zcGkvwcvgw__")\
                .style("width: 10vw; height: 15vh; object-fit: contain;")\
                .classes("mx-auto my-10")

        with ui.column().classes("w-full h-full justify-between"):
            with ui.column().classes("p-5 full-height"):
                with open("app/ui/pages/calendar.html", "r", encoding="utf-8") as f:
                                    ui.html(f.read())                
                ui.add_body_html("""
                    <script src="https://cdn.jsdelivr.net/npm/@fullcalendar/core@6.1.8/index.global.min.js" defer></script>
                    <script src="https://cdn.jsdelivr.net/npm/@fullcalendar/daygrid@6.1.8/index.global.min.js" defer></script>
                    <script src="https://cdn.jsdelivr.net/npm/@fullcalendar/timegrid@6.1.8/index.global.min.js" defer></script>
                    <script src="https://cdn.jsdelivr.net/npm/@fullcalendar/interaction@6.1.8/index.global.min.js" defer></script>
                    <script src="/static/scripts.js" defer></script>
                """)
            # Create a container for modals. This container is now part of the UI slot.
            modal_container = ui.column()

# ------------------------------------------------
# FastAPI Endpoints for Calendar Interaction
# ------------------------------------------------

# Endpoint for opening the meeting modal (for students).
@app.post("/open_create_meeting_model")
async def open_create_meeting_model(data: dict):
    global modal_container
    slots = data.get("slots", [])
    professor_name = data.get("professor_name", "Unknown Professor")
    if not slots:
        ui.notify("No valid slots provided!", type="negative")
        return {"message": "No valid slots provided"}
    # Use the modal container as the explicit slot for creating the dialog.
    with modal_container:
        meeting_model_func(slots, professor_name)
    return {"message": "Meeting modal opened"}

# Endpoint for opening the slot modal (for professors).
@app.post("/open_create_slot_modal")
async def open_create_slot_modal(data: dict):
    global modal_container
    date_clicked = data.get("date")
    if not date_clicked:
        ui.notify("No date provided!", type="negative")
        return {"message": "No date provided"}
    # Use the same or a separate container as needed.
    with modal_container:
        create_slot_modal(date_clicked)  # Pass the date if needed
    return {"message": "Slot modal opened"}