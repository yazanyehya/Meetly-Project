# app/ui/pages/slots.py

from nicegui import ui
import httpx

def create_slot_modal(date: str):
    """
    Opens a beautifully styled dialog for professors to create a new availability slot on a given date.
    """
    with ui.dialog() as dialog:
        with ui.card().style(
            "width: 420px; border-radius: 12px; "
            "box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.15); "
            "background: white; padding: 20px;"
        ):
            ui.label("🗓 Create New Slot")\
                .classes("text-h5 font-bold text-center")\
                .style(
                    "background: linear-gradient(to right, #3b82f6, #8b5cf6); "
                    "-webkit-background-clip: text; -webkit-text-fill-color: transparent;"
                )
            ui.label(f"📅 Date: {date}").classes("text-md font-semibold mt-2")

            start_time = ui.input("Start Time (HH:MM)").props("type=time").classes("w-full mt-3")
            end_time   = ui.input("End Time (HH:MM)").props("type=time").classes("w-full mt-2")

            async def on_create():
                if not start_time.value or not end_time.value:
                    ui.notify("⚠ Please fill both start and end times", type="warning")
                    return
                await create_slot(date, start_time.value, end_time.value, dialog)

            with ui.row().classes("justify-between mt-5 w-full"):
                ui.button("Cancel", on_click=dialog.close)\
                  .classes("bg-red text-white hover:bg-gray-600 rounded-lg px-4 py-2")
                ui.button("Create Slot", on_click=on_create)\
                  .classes("bg-green text-white hover:bg-blue-600 rounded-lg px-4 py-2")

    dialog.open()


async def create_slot(date: str, start: str, end: str, dialog):
    """
    Sends new slot data to the backend API.
    """
    slot_data = {"start": f"{date}T{start}", "end": f"{date}T{end}"}
    try:
        token = await ui.run_javascript("localStorage.getItem('token');")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://127.0.0.1:8000/api/auth/create_slot",
                json=slot_data,
                headers={"Authorization": f"Bearer {token}"}
            )
        if response.status_code == 200:
            ui.notify("✅ Slot created successfully!", type="positive")
            dialog.close()
            ui.run_javascript("window.calendar.refetchEvents();")
        else:
            ui.notify(f"❌ {response.json().get('detail', 'Failed to create slot')}", type="negative")
    except Exception as e:
        ui.notify(f"⚠ Error: {e}", type="negative")