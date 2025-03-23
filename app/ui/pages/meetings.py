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
        with ui.card().classes("w-full p-4 mb-3 rounded-lg shadow-md")\
            .style("border: 1px solid #e5e7eb;"):
            with ui.row().classes("flex items-center justify-between"):
                # Left side: Meeting details.
                with ui.column().classes("flex-1"):
                    ui.label(meeting['meeting_purpose'])\
                        .classes("font-bold text-lg")\
                        .style("color: #374151;")
                    ui.label(f"Starts at: {meeting['start_time']}")\
                        .classes("text-sm")\
                        .style("color: #6b7280;")
                    ui.label(f"With: {meeting['professor_name']}")\
                        .classes("text-sm")\
                        .style("color: #6b7280;")
                # Right side: Delete button.
                ui.button(
                    icon='delete',
                    on_click=lambda m=meeting['id']: delete_meeting(m, container),
                    color="red"
                )

async def delete_meeting(meeting_id, container):
    """
    Show a streamlined confirmation dialog before deleting a meeting.
    """
    with ui.dialog() as dialog:
            # HEADER
        with ui.card().style("width: 400px; padding: 0; overflow: hidden; border-radius: 8px;"):
            # Header with a gradient background, title, and close button.
            with ui.row().classes("w-full flex items-center justify-between px-4 py-2")\
                       .style("background: linear-gradient(135deg, #EF4444, #F87171);"):
                ui.label("⚠ Confirm Deletion").classes("text-h5 font-bold").style("color: white;")
                ui.button(icon="close", on_click=dialog.close)\
                  .props("flat color=white text-color=white")\
                  .style("font-size: 1.5rem;")

            # BODY
            with ui.column().classes("items-center px-6 py-8 gap-4"):
                ui.label("This action cannot be undone. Do you want to proceed?")\
                  .classes("text-center text-lg text-gray-700")

            # FOOTER — single action
            with ui.row().classes("justify-end px-4 py-3 items-center"):
                ui.button("Yes, Delete", on_click=lambda: confirm_delete(meeting_id, container, dialog))\
                  .classes("bg-green text-white hover:bg-blue-600 rounded-lg px-4 py-2")

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
        with ui.card().style("width: 400px; padding: 0; overflow: hidden; border-radius: 8px;"):
            # Header with a gradient background, title, and close button.
            with ui.row().classes("w-full flex items-center justify-between px-4 py-2")\
                .style("background: linear-gradient(to right, #3b82f6, #8b5cf6);"):
                ui.label("Your Meetings")\
                    .classes("text-h5 font-bold")\
                    .style("color: white;")
                ui.button(
                    icon='cancel',
                    on_click=dialog.close
                )\
                .style("background: transparent; color: white; border: none; font-size: 1.5rem;").props('flat color=transparent text-color=white')
            # Content container with padding.
            with ui.column().style("padding: 10px;"):
                container = ui.column()  # Container for the meetings list.
                await display_meetings(container)
    dialog.open()

def meetings_button():
    """
    Returns a button that opens the 'Your Meetings' dialog
    """
    return ui.button(icon='calendar_today', on_click=open_meetings_dialog)\
             .props("rounded")\
             .classes("bg-blue-500 text-white hover:bg-blue-600")
