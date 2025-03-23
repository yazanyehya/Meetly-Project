from nicegui import ui
import httpx

async def fetch_unread_count():
    """Fetch the count of unread notifications from FastAPI."""
    user_id = await ui.run_javascript("localStorage.getItem('user_id');")
    if not user_id:
        return 0  # No user, no notifications

    backend_url = f"http://127.0.0.1:8000/api/auth/unread_count?user_id={user_id}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(backend_url)

    if response.status_code == 200:
        return response.json().get("unread_count", 0)  # Get count or return 0
    return 0


async def fetch_notifications():
    """Fetch unread notifications from FastAPI."""
    user_id = await ui.run_javascript("localStorage.getItem('user_id');")
    if not user_id:
        return []

    backend_url = f"http://127.0.0.1:8000/api/auth/notifications?user_id={user_id}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(backend_url)

    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list):
            return data  
        return []

    return []


async def respond_to_reschedule(notification_id, response_action):
    """'response_action' can be either 'accept' or 'reject'."""
    print(f"🔍 Sending response: {response_action} for reschedule ID: {notification_id}")

    token = await ui.run_javascript("localStorage.getItem('token');")
    if not token:
        ui.notify("❌ No token found in localStorage. Please log in.", type="negative")
        return

    backend_url = f"http://127.0.0.1:8000/api/auth/reschedule_requests/{notification_id}/{response_action}"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            backend_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
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
    """Loads notifications into the menu with updated design."""
    notifications = await fetch_notifications()
    menu.clear()

    with menu:
        ui.label("🔔 Notifications").classes("font-bold text-lg mb-2")
        ui.separator().style("margin-bottom: 8px;")

        if notifications:
            for notification in notifications:
                with ui.card().style("""
                    background: rgba(255, 255, 255, 0.9);
                    backdrop-filter: blur(10px);
                    border-radius: 12px;
                    box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
                    padding: 12px;
                    margin-bottom: 8px;
                """):
                    ui.label(notification["message"]).classes("text-md font-semibold text-gray-800")

                    with ui.row().classes("justify-between mt-2"):
                        ui.button("✅ Accept", on_click=lambda n=notification["reschedule_id"]: respond_to_reschedule(n, "accept"))\
                            .style("""
                                background: linear-gradient(to right, #10b981, #22c55e);
                                color: black;
                                padding: 8px 12px;
                                border-radius: 8px;
                                font-weight: bold;
                                transition: all 0.3s ease-in-out;
                            """)\
                            .on("mouseenter", lambda e: e.sender.set_style("background: linear-gradient(to right, #059669, #16a34a);"))\
                            .on("mouseleave", lambda e: e.sender.set_style("background: linear-gradient(to right, #10b981, #22c55e);"))

                        ui.button("❌ Reject", on_click=lambda n=notification["reschedule_id"]: respond_to_reschedule(n, "reject"))\
                            .style("""
                                background: linear-gradient(to right, #ef4444, #dc2626);
                                color: black;
                                padding: 8px 12px;
                                border-radius: 8px;
                                font-weight: bold;
                                transition: all 0.3s ease-in-out;
                            """)\
                            .on("mouseenter", lambda e: e.sender.set_style("background: linear-gradient(to right, #b91c1c, #991b1b);"))\
                            .on("mouseleave", lambda e: e.sender.set_style("background: linear-gradient(to right, #ef4444, #dc2626);"))

        else:
            ui.label("✅ No new notifications").classes("text-gray-500 text-sm")


def notification_button():
    """Creates a full-width notification button."""
    with ui.column().classes("w-full"):
        with ui.button("🔔 Notifications")\
            .props('flat color=transparent text-color=white')\
            .classes("w-full text-left custom-btn rounded-lg")\
            .style("width: 100%; border: 1px solid #ffffff;"):
            
            with ui.menu().props('auto-close').style("""
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 12px;
                padding: 12px;
                box-shadow: 0px 6px 14px rgba(0, 0, 0, 0.2);
            """) as menu:
                ui.timer(2, lambda: load_notifications(menu))
