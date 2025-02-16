from nicegui import ui, app
from fastapi import Depends, Request
from sqlalchemy.orm import Session
from app.auth.routes import get_db
import httpx
from datetime import datetime



@ui.page("/calendar")
def calendar_page(request: Request, db: Session = Depends(get_db)):
    # Logout Button
    with ui.row().classes("justify-between items-center p-5 bg-gray-100"):
        ui.label("📅 Meetly Calendar").classes("text-h4 font-bold absolute top-5 left-5")
        ui.button("Logout", on_click=lambda: ui.run_javascript("""
            localStorage.removeItem('token');
            localStorage.removeItem('role');
            alert('✅ Logged out successfully!');
            window.location.href = '/';
        """)).props("rounded").classes("bg-red-500 text-white hover:bg-red-600 absolute top-5 right-5")

    # Authentication Check
    ui.run_javascript("""
        if (!localStorage.getItem('token')) {
            localStorage.removeItem('role');  // Clear any role
            alert('❌ Unauthorized: Please log in first.');
            window.location.href = '/';  // Redirect to login
        }
    """)

    # Calendar HTML
    with ui.column().classes("p-5 full-height"):
        ui.html(open("app/ui/pages/calendar.html").read())  # Contains the <style> & #calendar container
        ui.add_body_html("""
            <script src="https://cdn.jsdelivr.net/npm/@fullcalendar/core@6.1.8/index.global.min.js" defer></script>
            <script src="https://cdn.jsdelivr.net/npm/@fullcalendar/daygrid@6.1.8/index.global.min.js" defer></script>
            <script src="https://cdn.jsdelivr.net/npm/@fullcalendar/timegrid@6.1.8/index.global.min.js" defer></script>
            <script src="https://cdn.jsdelivr.net/npm/@fullcalendar/interaction@6.1.8/index.global.min.js" defer></script>
            <script src="/static/scripts.js" defer></script>
        """)
    create_meeting_model()
    create_slot_modal()


def create_slot_modal():
    with ui.dialog() as dialog:
        with ui.card().style("width: 400px;"):
            ui.label("Create Slot").classes("text-h5 font-bold")
            start_time = ui.input("Starting Time (HH:MM)").props("type=time").classes("w-full")
            end_time = ui.input("End Time (HH:MM)").props("type=time").classes("w-full")
            date_label = ui.label("")  

            with ui.row().classes("justify-between mt-4"):
                ui.button("Cancel", on_click=dialog.close).classes("bg-gray-500 text-white hover:bg-gray-600")
                ui.button("Create", on_click=lambda: create_slot()).classes("bg-blue-500 text-white hover:bg-blue-600")

    @app.post("/open_create_slot_modal")
    async def open_create_slot_modal(data: dict):
        date_label.set_text(f"Selected Date: {data['date']}")
        dialog.open()
        
    async def create_slot():
    # Combine the selected date with the provided start and end times
        full_start = f"{date_label.text.split(': ')[1]}T{start_time.value}"  
        full_end = f"{date_label.text.split(': ')[1]}T{end_time.value}"     

        slot_data = {
            "start": full_start,
            "end": full_end
        }
        try:
            token = await ui.run_javascript("localStorage.getItem('token');")
            
            backend_url = "http://127.0.0.1:8000/api/auth/create_slot"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    backend_url,
                    json=slot_data,
                    headers={
                        "Authorization": f"Bearer {token}",  
                        "Content-Type": "application/json"
                    },
                )

            if response.status_code == 200:
                data = response.json()
                ui.notify("✅ Slot saved successfully", type="positive")
                dialog.close()  
                ui.run_javascript("window.calendar.refetchEvents();")
            else:
                error_message = response.json().get("detail", "Creating slot failed")
                ui.notify(f"❌ {error_message}", type="negative")
        except Exception as e:
            ui.notify(f"⚠ Error: {str(e)}", type="negative")


def create_meeting_model():
    with ui.dialog() as dialog:
        with ui.card().style("width: 400px;"):
            ui.label("Book a Meeting").classes("text-h5 font-bold")
            slot_details = ui.label("")
            professor_name_label = ui.label("")
            meeting_purpose = ui.input("Meeting Purpose").classes("w-full")

            with ui.row().classes("justify-between mt-4"):
                ui.button("Cancel", on_click=dialog.close).classes("bg-gray-500 text-white hover:bg-gray-600")
                ui.button("Book Meeting", on_click=lambda: book_meeting(slot_id, meeting_purpose.value, dialog)).classes("bg-blue-500 text-white hover:bg-blue-600")


    @app.post("/open_create_meeting_model")
    async def open_create_meeting_model(data: dict):
        slots = data.get("slots", [])  # Safely get the slots from the data
        print(slots)
        professor_name = data.get("professor_name", "Unknown Professor")
        
        if not slots or not isinstance(slots, list):
            # Notify the user if no slots are available
            ui.notify("No valid slots provided!", type="negative")
            return

        # Use the first slot from the list (or handle multiple slots differently if required)
        slot = slots[0]  # Assuming you want to work with the first slot

        # Parse the start and end times
        start_time = datetime.fromisoformat(slot["start_time"])
        end_time = datetime.fromisoformat(slot["end_time"])

        # Format the date and time
        date_str = start_time.strftime("%B %d, %Y")  # Example: February 27, 2025
        start_time_str = start_time.strftime("%I:%M %p")  # Example: 11:11 AM
        end_time_str = end_time.strftime("%I:%M %p")  # Example: 11:30 AM

        # Set the formatted details
        slot_details.set_text(f"Date: {date_str}\n Start Time: {start_time_str}\n End Time: {end_time_str}")
        professor_name_label.set_text(f"Professor: {professor_name}")
        dialog.open()


async def book_meeting(slot_id, meeting_purpose, dialog):
    meeting_data = {
        "slot_id": slot_id,
        "meeting_purpose": meeting_purpose,
    }
    try:
        token = await ui.run_javascript("localStorage.getItem('token');")
        backend_url = "http://127.0.0.1:8000/api/auth/book_slot"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                backend_url,
                json=meeting_data,
                headers={"Authorization": f"Bearer {token}"}
            )

        if response.status_code == 200:
            ui.notify("Meeting booked successfully!", type="positive")
            dialog.close()
        else:
            error_message = response.json().get("detail", "Error booking meeting.")
            ui.notify(f"Error: {error_message}", type="negative")
    except Exception as e:
        ui.notify(f"Error: {str(e)}", type="negative")
