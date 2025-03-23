from nicegui import ui, app
from fastapi.staticfiles import StaticFiles
import httpx
import os

# Debug: print current working directory.
print("Current working directory:", os.getcwd())

# (Optional) Mount your local static directory if needed.
app.mount('/static', StaticFiles(directory='app/static'), name='static')

# Define icons for the password visibility toggle.
show_password_icon = "https://media-hosting.imagekit.io//70c384a083664f1d/showPassword.png?Expires=1836604075&Key-Pair-Id=K2ZIVPTIP2VGHC&Signature=1zeEwcD9WSrApnQ1QH69XNvXFnlfP4nLA2n1kh3U-IbcLcixBz0be-ODZI1NtoRMyLVklGyh-jH1sR2t-nu2fogN3Rasb1OcPVswoIt4ATxkExIiNcVPclBLo5RlCqJrv6T29vqAUvW0ab1LsnevUsp5ZPvA1NmHs91XwcvJytrjmLmslo0xOJ72M11I6hE4rUMF1aNdgUpH9Q8BBqL0gXdy4xej5EJFondPqc9gRQeSF86mCyepr4uxPsRqDu7644J95cT4iE9UEA7Gu-mjOcusZ4x18cY1vxRDA05prFB82UmIHxboYdI4uCqhG0DvksoyJ3Ig8SyNXHobTsqv9w__"
hide_password_icon = "https://media-hosting.imagekit.io//dcffbac9ebdb4f04/hidePassword.png?Expires=1836604007&Key-Pair-Id=K2ZIVPTIP2VGHC&Signature=JvbOb~uixi-rM0l03ozpCisrJDspKgHRUePkzW68VvodFdUBrcEYHyWLnRk54FVNPsj-6NjqUYYF3WOd395G6iZiyOvzEc1oJGjcfJZctcdHyK0Bm8Q3Lrb6KhgnCVONTztffOcimxhl4YSD7b2gOcXUlsh2s7KDlLJKICgXMQVXEB8dRbRb5mwx27ktiMEhArUJ5iG5gkC2uCVYgd16CCxWemc8UhmlXYMUCeUnldr4XGemsPH3Mmh1MiMID2e2ThKUE7kLeY5~AU-WXPBHnwtGbMpyMkBmi6jA84-rangrUipQ0n4LahbxBKwnurrwG5WQfUKm6YbP0UxHtbcdMA__"

def signup_page():
    @ui.page("/signup")
    def render():
        # Left half: Sign-up form on a light background.
        with ui.row().style(
            "position: absolute; top: 0; left: 0; width: 50%; height: 100%; "
        ):
            with ui.column().style(
                "position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 80%;"
            ):
                ui.label("Create Your Account")\
                  .style("font-family: 'Poppins', sans-serif; font-size: 2em; font-weight: bold; color: #333; text-align: center; margin-bottom: 10px;")
                ui.label("Join us to streamline your scheduling experience.")\
                  .style("font-family: 'Poppins', sans-serif; font-size: 1.2em; color: #555; text-align: center; margin-bottom: 20px;")
                
                # Name input and error label.
                name = ui.input(label="Name").props('type="text"')\
                         .style("margin-bottom: 0px; padding: 12px; width: 100%; font-family: 'Poppins', sans-serif;")
                name_error = ui.label("")\
                              .style("color: red; font-size: 0.8em; margin-bottom: 10px;")
                
                # Email input and error label.
                email = ui.input(label="Email").props('type="email"')\
                         .style("margin-bottom: 0px; padding: 12px; width: 100%; font-family: 'Poppins', sans-serif;")
                email_error = ui.label("")\
                              .style("color: red; font-size: 0.8em; margin-bottom: 10px;")
                
                # Password input with toggle icon and error label.
                with ui.element('div').style("position: relative; width: 100%;"):
                    password_input = ui.input(label="Password").props('type="password"')\
                                         .style("padding: 12px; width: 100%; font-family: 'Poppins', sans-serif; padding-right: 40px; margin-bottom: 5px;")
                    password_visible = False
                    def toggle_password():
                        nonlocal password_visible
                        password_visible = not password_visible
                        new_type = 'text' if password_visible else 'password'
                        password_input.props['type'] = new_type
                        password_input.update()
                        new_icon = hide_password_icon if password_visible else show_password_icon
                        visibility_image.props['src'] = new_icon
                        visibility_image.update()
                    visibility_image = ui.image(show_password_icon)\
                                          .style("position: absolute; right: 10px; top: 50%; transform: translateY(-50%); width: 24px; height: 24px;")\
                                          .on('click', toggle_password)
                password_error = ui.label("")\
                                  .style("color: red; font-size: 0.8em; margin-bottom: 10px;")
                
                # Sign-Up Button (initially disabled).
                signup_button = ui.button("Sign Up", on_click=lambda: handle_signup())\
                                  .props("rounded")\
                                .style(
                                    "margin-bottom: 10px; padding: 12px; "
                                    "background-image: linear-gradient(to bottom, #3b82f6, #8b5cf6) !important; "
                                    "color: white; font-family: 'Poppins', sans-serif; font-size: 1.2em; width: 100%;"
                                )
                signup_button.disabled = True
                
                # Update the button state and clear error messages on input.
                def update_signup_button_state():
                    is_name_valid = bool(name.value.strip())
                    is_email_valid = bool(email.value.strip())
                    is_password_valid = bool(password_input.value.strip())
                    signup_button.disabled = not (is_name_valid and is_email_valid and is_password_valid)
                    if is_name_valid:
                        name_error.set_text("")
                    if is_email_valid:
                        email_error.set_text("")
                    if is_password_valid:
                        password_error.set_text("")
                    signup_button.update()
                
                name.on("input", lambda e: update_signup_button_state())
                email.on("input", lambda e: update_signup_button_state())
                password_input.on("input", lambda e: update_signup_button_state())
                
                # Sign-Up Button Handler.
                async def handle_signup():
                    has_error = False
                    if not name.value.strip():
                        name_error.set_text("Name is required")
                        has_error = True
                    if not email.value.strip():
                        email_error.set_text("Email is required")
                        has_error = True
                    if not password_input.value.strip():
                        password_error.set_text("Password is required")
                        has_error = True
                    if has_error:
                        return
                    # Clear error messages.
                    name_error.set_text("")
                    email_error.set_text("")
                    password_error.set_text("")
                    
                    user_data = {
                        "name": name.value,
                        "email": email.value,
                        "password": password_input.value
                    }
                    try:
                        async with httpx.AsyncClient() as client:
                            response = await client.post("http://127.0.0.1:8000/api/auth/signup", json=user_data)
                        if response.status_code == 200:
                            ui.notify("Signed up successfully!", type="positive")
                        else:
                            ui.notify("Sign-up failed!", type="negative")
                    except Exception as e:
                        ui.notify(f"Error: {str(e)}", type="negative")
                
        # Right half: Background with a blur gradient.
        with ui.row().style(
            "position: absolute; top: 0; right: 0; width: 50%; height: 100%;"
            " background: linear-gradient(to bottom, #3b82f6, #8b5cf6);"
            " backdrop-filter: blur(5px);"
            " border-top-left-radius: 150px; border-bottom-left-radius: 150px;"
        ):
            with ui.column().style(
                "position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 80%;"
            ):
                ui.label("Welcome Back to Meetly")\
                  .style("font-family: 'Poppins', sans-serif; font-size: 3em; font-weight: bold; color: white; text-align: center;")
                ui.label(
                    "Connect, schedule, and elevate your daily experience,"
                    "Rediscover the joy of planning your day with ease and creativity.\n\n"
                    "Step into a world where every meeting unlocks new opportunities and meaningful connections."
                )\
                .style(
                    "font-family: 'Poppins', sans-serif; font-size: 1.5em; color: white; text-align: left; margin: 10px; white-space: pre-line;"
                )

                ui.link("SIGN IN", "/")\
                  .style(
                      "display: inline-block; margin-top: 30px; padding: 15px 40px;"
                      " background-color: white; color: #linear-gradient(to bottom, #3b82f6, #8b5cf6); font-family: 'Poppins', sans-serif;"
                      " font-weight: bold; font-size: 1.2em; border-radius: 10px; text-decoration: none;"
                      " text-align: center;"
                  )


signup_page()

