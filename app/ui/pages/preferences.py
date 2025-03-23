# preferences.py
from nicegui import ui
import httpx

def preferences_dialog():
    dialog = ui.dialog()

    with dialog:
        # Card with a unified design: no extra padding at the top, rounded corners, and overflow hidden.
        with ui.card().style("width: 400px; padding: 0; overflow: hidden; border-radius: 8px;"):
            # Header with gradient background, title, and close icon.
            with ui.row().classes("w-full flex items-center justify-between px-4 py-2")\
                .style("background: linear-gradient(to right, #3b82f6, #8b5cf6);"):
                ui.label("Preferred Times")\
                    .classes("text-h5 font-bold")\
                    .style("color: white;")
                ui.button(icon='cancel', on_click=dialog.close)\
                    .style("background: transparent; color: white; border: none; font-size: 1.5rem;").props('flat color=transparent text-color=white')
            # Content area with padding.
            with ui.column().style("padding: 20px;"):
                # Container to show current preferred times.
                times_container = ui.column().classes("gap-2")
                # Date-time picker input.
                datetime_input = ui.input(label="Select Date & Time")\
                    .props('type=datetime-local')\
                    .classes("w-full")
                # Footer row with both Close and Save buttons.
                with ui.row().classes("flex items-center justify-between mt-4"):
                    ui.button('Save',
                            on_click=lambda: add_preferred_time(datetime_input, times_container)) \
                  .classes("bg-green text-white hover:bg-blue-600 rounded-lg px-4 py-2")
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
                if isinstance(data, dict) and "preferred_times" in data:
                    times_list = data["preferred_times"]
                elif isinstance(data, list):
                    times_list = data
                else:
                    times_list = []

                if times_list:
                    with times_container:
                        for t in times_list:
                            with ui.card().classes("w-full p-4 mb-3 rounded-lg shadow-md")\
                                    .style("border: 1px solid #e5e7eb;"):
                                with ui.row().classes("flex items-center justify-between"):
                                    ui.label(f"• {t['time_slot']}").classes("text-sm").style("color: #6b7280;")
                                    ui.button(
                                        icon="delete",
                                        color="red",
                                        on_click=lambda pref_id=t["id"], cont=times_container: delete_preference(pref_id, cont)
                                    )

                else:
                    with times_container:
                        ui.label("No preferred times found")
            else:
                ui.notify(f"Error fetching preferences: {response.text}", type="negative")

        except Exception as e:
            ui.notify(f"Error: {str(e)}", type="negative")

        dialog.open()

    async def delete_preference(pref_id, container):
        token = await ui.run_javascript("localStorage.getItem('token')")
        user_id = await ui.run_javascript("localStorage.getItem('user_id')")
        url = f"http://127.0.0.1:8000/api/auth/users/{user_id}/preferences/{pref_id}"
        async with httpx.AsyncClient() as client:
            response = await client.delete(url, headers={"Authorization": f"Bearer {token}"})
        if response.status_code == 200:
            ui.notify("✅ Preference deleted", type="positive")
            container.clear()
            await show_dialog()    # refresh list
        else:
            ui.notify("❌ Failed to delete", type="negative")

    async def add_preferred_time(date_input, container):
        """Take a single date/time from the input and send to the server."""
        raw_value = date_input.value.strip()  # e.g. "2025-03-10T14:30"
        if not raw_value:
            ui.notify("Please select a date/time.", type="warning")
            return

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
                    json={"time_slots": [raw_value]},  # Correct key matching FastAPI.
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                )

            if response.status_code == 200:
                ui.notify("Preferred time added!", type="positive")
                date_input.set_value("")
                container.clear()
                await show_dialog()  # Refresh to see updated list.
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
      .classes("bg-green-500 text-white hover:bg-green-600 transition duration-300")
