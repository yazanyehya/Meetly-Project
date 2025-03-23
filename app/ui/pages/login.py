from nicegui import ui, app
from fastapi.staticfiles import StaticFiles
import httpx
import os

# Debug: print current working directory.
print("Current working directory:", os.getcwd())

# (Optional) Mount your local static directory if needed.
app.mount('/static', StaticFiles(directory='app/static'), name='static')

def login_page():
    @ui.page("/")
<<<<<<< HEAD
    def render():
        # Clear tokens on page load.
        ui.run_javascript("""
            localStorage.removeItem('token');
            localStorage.removeItem('role');
            localStorage.removeItem('user_id');
        """)

        # Define icon URLs.
        show_password_icon = "https://media-hosting.imagekit.io//70c384a083664f1d/showPassword.png?Expires=1836604075&Key-Pair-Id=K2ZIVPTIP2VGHC&Signature=1zeEwcD9WSrApnQ1QH69XNvXFnlfP4nLA2n1kh3U-IbcLcixBz0be-ODZI1NtoRMyLVklGyh-jH1sR2t-nu2fogN3Rasb1OcPVswoIt4ATxkExIiNcVPclBLo5RlCqJrv6T29vqAUvW0ab1LsnevUsp5ZPvA1NmHs91XwcvJytrjmLmslo0xOJ72M11I6hE4rUMF1aNdgUpH9Q8BBqL0gXdy4xej5EJFondPqc9gRQeSF86mCyepr4uxPsRqDu7644J95cT4iE9UEA7Gu-mjOcusZ4x18cY1vxRDA05prFB82UmIHxboYdI4uCqhG0DvksoyJ3Ig8SyNXHobTsqv9w__"
        hide_password_icon = "https://media-hosting.imagekit.io//dcffbac9ebdb4f04/hidePassword.png?Expires=1836604007&Key-Pair-Id=K2ZIVPTIP2VGHC&Signature=JvbOb~uixi-rM0l03ozpCisrJDspKgHRUePkzW68VvodFdUBrcEYHyWLnRk54FVNPsj-6NjqUYYF3WOd395G6iZiyOvzEc1oJGjcfJZctcdHyK0Bm8Q3Lrb6KhgnCVONTztffOcimxhl4YSD7b2gOcXUlsh2s7KDlLJKICgXMQVXEB8dRbRb5mwx27ktiMEhArUJ5iG5gkC2uCVYgd16CCxWemc8UhmlXYMUCeUnldr4XGemsPH3Mmh1MiMID2e2ThKUE7kLeY5~AU-WXPBHnwtGbMpyMkBmi6jA84-rangrUipQ0n4LahbxBKwnurrwG5WQfUKm6YbP0UxHtbcdMA__"

        with ui.row().style(
            "position: absolute; top: 0; left: 0; width: 50%; height: 100%;"
            " background: linear-gradient(to bottom, #3b82f6, #8b5cf6);"
            " backdrop-filter: blur(5px);"
            " border-top-right-radius: 150px; border-bottom-right-radius: 150px;"
        ):

            with ui.column().style(
                "position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 90%;"
            ):
                ui.label("Welcome to Meetly")\
                  .style("font-family: 'Poppins', sans-serif; font-size: 3em; font-weight: bold; color: white; text-align: center;")
                ui.label(
                "Where your time finds its perfect rhythm, "
                "Experience the art of smart scheduling as we help you orchestrate every meeting with precision and creativity.\n\n"
                "Transform your daily routine into a masterpiece of productivity, connection, and inspiration."
                ).style(
                    "font-family: 'Poppins', sans-serif; font-size: 1.5em; color: white; text-align: left; margin: 10px; white-space: pre-line;"
                )
                ui.link("SIGN UP", "/signup")\
                  .style(
                      "display: inline-block; margin-top: 30px; padding: 15px 40px;"
                      " background-color: white; color: #linear-gradient(to bottom, #3b82f6, #8b5cf6); font-family: 'Poppins', sans-serif;"
                      " font-weight: bold; font-size: 1.2em; border-radius: 10px; text-decoration: none;"
                      " text-align: center;"
                  )
                ui.image("https://media-hosting.imagekit.io//915b80c86395456b/Virtual-Meeting-Purple-PNG.png?Expires=1836774591&Key-Pair-Id=K2ZIVPTIP2VGHC&Signature=0IetDlJy8NWvKh0v4FN9d5m9fQ81CMeJlG8~LKXsck~BHfRK1u0GO2JnY6zrzfMo3O0TwQCpb0O9xcskLxUAbXBrdZG5AfhVxBq5w6vaXNg2ET7jt99Baf4A8uTGfk1oOy6qw7qvGGt-GxGG5ZBU9WumzkDXgffPdXntmfoSVsAFLwVF9VGMlpTH1-sRn9KURa-t7RuOt5xUHwSA0Or-TmKMoGZE~I3rwABpfvbF~I-EFXy0mxO95V-70vWAO1ZXreW5JbUAI1qbuH9REwnJ-fzOZkYNXwulinVLyznB7WTZfv4aQCIGzHpFo-TcSNhe1jTM0AYjO7aUtmkPyEbdCA__")\
                .classes("mx-auto w-1/2")


        # Right half: Login form on a light background.
        with ui.row().style(
            "position: absolute; top: 0; right: 0; width: 50%; height: 100%;"
        ):
            with ui.column().style(
                "position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 80%;"
            ):
                ui.label("Welcome Back to Meetly")\
                  .style("font-family: 'Poppins', sans-serif; font-size: 2em; font-weight: bold; color: #333; text-align: center; margin-bottom: 10px;")
                ui.label("Connect, schedule, and elevate your daily experience.")\
                  .style("font-family: 'Poppins', sans-serif; font-size: 1.2em; color: #555; text-align: center; margin-bottom: 20px;")
                
                # Email input.
                email = ui.input(label="Email Address").props('type="email"')\
                          .style("margin-bottom: 5px; padding: 12px; width: 100%; font-family: 'Poppins', sans-serif;")
                # Email error message (initially empty).
                email_error_label = ui.label("")\
                                      .style("color: red; font-size: 0.9em; margin-top: 0px; margin-bottom: 10px;")
                
                # Container for password input and toggle icon.
                with ui.element('div').style("position: relative; width: 100%;"):
                    password_input = ui.input(label="Password").props('type="password"')\
                                        .style("padding: 12px; width: 100%; font-family: 'Poppins', sans-serif; padding-right: 40px; margin-bottom: 5px;")
                    
                    # Track password visibility.
                    password_visible = False

                    def toggle_password():
                        nonlocal password_visible
                        password_visible = not password_visible
                        new_type = 'text' if password_visible else 'password'
                        password_input.props['type'] = new_type
                        password_input.update()
                        # Update the toggle icon.
                        new_icon = hide_password_icon if password_visible else show_password_icon
                        visibility_image.props['src'] = new_icon
                        visibility_image.update()

                    # Display the toggle icon.
                    visibility_image = ui.image(show_password_icon)\
                                        .style("position: absolute; right: 10px; top: 50%; transform: translateY(-50%); width: 24px; height: 24px;")\
                                        .on('click', toggle_password)
                # Password error message.
                password_error_label = ui.label("")\
                                         .style("color: red; font-size: 0.9em; margin-top: 0px; margin-bottom: 10px;")
                
                # Create the login button (initially disabled) with gradient background.
                login_button = ui.button("Login", on_click=lambda: handle_login())\
                        .props("rounded")\
                        .style(
                            "margin-bottom: 10px; padding: 12px; "
                            "background-image: linear-gradient(to bottom, #3b82f6, #8b5cf6) !important; "
                            "color: white; font-family: 'Poppins', sans-serif; font-size: 1.2em; width: 100%;"
                        )

                login_button.disabled = True  # start disabled

                # Update the button state and clear error messages on input.
                def update_login_button_state():
                    is_email_valid = bool(email.value.strip())
                    is_password_valid = bool(password_input.value.strip())
                    login_button.disabled = not (is_email_valid and is_password_valid)
                    if is_email_valid:
                        email_error_label.set_text("")
                    if is_password_valid:
                        password_error_label.set_text("")
                    login_button.update()
                
                # Attach event listeners to update the button state.
                email.on("input", lambda e: update_login_button_state())
                password_input.on("input", lambda e: update_login_button_state())
                
                # Handle login with pre‑validation.
                async def handle_login():
                    has_error = False
                    if not email.value.strip():
                        email_error_label.set_text("Email is required")
                        has_error = True
                    if not password_input.value.strip():
                        password_error_label.set_text("Password is required")
                        has_error = True
                    if has_error:
                        return  # Do not proceed if fields are empty.

                    # Clear error messages if any.
                    email_error_label.set_text("")
                    password_error_label.set_text("")
                    
                    # Proceed with backend login.
                    user_data = {"email": email.value, "password": password_input.value}
                    try:
                        backend_url = "http://127.0.0.1:8000/api/auth/login"
                        async with httpx.AsyncClient() as client:
                            response = await client.post(backend_url, json=user_data)
                        if response.status_code == 200:
                            data = response.json()
                            token = data.get("access_token")
                            role = data.get("role")
                            user_id = data.get("user_id")
                            ui.notify("✅ Login successful!", type="positive")
                            js_code = f"""
                                localStorage.setItem('token', '{token}');
                                localStorage.setItem('role', '{role}');
                                localStorage.setItem('user_id', '{user_id}');
                                window.location.replace('/calendar');
                            """
                            ui.run_javascript(js_code)
                        else:
                            # Optionally, you can handle backend errors here.
                            ui.notify("Login failed! Please check your credentials.", type="negative")
                    except Exception as e:
                        ui.notify(f"⚠ Error: {str(e)}", type="negative")

login_page()
=======
    def render():   
        with ui.row().style("position: absolute; top: 0; left: 0; width: 100%; height: 100%;"):
            ui.image('https://wallpapercave.com/wp/fMos4cr.jpg')\
              .style("width: 100%; height: 100%; object-fit: cover;")
        
        with ui.column()\
                .style("position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);"
                       " padding: 20px; width: 400px; background: rgba(255, 255, 255, 0.8);"
                       " border-radius: 8px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);"):

            ui.label("Welcome to Meetly")\
              .style("font-size: 1.5em; font-weight: bold; margin-bottom: 20px; text-align:center;")

            email = ui.input(label="Email").props('type="email"')\
                      .style("margin-bottom: 10px;")
            password = ui.input(label="Password").props('type="password"')\
                         .style("margin-bottom: 10px;")
            
            async def handle_login():
                user_data = {
                    "email": email.value,
                    "password": password.value
                }
                try:
                    backend_url = "http://127.0.0.1:8000/api/auth/login"
                    async with httpx.AsyncClient() as client:
                        response = await client.post(backend_url, json=user_data)

                    if response.status_code == 200:
                        data = response.json()

                        token = data.get("access_token")
                        role = data.get("role")
                        user_id = data.get("user_id")

                        ui.notify("✅ Login successful!", type="positive")

                        # Store token and role in localStorage
                        js_set_storage_and_redirect = f"""
                            localStorage.setItem('token', '{token}');
                            localStorage.setItem('role', '{role}');
                            localStorage.setItem('user_id', '{data['user_id']}');
                            // Force a full page reload to /calendar:
                            window.location.href = '/calendar';
                        """

                        ui.run_javascript(js_set_storage_and_redirect)

                    else:
                        error_message = response.json().get("detail", "Login failed!")
                        ui.notify(f"❌ {error_message}", type="negative")
                except Exception as e:
                    ui.notify(f"⚠ Error: {str(e)}", type="negative")

            ui.button("Login", on_click=handle_login)\
              .props("rounded")\
              .style("margin-bottom: 10px;")
            
            with ui.row():
                ui.label("Don't have an account?").style("margin-right: 5px;")
                ui.link("Sign Up", "/signup").style("color: blue; text-decoration: underline;")
>>>>>>> c50f9b7b695724d550c0e94564b32694d02128e0
