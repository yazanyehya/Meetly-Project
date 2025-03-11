from nicegui import ui
import httpx

async def fetch_notifications():
    """Fetch unread notifications from FastAPI."""
    user_id = await ui.run_javascript("localStorage.getItem('user_id');")
    if not user_id:
        return []

    backend_url = f"http://127.0.0.1:8000/api/auth/notifications?user_id={user_id}"
    async with httpx.AsyncClient() as client:
        response = await client.get(backend_url)

    if response.status_code == 200:
        return response.json().get("notifications", [])
    return []

async def respond_to_reschedule(notification_id, response):
    """Send Accept/Reject response for rescheduling."""
    
    print(f"🔍 Sending response: {response} for reschedule ID: {notification_id}")  # ✅ Debugging

    backend_url = "http://127.0.0.1:8000/api/auth/response_to_rescheduling"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            backend_url,
            json={"reschedule_id": notification_id, "response": response},  # ✅ Ensure JSON format
            headers={"Content-Type": "application/json"}
        )

    if response.status_code == 200:
        ui.notify(f"✅ {response.json()['message']}", type="positive")
    else:
        ui.notify(f"❌ Error: {response.text}", type="negative")



async def mark_notification_as_read(notification_id):
    """Mark a notification as read in FastAPI."""
    backend_url = "http://127.0.0.1:8000/api/auth/notifications/mark_as_read"
    async with httpx.AsyncClient() as client:
        await client.post(backend_url, json={"notification_id": notification_id})

async def load_notifications(menu):
    notifications = await fetch_notifications()
    menu.clear()

    if notifications:
        for notification in notifications:
            with menu:
                ui.label(notification["message"])

                # ✅ Accept Button
                ui.button("✅ Accept", on_click=lambda n=notification["id"]: respond_to_reschedule(n, "accept"))\
                    .classes("bg-green-500 text-white hover:bg-green-600")

                # ❌ Reject Button
                ui.button("❌ Reject", on_click=lambda n=notification["id"]: respond_to_reschedule(n, "reject"))\
                    .classes("bg-red-500 text-white hover:bg-red-600")

    else:
        ui.label("✅ No new notifications")


def notification_button():
    """Creates a menu item to show notifications inside the menu."""

    with ui.row():
        with ui.button(icon="notifications").classes("bg-blue-500 text-white"):
            with ui.menu().props('auto-close') as menu:
                ui.label("🔔 Notifications").classes("text-bold")
                ui.separator()
                ui.timer(2, lambda: load_notifications(menu))  # Auto-refresh notifications
