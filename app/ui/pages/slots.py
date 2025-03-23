# app/ui/pages/slots.py

from nicegui import ui, app
import httpx

def create_slot_modal():
    """
    Creates a dialog for professors to create a new slot.
    """
    with ui.dialog() as dialog:
        with ui.card().style("width: 400px;"):
            ui.label("Create Slot").classes("text-h5 font-bold")
            start_time = ui.input("Starting Time (HH:MM)").props("type=time").classes("w-full")
            end_time = ui.input("End Time (HH:MM)").props("type=time").classes("w-full")
            date_label = ui.label("")

            with ui.row().classes("justify-between mt-4"):
                ui.button(icon='cancel', on_click=dialog.close)\
                  .classes("bg-gray-500 text-white hover:bg-gray-600")
                ui.button(icon='add', on_click=lambda: create_slot(start_time, end_time, date_label, dialog))\
                  .classes("bg-blue-500 text-white hover:bg-blue-600")

    @app.post("/open_create_slot_modal")
    async def open_create_slot_modal(data: dict):
        """
        Called from scripts.js when user clicks a date in the calendar
        """
        date_label.set_text(f"Selected Date: {data['date']}")
        dialog.open()

async def create_slot(start_time, end_time, date_label, dialog):
    """
    Actually create the slot after the user fills the form.
    """
    selected_date = date_label.text.split(': ')[1]  # e.g. "2025-03-02"
    full_start = f"{selected_date}T{start_time.value}"
    full_end   = f"{selected_date}T{end_time.value}"

    slot_data = {
        "start": full_start,
        "end":   full_end
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
            ui.notify("✅ Slot saved successfully", type="positive")
            dialog.close()
            # Refresh the calendar events in the browser
            ui.run_javascript("window.calendar.refetchEvents();")
        else:
            error_message = response.json().get("detail", "Creating slot failed")
            ui.notify(f"❌ {error_message}", type="negative")
    except Exception as e:
        ui.notify(f"⚠ Error: {str(e)}", type="negative")
