# 🌟 **Meetly Website** 🌟

## 📖 **Overview**
Meetly is a simple and user-friendly scheduling platform that helps **lecturers** and **students** connect seamlessly. 

- 📅 **Lecturers**: Log in to add available times for meetings.  
- 🙋‍♂️ **Students**: Log in to view available slots and book a meeting.  

---

## ✨ **Features**
- 🔒 **Secure Login & Signup**: Role-based access for lecturers and students.
- 🗓️ **Calendar Integration**: Interactive calendar to manage time slots.
- ⚡ **Effortless Booking**: Students can easily book available slots.
- 🛠️ **Backend Powered by FastAPI**: Robust and secure backend.
- 💾 **SQLite Database**: Lightweight and easy data storage.

---

## 🛠️ **Technologies Used**
- 🌐 **Frontend**: NiceGUI for an intuitive and modern interface.
- 🚀 **Backend**: FastAPI for scalability and performance.
- 🗄️ **Database**: SQLite for local data storage.
- 🔐 **Authentication**: JWT for secure token-based login.

---

## 🚀 **Getting Started**

### 1️⃣ **Clone the Repository**
```bash
git clone <repository_url>
cd meetly
```

### 2️⃣ **Set Up Environment**
- Create a `.env` file and add:
  ```plaintext
  SECRET_KEY=
  ALGORITHM=
  ACCESS_TOKEN_EXPIRE_MINUTES=
  DATABASE_URL=
  ```

### 3️⃣ **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 4️⃣ **Run the Project**
```bash
uvicorn main:app --reload
```



## 🖥️ **How It Works**
### 👨‍🏫 **Lecturer**
1. Log in or sign up.
2. Add your available time slots.
3. View and manage student bookings.

### 👨‍🎓 **Student**
1. Log in or sign up.
2. Browse available slots for your lecturer.
3. Book a time and view your confirmed appointments.

---

## 🗂️ **Project Structure**
```
meetly/
├── app/
│   ├── auth/         # Authentication logic
│   ├── db.py         # Database setup
│   ├── main.py       # Application entry point
├── ui/               # UI components (NiceGUI pages)
├── static/           # Static files (JS, CSS, images)
├── .env              # Environment variables
├── requirements.txt  # Python dependencies
└── README.md         # Project documentation
```

---

## 🌟 **Future Plans**
- ✉️ **Email Notifications**: Reminders for upcoming meetings.
- 🔗 **Calendar Sync**: Integration with Google Calendar.
- 📊 **Advanced Reports**: Insights on bookings and schedules.

---

## ❤️ **Contributions Welcome**
1. Fork this repo.  
2. Create a new branch.  
3. Submit a pull request! 🎉  

---

## 📜 **License**
Licensed under the MIT License. ✨  

Enjoy scheduling smarter with **Meetly**! 🎉
