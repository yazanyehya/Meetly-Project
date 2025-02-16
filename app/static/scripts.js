// scripts.js
document.addEventListener('DOMContentLoaded', function () {
    const calendarEl = document.getElementById('calendar');
    if (!calendarEl) {
        console.error("No #calendar element found!");
        return;
    }

    // 1) Read user role from localStorage
    const userRole = localStorage.getItem('role');
    console.log('User role from localStorage:', userRole);

    // 2) Configure FullCalendar
    const calendarOptions = {
        initialView: 'dayGridMonth',
        height: "100%",
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay',
        },
        // 3) Load unbooked slots from the server
        events: async function (fetchInfo, successCallback, failureCallback) {
            try {
                const response = await fetch('/api/auth/get_slots', {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    },
                });
                const slots = await response.json();

                // Group slots by date
                const events = Object.entries(
                    slots.reduce((acc, slot) => {
                        const date = slot.start_time.split('T')[0]; // Extract the date portion
                        acc[date] = (acc[date] || 0) + 1; // Count the number of slots per date
                        return acc;
                    }, {})
                ).map(([date, count]) => ({
                    title: `${count} Slots`, // Display the count
                    start: date, // Use the date as the event start time
                    backgroundColor: 'green', // Green background for the event
                }));

                successCallback(events);
            } catch (error) {
                console.error('Error fetching slots:', error);
                failureCallback(error);
            }
        },
    };

    // Unified dateClick handler for both professors and students
    calendarOptions.dateClick = function (info) {
        if (userRole === 'professor') {
            console.log('Professor clicked a date:', info.dateStr);
            // Trigger the NiceGUI backend to open the modal for creating a slot
            fetch('/open_create_slot_modal', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
                body: JSON.stringify({ date: info.dateStr }),
            }).catch(error => console.error('Error opening create slot modal:', error));
        } else if (userRole === 'student') {
            console.log('Student clicked a date:', info.dateStr);
            // Fetch available slots for the selected date
            fetch('/api/auth/get_slots', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                },
            })
                .then(response => response.json())
                .then(slots => {
                    // Filter slots for the clicked date
                    const availableSlots = slots.filter(slot => slot.start_time.startsWith(info.dateStr));
                    if (availableSlots.length > 0) {
                        // Send available slots to the backend to open the modal for booking a meeting
                        fetch('/open_create_meeting_model', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                            },
                            body: JSON.stringify({
                                slots: availableSlots,
                            }),
                        }).catch(error => console.error('Error opening create meeting modal:', error));
                    } else {
                        alert("No available slots on this date.");
                    }
                })
                .catch(error => console.error('Error fetching slots:', error));
        } else {
            console.warn("Unhandled user role:", userRole);
        }
    };

    // 6) Create and render the calendar
    const calendar = new FullCalendar.Calendar(calendarEl, calendarOptions);
    calendar.render();
});

// Optional: Modal utility
function openSlotModal(content) {
    const modal = document.createElement('div');
    modal.id = 'slot-modal';
    modal.style.position = 'fixed';
    modal.style.top = '50%';
    modal.style.left = '50%';
    modal.style.transform = 'translate(-50%, -50%)';
    modal.style.padding = '20px';
    modal.style.backgroundColor = 'white';
    modal.style.borderRadius = '8px';
    modal.style.boxShadow = '0px 5px 15px rgba(0,0,0,0.3)';
    modal.style.zIndex = 1000;

    modal.innerHTML = `
        ${content}
        <button style="margin-top: 15px; background-color: #dc3545; color: white; padding: 10px 15px; border: none; border-radius: 6px; cursor: pointer;" onclick="document.getElementById('slot-modal').remove()">Close</button>
    `;
    document.body.appendChild(modal);
}
