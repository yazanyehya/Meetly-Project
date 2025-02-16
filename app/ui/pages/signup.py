from nicegui import ui
import httpx  # HTTP client to call the backend API

def signup_page():
    @ui.page("/signup")
    def render():
        with ui.row().style("position: absolute; top: 0; left: 0; width: 100%; height: 100%;"):
            ui.image('https://wallpapercave.com/wp/fMos4cr.jpg').style("width: 100%; height: 100%; object-fit: cover;")
        
        with ui.column().style("position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); padding: 20px; background: rgba(255,255,255,0.8); border-radius:8px; box-shadow: 0px 4px 10px rgba(0,0,0,0.2);"):
            ui.label("Create Your Account").style("font-size: 1.5em; font-weight:bold; margin-bottom:20px;")
            
            # Input fields
            name = ui.input(label="Name").props('type="text"').style("margin-bottom:10px;")
            email = ui.input(label="Email").props('type="email"').style("margin-bottom: 10px;")
            password = ui.input(label="Password").props('type="password"').style("margin-bottom:10px;")
            
            # Sign-Up Button
            async def handle_signup():
                # Data to send to the backend
                user_data = {
                    "name": name.value,
                    "email": email.value,
                    "password": password.value
                }
                try:
                    # Make an HTTP POST request to the backend
                    async with httpx.AsyncClient() as client:
                        response = await client.post("http://127.0.0.1:8000/api/auth/signup", json=user_data)
                    
                    if response.status_code == 200:
                        ui.notify("Signed up successfully!", type="positive")
                    else:
                        error_message = response.json().get("detail", "Sign-up failed!")
                        ui.notify(error_message, type="negative")
                except Exception as e:
                    ui.notify(f"Error: {str(e)}", type="negative")
            
            ui.button("Sign Up", on_click=handle_signup).props("rounded").style("margin-bottom: 10px;")
            
            # Log In Link
            with ui.row():
                ui.label("Have an account?").style("margin-right:5px;")
                ui.link("Log in", "/").style("color:blue; text-decoration:underline;")
