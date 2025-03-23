from nicegui import ui, app
import httpx


def create_meeting_model(slots, professor_name):
    """
    Build and open a dialog for booking a meeting or joining a waitlist.
    This updated function accepts available slots and the professor's name.
    """
    with ui.dialog() as dialog:
        with ui.card().style("width: 420px; border-radius: 12px; box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.15); background: white; padding: 20px;"):
            ui.label("📅 Book a Meeting")\
                .classes("text-h5 font-bold text-center")\
                .style("background: linear-gradient(to right, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;")
            ui.label(f"👨‍🏫 Professor: {professor_name}").classes("text-md font-semibold mt-2")

            slot_labels = []
            for i, slot in enumerate(slots):
                booking_status = "✅ BOOKED" if slot.get("is_booked") else "🟢 AVAILABLE"
                label_text = f"{i+1}. {slot.get('start_time')} - {slot.get('end_time')} ({booking_status})"
                slot_labels.append(label_text)

            slot_radio = ui.radio(slot_labels, value=None).classes("w-full mt-3")
            meeting_purpose_input = ui.input("📝 Meeting Purpose").classes("w-full mt-2")

            async def on_proceed():
                if not slot_radio.value:
                    ui.notify("⚠️ Please select a slot", type="warning")
                    return
                selected_index_str = slot_radio.value.split(".")[0]
                selected_index = int(selected_index_str) - 1
                chosen_slot = slots[selected_index]
                slot_id = chosen_slot.get("id")
                is_booked = chosen_slot.get("is_booked")
                meeting_purpose = meeting_purpose_input.value

                if not is_booked:
                    await book_meeting(slot_id, meeting_purpose, dialog)
                else:
                    await join_waitlist(slot_id, dialog)

            with ui.row().classes("justify-between mt-5 w-full"):
                ui.button("Cancel", on_click=dialog.close)\
                  .classes("bg-red text-white hover:bg-gray-600 rounded-lg px-4 py-2")
                ui.button("Proceed", on_click=on_proceed)\
                  .classes("bg-green text-white hover:bg-blue-600 rounded-lg px-4 py-2")
    dialog.open()

async def book_meeting(slot_id: int, meeting_purpose: str, dialog):
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
            ui.notify("🎉 Meeting booked successfully!", type="positive")
            dialog.close()
        else:
            error_message = response.json().get("detail", "Error booking meeting.")
            ui.notify(f"❌ Error: {error_message}", type="negative")
    except Exception as e:
        ui.notify(f"❌ Error: {str(e)}", type="negative")

async def join_waitlist(slot_id: int, dialog):
    try:
        token = await ui.run_javascript("localStorage.getItem('token');")
        backend_url = "http://127.0.0.1:8000/api/auth/add_to_waitlist"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                backend_url,
                json={"slot_id": slot_id},
                headers={"Authorization": f"Bearer {token}"}
            )

        if response.status_code == 200:
            ui.notify("📌 You have joined the waitlist!", type="positive")
            dialog.close()
        else:
            detail = response.json().get("detail", "Unknown error")
            ui.notify(f"❌ Error joining waitlist: {detail}", type="negative")
    except Exception as e:
        ui.notify(f"❌ Error: {str(e)}", type="negative")