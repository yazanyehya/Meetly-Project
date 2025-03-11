# app/ui/pages/meetings.py
from nicegui import ui
import httpx

async def get_meetings():
    """
    Fetch all meetings for the currently logged-in student.
    """
    try:
        token = await ui.run_javascript("localStorage.getItem('token');")
        backend_url = "http://127.0.0.1:8000/api/auth/student/meetings"
        async with httpx.AsyncClient() as client:
            response = await client.get(
                backend_url,
                headers={"Authorization": f"Bearer {token}"}
            )

        if response.status_code == 200:
            return response.json()  # List of meetings
        else:
            ui.notify("⚠ Error fetching meetings", type="negative")
            return []
    except Exception as e:
        ui.notify(f"⚠ Error: {str(e)}", type="negative")
        return []

async def display_meetings(container):
    """
    Populate the container with the user's existing meetings.
    """
    container.clear()
    meetings = await get_meetings()

    if not meetings:
        ui.label("No meetings found")
        return

    for meeting in meetings:
        with ui.row().classes("items-center gap-2"):
            ui.label(f"{meeting['meeting_purpose']} - {meeting['start_time']} ({meeting['professor_name']})")
            ui.button(
                icon='delete',
                on_click=lambda m=meeting['id']: delete_meeting(m, container),
                color="red"
            )

async def delete_meeting(meeting_id, container):
    """
    Show a confirmation dialog, then delete the meeting if confirmed.
    """
    with ui.dialog() as dialog:
        with ui.card().style("width: 400px; padding: 10px;"):
            ui.label("⚠ Confirm Deletion").classes("text-h5 font-bold")
            ui.label("Are you sure you want to delete this meeting?")

            with ui.row().classes("justify-between mt-4"):
                ui.button("❌ No", on_click=dialog.close)\
                  .classes("bg-gray-500 text-white hover:bg-gray-600")
                ui.button("✅ Yes", on_click=lambda: confirm_delete(meeting_id, container, dialog))\
                  .classes("bg-red-500 text-white hover:bg-red-600")

    dialog.open()

async def confirm_delete(meeting_id, container, dialog):
    """
    Actually delete the meeting after the user confirms.
    """
    try:
        token = await ui.run_javascript("localStorage.getItem('token');")
        backend_url = f"http://127.0.0.1:8000/api/auth/student/meetings/{meeting_id}"

        async with httpx.AsyncClient() as client:
            response = await client.delete(
                backend_url,
                headers={"Authorization": f"Bearer {token}"}
            )

        if response.status_code == 200:
            ui.notify("✅ Meeting deleted", type="positive")
            dialog.close()
            container.clear()
            await display_meetings(container)  # Refresh the UI
        else:
            ui.notify("⚠ Error deleting meeting", type="negative")
    except Exception as e:
        ui.notify(f"⚠ Error: {str(e)}", type="negative")

async def open_meetings_dialog():
    """
    Opens a dialog that shows the user's meetings.
    """
    with ui.dialog() as dialog:
        with ui.card().style("width: 400px; padding: 10px;"):
            ui.label("Your Meetings")
            container = ui.column()  # Container for meetings list
            await display_meetings(container)
            ui.button(icon='cancel', on_click=dialog.close)
    dialog.open()

def meetings_button():
    """
    Returns a button that opens the 'Your Meetings' dialog
    """
    return ui.button(icon='calendar_today', on_click=open_meetings_dialog)\
             .props("rounded")\
             .classes("bg-blue-500 text-white hover:bg-blue-600")
