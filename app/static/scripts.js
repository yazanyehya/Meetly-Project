document.addEventListener("DOMContentLoaded", function () {
  const calendarEl = document.getElementById("calendar");
  if (!calendarEl) {
    console.error("No #calendar element found!");
    return;
  }

  // 1) Read user role from localStorage
  const userRole = localStorage.getItem("role");
  console.log("User role from localStorage:", userRole);

  // 2) Configure FullCalendar
  const calendarOptions = {
    initialView: "dayGridMonth",
    height: "100%",
    headerToolbar: {
      left: "prev,next",
      center: "title",
      right: "", // Remove view buttons
    },
    
    events: async function (fetchInfo, successCallback, failureCallback) {
      try {
        const response = await fetch("/api/auth/get_slots", {
          method: "GET",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        });
        const slots = await response.json();

        // 🔹 Count slots per day
        const slotsByDate = {};
        slots.forEach((slot) => {
          const date = slot.start_time.split("T")[0];
          if (!slotsByDate[date]) {
            slotsByDate[date] = { available: 0, booked: 0 };
          }
          if (slot.is_booked) {
            slotsByDate[date].booked += 1;
          } else {
            slotsByDate[date].available += 1;
          }
        });

        // 🎨 Gradient colors for available and booked slots
        const gradientAvailable = "linear-gradient(135deg, #3b82f6, #8b5cf6)"; // Blue to Purple
        const gradientBooked =
          "linear-gradient(135deg,rgb(151, 249, 22), #dc2626)"; // Orange to Red

        // 🔹 Create events showing slot count per date
        let events = Object.keys(slotsByDate).map((date) => ({
          title: `📅 ${slotsByDate[date].available} Available / ${slotsByDate[date].booked} Booked`,
          start: date, 
          backgroundColor: "#8b5cf6",
          textColor: "white",
        }));

        successCallback(events);
      } catch (error) {
        console.error("Error fetching slots:", error);
        failureCallback(error);
      }
    },
  };

  // 3) dateClick logic
  calendarOptions.dateClick = function (info) {
    if (userRole === "professor") {
      console.log("Professor clicked a date:", info.dateStr);
      // Trigger the NiceGUI backend to open the modal for creating a slot
      fetch("/open_create_slot_modal", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ date: info.dateStr }),
      }).catch((error) =>
        console.error("Error opening create slot modal:", error)
      );
    } else if (userRole === "student") {
      console.log("Student clicked a date:", info.dateStr);
      // Fetch available slots for the selected date
      fetch("/api/auth/get_slots", {
        method: "GET",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      })
        .then((response) => response.json())
        .then((slots) => {
          // Filter slots by clicked date
          const dateStr = info.dateStr; // e.g. "2025-02-23"
          const availableSlots = slots.filter((slot) =>
            slot.start_time.startsWith(dateStr)
          );
          if (availableSlots.length > 0) {
            // Pass the slots to open_create_meeting_model
            fetch("/open_create_meeting_model", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${localStorage.getItem("token")}`,
              },
              cache: "no-cache",
              body: JSON.stringify({ slots: availableSlots }),
            }).catch((error) =>
              console.error("Error opening create meeting modal:", error)
            );
          } else {
            alert("No available slots on this date.");
          }
        })
        .catch((error) => console.error("Error fetching slots:", error));
    } else {
      console.warn("Unhandled user role:", userRole);
    }
  };

<<<<<<< HEAD
  // 4) Create and render the calendar
  const calendar = new FullCalendar.Calendar(calendarEl, calendarOptions);
  calendar.render();
});

// Optional: Custom modal with gradient styling ✨
=======
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
        events: async function (fetchInfo, successCallback, failureCallback) {
            try {
                const response = await fetch('/api/auth/get_slots', {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    },
                });
                const slots = await response.json();
        
                // 🔹 Count slots per day
                const slotsByDate = {};
                slots.forEach(slot => {
                    const date = slot.start_time.split('T')[0];
                    if (!slotsByDate[date]) {
                        slotsByDate[date] = { available: 0, booked: 0 };
                    }
                    if (slot.is_booked) {
                        slotsByDate[date].booked += 1;
                    } else {
                        slotsByDate[date].available += 1;
                    }
                });
        
                // 🔹 Create events showing slot count per date
                let events = Object.keys(slotsByDate).map(date => ({
                    title: `📅 ${slotsByDate[date].available} Available / ${slotsByDate[date].booked} Booked`,
                    start: date,
                    backgroundColor: "#007bff",
                    textColor: "white",
                }));
        
                successCallback(events);
            } catch (error) {
                console.error('Error fetching slots:', error);
                failureCallback(error);
            }
        },
    };

    // 3) dateClick logic
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
                    // Filter slots by clicked date
                    const dateStr = info.dateStr;  // e.g. "2025-02-23"
                    const availableSlots = slots.filter(slot => slot.start_time.startsWith(dateStr));
                    if (availableSlots.length > 0) {
                        // Pass the slots to open_create_meeting_model
                        fetch('/open_create_meeting_model', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                            },
                            body: JSON.stringify({ slots: availableSlots }),
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

    // 4) Create and render the calendar
    const calendar = new FullCalendar.Calendar(calendarEl, calendarOptions);
    calendar.render();
});

// Optional: custom modal utility, not used by NiceGUI
>>>>>>> c50f9b7b695724d550c0e94564b32694d02128e0
function openSlotModal(content) {
  const modal = document.createElement("div");
  modal.id = "slot-modal";
  modal.style.position = "fixed";
  modal.style.top = "50%";
  modal.style.left = "50%";
  modal.style.transform = "translate(-50%, -50%)";
  modal.style.padding = "20px";
  modal.style.background = "linear-gradient(135deg, #9333ea, #2563eb)"; // Purple to Blue
  modal.style.color = "white";
  modal.style.borderRadius = "8px";
  modal.style.boxShadow = "0px 5px 15px rgba(0,0,0,0.3)";
  modal.style.zIndex = 1000;

  modal.innerHTML = `
        <div style="text-align:center; font-weight: bold; font-size: 1.2rem;">${content}</div>
        <button style="margin-top: 15px; background: linear-gradient(135deg, #e11d48, #f43f5e); color: white; padding: 10px 15px; border: none; border-radius: 6px; cursor: pointer;" onclick="document.getElementById('slot-modal').remove()">Close</button>
    `;
  document.body.appendChild(modal);
}
