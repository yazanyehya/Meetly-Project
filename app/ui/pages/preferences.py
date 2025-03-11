# preferences.py
from nicegui import ui
import httpx

def preferences_dialog():
    dialog = ui.dialog()

    # We'll make the card a bit bigger:
    with dialog:
        with ui.card().style("width: 400px; padding: 20px;"):
            ui.label("Preferred Times").classes("text-h5 font-bold")

            # Container to show current preferred times
            times_container = ui.column().classes("gap-2")

            # Instead of a text input, use a date-time picker
            # Browser will show a combined date/time field
            datetime_input = ui.input(label="Select Date & Time").props('type=datetime-local').classes("w-full")

            with ui.row().classes("justify-between mt-4"):
                ui.button("Close", on_click=dialog.close).classes("bg-gray-500 text-white hover:bg-gray-600")
                ui.button("Save", on_click=lambda: add_preferred_time(datetime_input, times_container))\
                  .classes("bg-blue-500 text-white hover:bg-blue-600")

    async def show_dialog():
        """Open dialog and fetch existing preferences for display."""
        times_container.clear()

        token = await ui.run_javascript("localStorage.getItem('token');")
        user_id = await ui.run_javascript("localStorage.getItem('user_id');")

        if not user_id or not token:
            ui.notify("No user or token found. Please log in.", type="warning")
            return

        backend_url = f"http://127.0.0.1:8000/api/auth/users/{user_id}/preferences"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(backend_url, headers={"Authorization": f"Bearer {token}"})
            if response.status_code == 200:
                data = response.json()
                # data might be { "preferred_times": ["2025-03-10T14:30", ...] } or just a list
                if isinstance(data, dict) and "preferred_times" in data:
                    times_list = data["preferred_times"]
                elif isinstance(data, list):
                    times_list = data
                else:
                    times_list = []

                # Show each preferred time
                if times_list:
                    with times_container:
                        for t in times_list:
                            ui.label(f"• {t}")
                else:
                    with times_container:
                        ui.label("No preferred times found")
            else:
                ui.notify(f"Error fetching preferences: {response.text}", type="negative")

        except Exception as e:
            ui.notify(f"Error: {str(e)}", type="negative")

        dialog.open()

    async def add_preferred_time(date_input, container):
        """Take a single date/time from the input and send to the server."""
        raw_value = date_input.value.strip()  # e.g. "2025-03-10T14:30"
        if not raw_value:
            ui.notify("Please select a date/time.", type="warning")
            return

        # We'll just send it as a single-element list to the backend.
        # The backend can parse it however it wants (Time, DateTime, etc.)
        times = [raw_value]

        token = await ui.run_javascript("localStorage.getItem('token');")
        user_id = await ui.run_javascript("localStorage.getItem('user_id');")
        if not user_id or not token:
            ui.notify("No user or token found. Please log in.", type="warning")
            return

        backend_url = f"http://127.0.0.1:8000/api/auth/users/{user_id}/preferences"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    backend_url,
                    json={"times": times},
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                )

            if response.status_code == 200:
                ui.notify("Preferred time added!", type="positive")
                date_input.set_value("")
                container.clear()
                await show_dialog()  # Refresh to see updated list
            else:
                detail = response.json().get("detail", "Unknown error")
                ui.notify(f"Failed to add preference: {detail}", type="negative")

        except Exception as e:
            ui.notify(f"Error: {str(e)}", type="negative")

    return show_dialog


def preferences_button():
    """Create a button that opens the preferences dialog."""
    show_dialog_fn = preferences_dialog()
    ui.button("Set Preferred Times", on_click=show_dialog_fn)\
      .props("rounded")\
      .classes("bg-green-500 text-white hover:bg-green-600")
