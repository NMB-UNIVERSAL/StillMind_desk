import sys
import traceback
import logging

def handle_exception(exc_type, exc_value, exc_traceback):
    # Write error to file
    with open('error_log.txt', 'w') as f:
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    # Also print to console
    print("An error occurred! Check error_log.txt for details")
    input("Press Enter to exit...")  # Keep console window open

sys.excepthook = handle_exception

try:
    # Your existing imports and code here
    import customtkinter as ctk
    from PIL import Image, ImageDraw
    import random
    import json
    from datetime import datetime
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import tkinter.messagebox as messagebox
    import math
    import tkinter as tk
    from pygame import mixer
    import os
    from plyer import notification
    import threading
    import time
    from datetime import datetime, timedelta
    import platform
    import subprocess
    from supabase import create_client, Client
    from dotenv import load_dotenv

except Exception as e:
    with open('startup_error.txt', 'w') as f:
        traceback.print_exc(file=f)
    print("Error during startup! Check startup_error.txt")
    input("Press Enter to exit...")

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# Set up logging
def setup_logging():
    log_path = "stillmind_log.txt"
    if getattr(sys, 'frozen', False):
        # If running as executable
        log_path = os.path.join(os.path.dirname(sys.executable), "stillmind_log.txt")
    
    logging.basicConfig(
        filename=log_path,
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

setup_logging()

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller/Nuitka"""
    try:
        # PyInstaller/Nuitka creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def get_app_data_path(filename):
    """Get path for app data files that need to be written to"""
    if getattr(sys, 'frozen', False):
        # Running as compiled
        app_dir = os.path.dirname(sys.executable)
    else:
        # Running in development
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(app_dir, filename)

def load_image(path, size=None):
    """Safely load an image with error handling"""
    try:
        img_path = get_resource_path(path)
        img = Image.open(img_path)
        if size:
            img = img.resize(size)
        return img
    except Exception as e:
        print(f"Error loading image {path}: {e}")
        return None

class ParticleBurst:
    def __init__(self, canvas, x, y, colors=None):
        if colors is None:
            self.colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEEAD"]  # Default colors
        else:
            self.colors = colors
        
        self.canvas = canvas
        self.particles = []
        self.create_particles(x, y)
        self.animate()

    def create_particles(self, x, y):
        for _ in range(15):  # Increased number of particles
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 6)  # Increased speed range
            size = random.randint(3, 8)  # Increased size range
            color = random.choice(self.colors)
            
            particle = {
                'id': self.canvas.create_oval(x-size, y-size, x+size, y+size, 
                                            fill=color, outline=""),
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'size': size,
                'alpha': 1.0
            }
            self.particles.append(particle)

    def animate(self):
        if not self.particles:
            return
        
        for particle in self.particles[:]:
            # Update position
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            
            # Update alpha (fade out more slowly)
            particle['alpha'] -= 0.02  # Reduced from 0.05 to 0.02
            
            if particle['alpha'] <= 0:
                self.canvas.delete(particle['id'])
                self.particles.remove(particle)
            else:
                # Move particle
                self.canvas.moveto(particle['id'], 
                                 particle['x'] - particle['size'],
                                 particle['y'] - particle['size'])
                
                # Update opacity
                current_color = self.canvas.itemcget(particle['id'], 'fill')
                rgb = self.hex_to_rgb(current_color)
                new_color = self.rgb_to_hex(*rgb, particle['alpha'])
                self.canvas.itemconfig(particle['id'], fill=new_color)
        
        if self.particles:
            self.canvas.after(16, self.animate)  # ~60 FPS

    @staticmethod
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    @staticmethod
    def rgb_to_hex(r, g, b, alpha=1.0):
        return f'#{int(r*alpha):02x}{int(g*alpha):02x}{int(b*alpha):02x}'

class BackgroundCanvas(ctk.CTkCanvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, highlightthickness=0, borderwidth=0, **kwargs)
        self.bind('<Button-1>', self.create_burst)
        self.parent = parent
        
        # Load background images
        self.bg_dark = ctk.CTkImage(
            light_image=Image.open(get_resource_path("images/dark_background.jpg")),
            dark_image=Image.open(get_resource_path("images/dark_background.jpg")),
            size=(800, 600)  # Adjust size to match your window
        )
        self.bg_light = ctk.CTkImage(
            light_image=Image.open(get_resource_path("images/light_background.jpg")),
            dark_image=Image.open(get_resource_path("images/light_background.jpg")),
            size=(800, 600)  # Adjust size to match your window
        )
        
        # Create background image label
        self.bg_label = ctk.CTkLabel(self, text="", image=self.bg_dark)
        self.bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Initial background color setup
        self.update_background_color()
        
        # Bind to theme changes
        self.bind('<Configure>', lambda e: self.update_background_color())

    def update_background_color(self):
        # Update background image based on theme
        if ctk.get_appearance_mode() == "Dark":
            self.bg_label.configure(image=self.bg_dark)
        else:
            self.bg_label.configure(image=self.bg_light)

    def create_burst(self, event):
        ParticleBurst(self, event.x, event.y)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialize data_handler as None at start
        self.data_handler = None
        
        # Set default theme
        ctk.set_appearance_mode("dark")
        
        self.title("StillMind")
        self.geometry("800x600")
        self.resizable(False, False)
        
        # Initialize notification manager and connect data_handler later after login
        self.notification_manager = NotificationManager()
        self.notification_manager.start_notification_thread()
        
        # Create container
        self.container = ctk.CTkFrame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        # Check for saved session BEFORE creating frames
        self.check_saved_session()
        
        # Initialize frames dictionary
        self.frames = {}
        
        # Add all pages to the frames dictionary
        for F in (LoginPage, StartingPage, MainPage, StatsPage, SettingsPage, AchievementsPage, HelpPage, AccountPage):
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        # Show the starting frame based on login state
        if self.data_handler:
            print("Auto-login successful, showing StartingPage")
            self.show_frame(StartingPage)
            # Apply theme if user is already logged in
            self.apply_theme_from_settings()
        else:
            print("No active session, showing LoginPage")
            self.show_frame(LoginPage)

    def check_saved_session(self):
        """Check for saved login session and auto-login if valid"""
        try:
            # Check if session file exists
            session_file = os.path.join(os.path.expanduser("~"), ".stillmind_session")
            if os.path.exists(session_file):
                with open(session_file, "r") as f:
                    session_data = json.load(f)
                
                # Check if session is not expired
                expires_at = datetime.fromisoformat(session_data.get("expires_at", "2000-01-01"))
                if expires_at > datetime.now():
                    # Try to restore session
                    user_id = session_data.get("user_id")
                    access_token = session_data.get("access_token")
                    refresh_token = session_data.get("refresh_token")
                    
                    if user_id and access_token and refresh_token:
                        # Set Supabase access token
                        try:
                            # Set the session with both tokens
                            supabase.auth.set_session(access_token, refresh_token)
                            
                            # Initialize data handler
                            self.data_handler = DataHandling(user_id)
                            print(f"Auto-login successful for user: {user_id}")
                            return
                        except Exception as e:
                            print(f"Error restoring session: {e}")
        except Exception as e:
            print(f"Error during auto-login: {e}")
        
        # If we get here, no valid session was found
        self.data_handler = None
        
    def save_session(self, user_id, access_token, refresh_token, expires_at):
        """Save login session for auto-login"""
        try:
            session_data = {
                "user_id": user_id,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at.isoformat()
            }
            
            session_file = os.path.join(os.path.expanduser("~"), ".stillmind_session")
            with open(session_file, "w") as f:
                json.dump(session_data, f)
            
            print(f"Session saved for user: {user_id}")
        except Exception as e:
            print(f"Error saving session: {e}")

    def logout(self):
        """Log out the current user"""
        try:
            # Clear Supabase session
            supabase.auth.sign_out()
            
            # Clear data handler
            self.data_handler = None
            
            # Remove session file
            session_file = os.path.join(os.path.expanduser("~"), ".stillmind_session")
            if os.path.exists(session_file):
                os.remove(session_file)
            
            # Stop sounds
            if MainPage in self.frames:
                self.frames[MainPage].stop_all_sounds()
            
            # Show login page
            self.show_frame(LoginPage)
            
            print("Logout successful")
        except Exception as e:
            print(f"Error during logout: {e}")

    def apply_theme_from_settings(self):
        """Load and apply theme and sound settings from database settings"""
        if self.data_handler:
            settings = self.data_handler.get_settings()
            
            # Apply theme
            theme = settings.get('theme', 'dark')
            ctk.set_appearance_mode(theme)
            
            # Apply sound settings
            should_play_sound = settings.get('sound', True)
            if MainPage in self.frames:
                self.frames[MainPage].toggle_background_music(should_play_sound)
            
            # Update button colors
            button_color = get_button_color()
            for frame in self.frames.values():
                for widget in frame.winfo_children():
                    if isinstance(widget, ctk.CTkButton):
                        widget.configure(fg_color=button_color)
                        
            # Update all background canvases
            for frame in self.frames.values():
                if hasattr(frame, 'bg_canvas'):
                    frame.bg_canvas.update_background_color()

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()
        
        # Update frame-specific content
        if cont == AccountPage:
            # Refresh account page content when shown
            if hasattr(frame, 'load_user_info'):
                frame.load_user_info()
                
        if hasattr(frame, 'bg_canvas'):
            frame.bg_canvas.update_background_color()
        
        # Other existing show_frame code...
        if cont == MainPage:
            # Reload settings from database before showing the page
            if self.data_handler:
                self.frames[MainPage].settings = self.data_handler.get_settings()
                # Apply sound settings
                should_play_sound = self.frames[MainPage].settings.get('sound', True)
                self.frames[MainPage].toggle_background_music(should_play_sound)
            self.frames[MainPage].create_progress_indicators()
            self.frames[MainPage].start_countdown()
        elif cont == StatsPage:
            self.frames[MainPage].stop_exercise()
            self.frames[StatsPage].update_graph()
        elif cont == SettingsPage:
            # Refresh settings when entering settings page
            if self.data_handler:
                self.frames[SettingsPage].refresh_settings_from_database()
        elif cont == AchievementsPage:
            # Refresh achievements when showing achievements page
            self.frames[AchievementsPage].update_achievements()
            
        # Update notification manager if data_handler exists
        if self.data_handler:
            self.notification_manager.set_data_handler(self.data_handler)

    def on_closing(self):
        """Handle cleanup when window is closed"""
        try:
            # Stop all sounds
            mixer.music.stop()
            mixer.quit()
            
            # Stop notification thread
            if hasattr(self, 'notification_manager'):
                self.notification_manager.stop_notification_thread()
            
            # Destroy the window
            self.quit()
            self.destroy()
            
            # Force exit the application
            sys.exit()
            
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
            sys.exit()

def get_button_color():
    """Returns the appropriate button color based on the current theme"""
    if ctk.get_appearance_mode() == "Dark":
        return "#766E7A"
    return "#859FBB"

class LoginPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Set up background canvas (optional, for consistency)
        self.bg_canvas = BackgroundCanvas(self)
        self.bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Title for the account page
        self.title_label = ctk.CTkLabel(
            self, text="Account System", font=("Arial", 30, "bold")
        )
        self.title_label.place(relx=0.5, rely=0.1, anchor="center")

        # Email entry
        self.email_entry = ctk.CTkEntry(
            self, placeholder_text="Email", width=300, font=("Arial", 16)
        )
        self.email_entry.place(relx=0.5, rely=0.3, anchor="center")

        # Password entry (with masking)
        self.password_entry = ctk.CTkEntry(
            self, placeholder_text="Password", show="*", width=300, font=("Arial", 16)
        )
        self.password_entry.place(relx=0.5, rely=0.4, anchor="center")

        # Sign Up button
        self.signup_button = ctk.CTkButton(
            self,
            text="Sign Up",
            width=140,
            command=self.sign_up
        )
        self.signup_button.place(relx=0.35, rely=0.5, anchor="center")

        # Sign In button
        self.signin_button = ctk.CTkButton(
            self,
            text="Sign In",
            width=140,
            command=self.sign_in
        )
        self.signin_button.place(relx=0.65, rely=0.5, anchor="center")

        # Message label for feedback
        self.message_label = ctk.CTkLabel(
            self, text="", font=("Arial", 14)
        )
        self.message_label.place(relx=0.5, rely=0.6, anchor="center")

        # Back button to return to StartingPage
        self.back_button = ctk.CTkButton(
            self,
            text="Back",
            image=ctk.CTkImage(Image.open(get_resource_path("icons/back.png")), size=(20, 20)),
            command=lambda: controller.show_frame(StartingPage)
        )
        self.back_button.place(relx=0.5, rely=0.9, anchor="center")
        self.back_button.lift()

    def sign_up(self):
        # Get user input from entries
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        if not email or not password:
            self.message_label.configure(text="Please enter both email and password.")
            return

        try:
            # Call Supabase auth API for sign up
            response = supabase.auth.sign_up({"email": email, "password": password})
            resp = response.dict()  # Convert the Pydantic model to a dictionary
            if resp.get("error"):
                err = resp["error"]["message"]
                self.message_label.configure(text=f"Sign up failed: {err}")
            else:
                self.message_label.configure(text="Sign up successful, now just click sign in")
        except Exception as e:
            self.message_label.configure(text=f"Error: {str(e)}")

    def sign_in(self):
        # Get user input from entries
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        if not email or not password:
            self.message_label.configure(text="Please enter both email and password.")
            return

        try:
            # Call Supabase auth API for sign in
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            resp = response.dict()  # Convert to a dictionary for easier access
            if resp.get("error"):
                err = resp["error"]["message"]
                self.message_label.configure(text=f"Login failed: {err}")
            else:
                self.message_label.configure(text="Login successful!")
                current_user_id = resp.get("user", {}).get("id")
                if current_user_id:
                    self.controller.data_handler = DataHandling(current_user_id)
                    
                    # Save session for auto-login
                    access_token = resp.get("session", {}).get("access_token")
                    refresh_token = resp.get("session", {}).get("refresh_token")
                    expires_at_value = resp.get("session", {}).get("expires_at")
                    
                    if access_token and refresh_token and expires_at_value is not None:
                        # Handle expires_at which could be an integer (timestamp) or string
                        if isinstance(expires_at_value, int):
                            # Unix timestamp (seconds since epoch)
                            expires_at = datetime.fromtimestamp(expires_at_value)
                        else:
                            # ISO format string
                            try:
                                # Handle different string formats
                                if isinstance(expires_at_value, str) and 'Z' in expires_at_value:
                                    expires_at_value = expires_at_value.replace('Z', '+00:00')
                                expires_at = datetime.fromisoformat(str(expires_at_value))
                            except ValueError:
                                # Fallback - set expiry to 7 days from now
                                expires_at = datetime.now() + timedelta(days=7)
                
                        self.controller.save_session(current_user_id, access_token, refresh_token, expires_at)
                    
                    # Apply theme after login
                    self.controller.apply_theme_from_settings()
                    self.controller.show_frame(StartingPage)
                else:
                    self.message_label.configure(text="User ID not found in response")
        except Exception as e:
            self.message_label.configure(text=f"Error: {str(e)}")


class DataHandling:
    def __init__(self, user_id: str):
        self.user_id = user_id

    def get_settings(self) -> dict:
        response = supabase.table('app_settings').select('*').eq('user_id', self.user_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]['settings']
        else:
            default_settings = {
                'theme': 'dark',
                'sound': True,
                'breathing_times': {
                    'inhale': 4,
                    'hold': 7,
                    'exhale': 8
                },
                'progress_style': 'bars'
            }
            supabase.table('app_settings').insert({'user_id': self.user_id, 'settings': default_settings}).execute()
            return default_settings

    def save_settings(self, settings: dict):
        response = supabase.table('app_settings').select('*').eq('user_id', self.user_id).execute()
        if response.data and len(response.data) > 0:
            supabase.table('app_settings').update({'settings': settings}).eq('user_id', self.user_id).execute()
        else:
            supabase.table('app_settings').insert({'user_id': self.user_id, 'settings': settings}).execute()

    def get_stats(self) -> dict:
        response = supabase.table('breathing_stats').select('*').eq('user_id', self.user_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]['stats']
        else:
            default_stats = {}
            supabase.table('breathing_stats').insert({'user_id': self.user_id, 'stats': default_stats}).execute()
            return default_stats

    def save_stats(self, stats: dict):
        response = supabase.table('breathing_stats').select('*').eq('user_id', self.user_id).execute()
        if response.data and len(response.data) > 0:
            supabase.table('breathing_stats').update({'stats': stats}).eq('user_id', self.user_id).execute()
        else:
            supabase.table('breathing_stats').insert({'user_id': self.user_id, 'stats': stats}).execute()

    def get_notification_settings(self) -> dict:
        response = supabase.table('notification_settings').select('*').eq('user_id', self.user_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]['settings']
        else:
            default_notif = {'enabled': True, 'time': '09:00'}
            supabase.table('notification_settings').insert({'user_id': self.user_id, 'settings': default_notif}).execute()
            return default_notif

    def save_notification_settings(self, notification_settings: dict):
        response = supabase.table('notification_settings').select('*').eq('user_id', self.user_id).execute()
        if response.data and len(response.data) > 0:
            supabase.table('notification_settings').update({'settings': notification_settings}).eq('user_id', self.user_id).execute()
        else:
            supabase.table('notification_settings').insert({'user_id': self.user_id, 'settings': notification_settings}).execute()
            
    def get_achievements(self) -> dict:
        response = supabase.table('achievements').select('*').eq('user_id', self.user_id).execute()
        print(f"Achievement response: {response.data}")  # Debugging
        
        if response.data and len(response.data) > 0:
            achievements = response.data[0]['achievements']
            print(f"Loaded achievements: {achievements}")  # Debugging
            return achievements
        else:
            default_achievements = {}
            supabase.table('achievements').insert({'user_id': self.user_id, 'achievements': default_achievements}).execute()
            return default_achievements
            
    def save_achievements(self, achievements: dict):
        response = supabase.table('achievements').select('*').eq('user_id', self.user_id).execute()
        if response.data and len(response.data) > 0:
            supabase.table('achievements').update({'achievements': achievements}).eq('user_id', self.user_id).execute()
        else:
            supabase.table('achievements').insert({'user_id': self.user_id, 'achievements': achievements}).execute()


class StartingPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Add background canvas
        self.bg_canvas = BackgroundCanvas(self)
        self.bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Help button in top right
        self.help_button = ctk.CTkButton(
            self,
            text="",
            width=40,
            height=40,
            corner_radius=20,
            image=ctk.CTkImage(Image.open(get_resource_path("icons/help.png")), size=(20, 20)),
            command=lambda: controller.show_frame(HelpPage)
        )
        self.help_button.place(relx=0.95, rely=0.05, anchor="center")
        self.help_button.lift()

        self.title_label = ctk.CTkLabel(
            self,
            text="StillMind",
            font=("Arial", 30, "bold")
        )
        self.title_label.place(relx=0.5, rely=0.2, anchor="center")
        self.title_label.lift()  # Ensure it's above the canvas
        
        button_y = 400
        button_width = 140
        spacing = 20
        start_x = (800 - (4 * button_width + 3 * spacing)) // 2
        
        # Update button colors
        button_color = get_button_color()
        
        self.stats_button = ctk.CTkButton(
            self,
            text="Stats",
            width=button_width,
            fg_color=button_color,
            image=ctk.CTkImage(Image.open(get_resource_path("icons/stats.png")), size=(20, 20)),
            command=lambda: controller.show_frame(StatsPage)
        )
        self.stats_button.place(x=start_x, y=button_y)
        self.stats_button.lift()
        
        self.start_Button = ctk.CTkButton(
            self,
            text="Start",
            width=button_width,
            fg_color=button_color,
            image=ctk.CTkImage(Image.open(get_resource_path("icons/play.png")), size=(20, 20)),
            command=lambda: controller.show_frame(MainPage)
        )
        self.start_Button.place(x=start_x + button_width + spacing, y=button_y)
        self.start_Button.lift()
        
        self.achievements_button = ctk.CTkButton(
            self,
            text="Achievements",
            width=button_width,
            fg_color=button_color,
            image=ctk.CTkImage(Image.open(get_resource_path("icons/trophy.png")), size=(20, 20)),
            command=lambda: controller.show_frame(AchievementsPage)
        )
        self.achievements_button.place(x=start_x + 2 * (button_width + spacing), y=button_y)
        self.achievements_button.lift()
        
        self.settings_Button = ctk.CTkButton(
            self,
            text="Settings",
            width=button_width,
            fg_color=button_color,
            image=ctk.CTkImage(Image.open(get_resource_path("icons/settings.png")), size=(20, 20)),
            command=lambda: controller.show_frame(SettingsPage)
        )
        self.settings_Button.place(x=start_x + 3 * (button_width + spacing), y=button_y)
        self.settings_Button.lift()

        # Account button
        self.account_button = ctk.CTkButton(
            self,
            text="Account",
            image=ctk.CTkImage(Image.open(get_resource_path("icons/account.png")), size=(20, 20)),
            command=lambda: controller.show_frame(AccountPage)
        )
        self.account_button.place(relx=0.8, rely=0.05, anchor="center")

class MainPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.timer = 0
        self.scheduled_tasks = []
        self.is_exercise_active = False
        
        # Add background canvas
        self.bg_canvas = BackgroundCanvas(self)
        self.bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Load settings
        self.settings = self.get_settings()
        
        # Initialize audio
        mixer.init()
        
        # Load audio files with better error handling
        self.inhale_sound = None
        self.hold_sound = None
        self.exhale_sound = None
        self.background_music = None
        
        try:
            if os.path.exists(get_resource_path(os.path.join("audio", "inhale.wav"))):
                self.inhale_sound = mixer.Sound(get_resource_path(os.path.join("audio", "inhale.wav")))
            if os.path.exists(get_resource_path(os.path.join("audio", "hold.wav"))):
                self.hold_sound = mixer.Sound(get_resource_path(os.path.join("audio", "hold.wav")))
            if os.path.exists(get_resource_path(os.path.join("audio", "exhale.wav"))):
                self.exhale_sound = mixer.Sound(get_resource_path(os.path.join("audio", "exhale.wav")))
            if os.path.exists(get_resource_path(os.path.join("audio", "background.wav"))):
                self.background_music = mixer.Sound(get_resource_path(os.path.join("audio", "background.wav")))
                # Check settings for sound before playing
                if self.settings.get('sound', True):
                    self.background_music.play(-1)
        except Exception as e:
            print(f"Warning: Error loading audio files: {e}")

        quotes = [
            "Breathe deeply, for each breath is a new opportunity. -Unknown",
            "Inhale strength, exhale weakness. -Unknown",
            "“Your breath is your anchor. Use it to return to the present\n moment.” – Unknown",
            "“The mind is like water. When it's calm, everything is clear\n.” – Unknown",
            "“Take a deep breath. It's just a bad day, not a bad life.”\n – Unknown",
            "“To breathe is to live, and to live is to be mindful.” – Unknown",
            "“Every breath you take can change your life.” – Unknown",
            "“Mindfulness isn't difficult. What's difficult is to remember\n to be mindful.” – Sharon Salzberg",
            "“Breathe in peace, breathe out stress.” – Unknown"
            "“Life is a balance of holding on and\n letting go. Breathe deeply\n with every in-breath.” – Unknown",
            "“Strength doesn't come from what\n you can do. It comes from overcoming the things you once\n thought you couldn't.” – Rikki Rogers",
            "“The strongest people are not those who show strength in front of\n us but those who win battles we know nothing about.” – Unknown",
            "You are stronger than you think. Your resilience is your power."
            "“Fall seven times, stand up eight.” – Japanese Proverb",
            "“What lies behind us and what lies before us are tiny matters compared\n to what lies within us.” – Ralph Waldo Emerson",
            "“Your strength is a culmination of your struggles.” – Unknown",
            "“You never know how strong you are until\n being strong is your only choice\n.” – Bob Marley",
            "“Strength grows in the moments when you\n think you can't go on but you keep\n going anyway.” – Unknown",
            "“Difficulties mastered are opportunities won.” – Winston Churchill",
            "It's not the load that breaks you down, it's the way you carry it."
        ]

        self.Changing_text = ctk.CTkLabel(
            self,
            text="Welcome",
            font=("Arial", 30, "bold")
        )
        self.Changing_text.place(relx=0.5, rely=0.1, anchor="center")

        self.progress_container = ctk.CTkFrame(self)
        self.progress_container.place(relx=0.5, rely=0.5, anchor="center")
        
        self.Quotes_text = ctk.CTkLabel(
            self,
            text=random.choice(quotes),
            font=("Arial", 24, "bold")
        )
        self.Quotes_text.place(relx=0.5, rely=0.8, anchor="center")

        self.create_progress_indicators()
        
        button_width = 140
        spacing = 20
        start_x = (800 - (2 * button_width + spacing)) // 2
        button_y = 550

        self.restart_button = ctk.CTkButton(
            self,
            text="Restart",
            image=ctk.CTkImage(Image.open(get_resource_path("icons/restart.png")), size=(20, 20)),
            width=button_width,
            command=self.start_countdown
        )
        self.restart_button.place(x=start_x, y=button_y)

        self.done_button = ctk.CTkButton(
            self,
            text="Done",
            image=ctk.CTkImage(Image.open(get_resource_path("icons/done.png")), size=(20, 20)),
            width=button_width,
            command=self.done_button_click
        )
        self.done_button.place(x=start_x + button_width + spacing, y=button_y)
        
        # Make sure to lift all widgets above the background
        self.Changing_text.lift()
        self.progress_container.lift()
        self.Quotes_text.lift()
        self.restart_button.lift()
        self.done_button.lift()
    
    def create_progress_indicators(self):
        for widget in self.progress_container.winfo_children():
            widget.destroy()

        # Always get fresh settings when creating indicators
        self.settings = self.get_settings()
        
        if self.settings['progress_style'] == 'bars':
            self.progress_bars = []
            bar_width = 200
            spacing = 20
            
            for i in range(3):
                progress = ctk.CTkProgressBar(self.progress_container, width=bar_width)
                progress.set(0)
                progress.pack(side="left", padx=spacing)
                self.progress_bars.append(progress)
                
        elif self.settings['progress_style'] == 'circle':
            self.progress_indicator = CircleProgress(self.progress_container, size=300)
            self.progress_indicator.pack(padx=20)
            
        elif self.settings['progress_style'] == 'triangle':
            self.progress_indicator = TriangleProgress(self.progress_container, size=300)
            self.progress_indicator.pack(padx=20)

    def cancel_scheduled_tasks(self):
        # Stop all sounds
        self.stop_all_sounds()
            
        # Cancel scheduled tasks
        for task in self.scheduled_tasks:
            self.after_cancel(task)
        self.scheduled_tasks.clear()

    def stop_all_sounds(self):
        if hasattr(self, 'inhale_sound') and self.inhale_sound:
            self.inhale_sound.stop()
        if hasattr(self, 'hold_sound') and self.hold_sound:
            self.hold_sound.stop()
        if hasattr(self, 'exhale_sound') and self.exhale_sound:
            self.exhale_sound.stop()
        if hasattr(self, 'background_music') and self.background_music:
            self.background_music.stop()

    def start_countdown(self):
        self.stop_exercise()
        self.is_exercise_active = True
        
        if self.settings['progress_style'] == 'bars':
            for bar in self.progress_bars:
                bar.set(0)
            
        self.Changing_text.configure(text="Get Ready")
        
        self.scheduled_tasks.extend([
            self.after(1000, lambda: self.Changing_text.configure(text="3")),
            self.after(2000, lambda: self.Changing_text.configure(text="2")),
            self.after(3000, lambda: self.Changing_text.configure(text="1")),
            self.after(4000, self.start_inhale)
        ])
    
    def start_inhale(self):
        if self.settings['progress_style'] == 'bars':
            for bar in self.progress_bars:
                bar.set(0)
        self.Changing_text.configure(text="Inhale")
        self.play_sound('inhale')
        self.animate_progress(0, 0, 4000, lambda: self.start_hold())
    
    def start_hold(self):
        self.Changing_text.configure(text="Hold")
        self.play_sound('hold')
        self.animate_progress(1, 0, 7000, lambda: self.start_exhale())
    
    def start_exhale(self):
        self.Changing_text.configure(text="Exhale")
        self.play_sound('exhale')
        self.animate_progress(2, 0, 8000, self.complete_cycle)
    
    def complete_cycle(self):
        if hasattr(self.controller, 'data_handler') and self.controller.data_handler:
            stats = self.controller.data_handler.get_stats()
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            if today in stats:
                stats[today] += 1
            else:
                stats[today] = 1
            
            # Save updated stats    
            self.controller.data_handler.save_stats(stats)
            
            # Check for newly unlocked achievements
            total_cycles = sum(stats.values())
            unlocked_achievements = self.controller.data_handler.get_achievements()
            
            # Achievement definitions from AchievementsPage
            achievement_definitions = self.controller.frames[AchievementsPage].achievements
            
            # Check for cycle-based achievements
            for achievement_id, achievement in achievement_definitions.items():
                if (not achievement_id.startswith("streak_") and 
                    achievement_id not in unlocked_achievements and
                    total_cycles >= achievement["requirement"]):
                    
                    # Unlock the achievement
                    unlocked_achievements[achievement_id] = {
                        'unlocked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # Show notification for new achievement
                    if hasattr(self, 'Changing_text'):
                        self.after(100, lambda: self.Changing_text.configure(
                            text=f"Achievement Unlocked: {achievement['name']}"))
                        self.after(3000, lambda: self.Changing_text.configure(text="Inhale"))
            
            # Save updated achievements
            self.controller.data_handler.save_achievements(unlocked_achievements)
        
        # Continue with the next cycle
        self.start_inhale()

    def animate_progress(self, segment, current, duration, callback):
        if current <= duration:
            progress = current / duration
            
            if self.settings['progress_style'] == 'bars':
                self.progress_bars[segment].set(progress)
            else:
                self.progress_indicator.set_progress(segment, progress)
                
            task = self.after(50, lambda: self.animate_progress(segment, current + 50, duration, callback))
            self.scheduled_tasks.append(task)
        else:
            if self.settings['progress_style'] == 'bars':
                self.progress_bars[segment].set(1)
            else:
                self.progress_indicator.set_progress(segment, 1)
            callback()

    def play_sound(self, sound):
        if not self.is_exercise_active or not self.winfo_viewable():
            return
            
        # Get fresh settings to ensure we have the latest sound preference
        self.settings = self.get_settings()
        if self.settings.get('sound', True) and hasattr(self, sound + '_sound'):
            sound_obj = getattr(self, sound + '_sound')
            if sound_obj:
                sound_obj.play()

    def done_button_click(self):
        self.stop_exercise()
        self.controller.show_frame(StatsPage)

    def stop_exercise(self):
        self.is_exercise_active = False
        if hasattr(self, 'inhale_sound') and self.inhale_sound:
            self.inhale_sound.stop()
        if hasattr(self, 'hold_sound') and self.hold_sound:
            self.hold_sound.stop()
        if hasattr(self, 'exhale_sound') and self.exhale_sound:
            self.exhale_sound.stop()
        
        for task in self.scheduled_tasks:
            self.after_cancel(task)
        self.scheduled_tasks.clear()

    def toggle_background_music(self, should_play):
        # Get fresh settings to ensure we have the latest sound preference
        self.settings = self.get_settings()
        if hasattr(self, 'background_music') and self.background_music:
            if should_play and self.settings.get('sound', True):
                self.background_music.play(-1)
            else:
                self.background_music.stop()

    def play_background_music(self):
        try:
            mixer.init()
            mixer.music.load(get_resource_path("audio/background.wav"))
            mixer.music.play(-1)  # -1 means loop indefinitely
        except Exception as e:
            logging.error(f"Error playing background music: {e}")

    def get_settings(self):
        if hasattr(self.controller, 'data_handler') and self.controller.data_handler:
            return self.controller.data_handler.get_settings()
        else:
            # Default settings if no user is logged in
            return {
                'progress_style': 'bars',
                'sound': True,
                'breathing_times': {
                    'inhale': 4,
                    'hold': 7,
                    'exhale': 8
                }
            }

class StatsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Add background canvas
        self.bg_canvas = BackgroundCanvas(self)
        self.bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        self.Stats = ctk.CTkLabel(
            self,
            text="Stats",
            font=("Arial", 30, "bold")
        )
        self.Stats.place(relx=0.5, rely=0.05, anchor="center")
        self.Stats.lift()

        self.back_button = ctk.CTkButton(
            self,
            text="Back",
            image=ctk.CTkImage(Image.open(get_resource_path("icons/back.png")), size=(20, 20)),
            command=lambda: controller.show_frame(StartingPage)
        )
        self.back_button.place(relx=0.5, rely=0.95, anchor="center")
        self.back_button.lift()

        self.graph_frame = ctk.CTkFrame(self)
        self.graph_frame.place(relx=0.5, rely=0.4, anchor="center")
        
        self.update_graph()

    def update_graph(self):
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

        if self.controller.data_handler:
            stats = self.controller.data_handler.get_stats()
        else:
            stats = {}  # Default empty stats if no user is logged in

        if not stats:
            no_data = ctk.CTkLabel(
                self.graph_frame,
                text="No breathing exercises completed yet",
                font=("Arial", 16)
            )
            no_data.pack(pady=20)
            return

        fig, ax = plt.subplots(figsize=(8, 4))
        dates = list(stats.keys())[-7:]
        counts = [stats.get(date, 0) for date in dates]
        total_cycles = sum(stats.values())
        streak = self.calculate_streak(stats)
        stats_frame = ctk.CTkFrame(self)
        stats_frame.place(relx=0.5, rely=0.8, anchor="center")

        # Display statistics
        cycle_label = ctk.CTkLabel(stats_frame, text=f"Total Cycles: {total_cycles}", font=("Arial", 16))
        cycle_label.pack(pady=5)

        streak_label = ctk.CTkLabel(stats_frame, text=f"Current Streak: {streak}", font=("Arial", 16))
        streak_label.pack(pady=5)
        
        ax.bar(dates, counts)
        ax.set_xlabel('Date')
        ax.set_ylabel('Completed Cycles')
        ax.set_title('Breathing Exercises Per Day')
        plt.xticks(rotation=45)
        
        canvas = FigureCanvasTkAgg(fig, self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def calculate_streak(self, stats):
        # Calculate the current streak of consecutive days
        today = datetime.now().date()
        dates = sorted([datetime.strptime(date, '%Y-%m-%d').date() for date in stats.keys()])
        
        if not dates:
            return 0
            
        # Check if today is in the stats
        if today in dates:
            streak = 1
        else:
            return 0  # No exercise today, no streak
            
        prev_date = today
        for date in sorted(dates, reverse=True):
            if (prev_date - date).days == 1:
                streak += 1
                prev_date = date
            elif (prev_date - date).days > 1:
                break
                
        return streak

class NotificationManager:
    def __init__(self):
        print("Initializing NotificationManager...")
        self.notification_thread = None
        self.is_running = False
        self.last_notification_time = None
        self.settings_last_modified = None
        self.user_data_handler = None
        
        # Default settings
        self.settings = {
            'enabled': True,
            'time': '09:00'
        }
        
    def set_data_handler(self, data_handler):
        self.user_data_handler = data_handler
        if self.user_data_handler:
            self.settings = self.user_data_handler.get_notification_settings()
            print(f"Loaded notification settings: {self.settings}")

    def save_settings(self):
        print("Saving notification settings...")
        if self.user_data_handler:
            self.user_data_handler.save_notification_settings(self.settings)
            print("Settings saved successfully to Supabase")
            self.last_notification_time = None  # Reset last notification time
        else:
            print("No data handler available to save settings")

    def start_notification_thread(self):
        print("Starting notification thread...")
        if self.notification_thread is None or not self.notification_thread.is_alive():
            self.is_running = True
            self.notification_thread = threading.Thread(target=self.notification_loop)
            self.notification_thread.daemon = True
            self.notification_thread.start()
            print("Notification thread started")

    def stop_notification_thread(self):
        print("Stopping notification thread...")
        self.is_running = False
        if self.notification_thread:
            self.notification_thread.join(timeout=1)
        print("Notification thread stopped")

    def check_settings_updated(self):
        if self.user_data_handler:
            current_settings = self.user_data_handler.get_notification_settings()
            if current_settings != self.settings:
                self.settings = current_settings
                self.last_notification_time = None  # Reset last notification time
                print("Settings updated from Supabase:", self.settings)
                return True
        return False

    def should_send_notification(self):
        if not self.settings['enabled']:
            print("Notifications are disabled")
            return False

        # Check if settings have been updated
        self.check_settings_updated()

        now = datetime.now()
        try:
            notification_time = datetime.strptime(self.settings['time'], '%H:%M').time()
            current_time = now.time()
            target_datetime = datetime.combine(now.date(), notification_time)
            
            print(f"\nNotification Debug Info:")
            print(f"Current time: {current_time.strftime('%H:%M:%S')}")
            print(f"Target time: {notification_time.strftime('%H:%M')}")
            print(f"Scheduled for: {target_datetime.strftime('%Y-%m-%d %H:%M')}")
            print(f"Last notification sent: {self.last_notification_time}")
            
            # Only proceed if hours and minutes match exactly
            time_matches = (current_time.hour == notification_time.hour and 
                          current_time.minute == notification_time.minute)
            
            if time_matches:
                # Make sure we haven't sent a notification in the last 30 seconds
                if (self.last_notification_time and 
                    (now - self.last_notification_time).total_seconds() < 30):
                    print("Skipping: Last notification was sent less than 30 seconds ago")
                    return False
                    
                print(f"✓ It's notification time! Preparing to send notification...")
                return True
            
            print("× Not notification time yet")
            return False
            
        except Exception as e:
            print(f"Error checking notification time: {e}")
            return False

    def notification_loop(self):
        print("\nStarting notification loop...")
        print("Notification system is running and checking for scheduled times")
        while self.is_running:
            try:
                if self.should_send_notification():
                    self.send_notification()
                    self.last_notification_time = datetime.now()
                    print(f"✓ Notification sent at: {self.last_notification_time.strftime('%Y-%m-%d %H:%M:%S')}")
                time.sleep(1)  # Check every second
                    
            except Exception as e:
                print(f"Error in notification loop: {e}")
                time.sleep(5)

    def send_notification(self):
        try:
            print("\nSending notification...")
            notification.notify(
                title='StillMind Reminder',
                message='Time for your daily breathing exercise!',
                app_icon=None,
                timeout=10,
            )
            print("✓ Notification sent successfully")
        except Exception as e:
            print(f"× Error sending notification: {e}")

class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Add background canvas
        self.bg_canvas = BackgroundCanvas(self)
        self.bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Title
        self.Settings = ctk.CTkLabel(
            self,
            text="Settings",
            font=("Arial", 30, "bold")
        )
        self.Settings.place(relx=0.5, rely=0.1, anchor="center")
        self.Settings.lift()

        # Create main scrollable frame for all settings
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            width=500,
            height=400
        )
        self.scrollable_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Load settings
        self.settings = self.get_settings()

        # Create frames for different setting sections
        general_frame = ctk.CTkFrame(self.scrollable_frame)
        general_frame.pack(fill="x", padx=20, pady=10)

        # General Settings
        general_label = ctk.CTkLabel(general_frame, text="General Settings", font=("Arial", 16, "bold"))
        general_label.pack(pady=10)

        # Theme setting
        theme_frame = ctk.CTkFrame(general_frame)
        theme_frame.pack(fill="x", padx=20, pady=5)
        theme_label = ctk.CTkLabel(theme_frame, text="Theme:", anchor="center")
        theme_label.pack(side="left", expand=True)
        self.theme_switch = ctk.CTkSwitch(
            theme_frame,
            text="Dark Mode",
            command=self.toggle_theme,
            onvalue=True,
            offvalue=False
        )
        self.theme_switch.pack(side="right", expand=True)
        self.theme_switch.select() if self.settings['theme'] == 'dark' else self.theme_switch.deselect()

        # Sound setting
        sound_frame = ctk.CTkFrame(general_frame)
        sound_frame.pack(fill="x", padx=20, pady=5)
        sound_label = ctk.CTkLabel(sound_frame, text="Sound:", anchor="center")
        sound_label.pack(side="left", expand=True)
        self.sound_switch = ctk.CTkSwitch(
            sound_frame,
            text="Enable Sound",
            command=self.toggle_sound,
            onvalue=True,
            offvalue=False
        )
        self.sound_switch.pack(side="right", expand=True)
        self.sound_switch.select() if self.settings['sound'] else self.sound_switch.deselect()

        # Breathing Settings
        breathing_frame = ctk.CTkFrame(self.scrollable_frame)
        breathing_frame.pack(fill="x", padx=20, pady=10)

        breathing_label = ctk.CTkLabel(breathing_frame, text="Breathing Times (seconds)", font=("Arial", 16, "bold"))
        breathing_label.pack(pady=10)

        # Inhale setting
        inhale_frame = ctk.CTkFrame(breathing_frame)
        inhale_frame.pack(fill="x", padx=20, pady=5)
        inhale_label = ctk.CTkLabel(inhale_frame, text="Inhale:", anchor="center")
        inhale_label.pack(side="left", expand=True)
        self.inhale_entry = ctk.CTkEntry(inhale_frame, width=100)
        self.inhale_entry.pack(side="right", expand=True)
        self.inhale_entry.insert(0, str(self.settings['breathing_times']['inhale']))

        # Hold setting
        hold_frame = ctk.CTkFrame(breathing_frame)
        hold_frame.pack(fill="x", padx=20, pady=5)
        hold_label = ctk.CTkLabel(hold_frame, text="Hold:", anchor="center")
        hold_label.pack(side="left", expand=True)
        self.hold_entry = ctk.CTkEntry(hold_frame, width=100)
        self.hold_entry.pack(side="right", expand=True)
        self.hold_entry.insert(0, str(self.settings['breathing_times']['hold']))

        # Exhale setting
        exhale_frame = ctk.CTkFrame(breathing_frame)
        exhale_frame.pack(fill="x", padx=20, pady=5)
        exhale_label = ctk.CTkLabel(exhale_frame, text="Exhale:", anchor="center")
        exhale_label.pack(side="left", expand=True)
        self.exhale_entry = ctk.CTkEntry(exhale_frame, width=100)
        self.exhale_entry.pack(side="right", expand=True)
        self.exhale_entry.insert(0, str(self.settings['breathing_times']['exhale']))

        # Progress Style Settings
        style_frame = ctk.CTkFrame(self.scrollable_frame)
        style_frame.pack(fill="x", padx=20, pady=10)

        style_label = ctk.CTkLabel(style_frame, text="Progress Style", font=("Arial", 16, "bold"))
        style_label.pack(pady=10)

        self.style_var = ctk.StringVar(value=self.settings['progress_style'])
        self.style_menu = ctk.CTkOptionMenu(
            style_frame,
            values=['bars', 'circle', 'triangle'],
            variable=self.style_var,
            command=self.change_progress_style
        )
        self.style_menu.pack(pady=10)

        # Notification Settings
        notification_frame = ctk.CTkFrame(self.scrollable_frame)
        notification_frame.pack(fill="x", padx=20, pady=10)

        notification_label = ctk.CTkLabel(notification_frame, text="Daily Reminder", font=("Arial", 16, "bold"))
        notification_label.pack(pady=10)

        # Load notification settings
        self.notification_settings = self.get_notification_settings()

        # Notification switch
        notification_switch_frame = ctk.CTkFrame(notification_frame)
        notification_switch_frame.pack(fill="x", padx=20, pady=5)
        self.notification_switch = ctk.CTkSwitch(
            notification_switch_frame,
            text="Enable Notifications",
            command=self.toggle_notifications
        )
        self.notification_switch.pack(expand=True)
        self.notification_switch.select() if self.notification_settings['enabled'] else self.notification_switch.deselect()

        # Time picker frame
        time_picker_frame = ctk.CTkFrame(notification_frame)
        time_picker_frame.pack(pady=5)

        current_hour = self.notification_settings['time'].split(':')[0]
        self.hours_var = ctk.StringVar(value=current_hour)
        self.hours_dropdown = ctk.CTkOptionMenu(
            time_picker_frame,
            values=[f"{i:02d}" for i in range(24)],
            variable=self.hours_var,
            command=self.update_notification_time
        )
        self.hours_dropdown.pack(side="left", padx=5)

        # Minutes dropdown (similar to hours)
        current_minute = self.notification_settings['time'].split(':')[1]
        self.minutes_var = ctk.StringVar(value=current_minute)
        self.minutes_dropdown = ctk.CTkOptionMenu(
            time_picker_frame,
            values=[f"{i:02d}" for i in range(60)],
            variable=self.minutes_var,
            command=self.update_notification_time
        )
        self.minutes_dropdown.pack(side="left", padx=5)

        # Save Button
        self.save_button = ctk.CTkButton(
            self.scrollable_frame,
            text="Save Changes",
            command=self.save_changes
        )
        self.save_button.pack(pady=20)

        # Back Button
        self.back_button = ctk.CTkButton(
            self,
            text="Back",
            image=ctk.CTkImage(Image.open(get_resource_path("icons/back.png")), size=(20, 20)),
            command=lambda: controller.show_frame(StartingPage)
        )
        self.back_button.place(relx=0.5, rely=0.9, anchor="center")
        self.back_button.lift()

    def get_settings(self):
        if self.controller.data_handler:
            return self.controller.data_handler.get_settings()
        else:
            # Default settings if no user is logged in
            return {
                'theme': 'dark',
                'sound': True,
                'breathing_times': {
                    'inhale': 4,
                    'hold': 7,
                    'exhale': 8
                },
                'notifications': True,
                'progress_style': 'bars'
            }

    def get_notification_settings(self):
        if self.controller.data_handler:
            return self.controller.data_handler.get_notification_settings()
        else:
            # Default notification settings if no user is logged in
            return {
                'enabled': True,
                'time': '09:00'
            }

    def toggle_theme(self):
        self.settings['theme'] = 'dark' if self.theme_switch.get() else 'light'
        # Update theme immediately
        if self.settings['theme'] == 'dark':
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")
        
        # Update button colors
        button_color = get_button_color()
        for frame in self.controller.frames.values():
            for widget in frame.winfo_children():
                if isinstance(widget, ctk.CTkButton):
                    widget.configure(fg_color=button_color)
        
        # Update all background canvases
        for frame in self.controller.frames.values():
            if hasattr(frame, 'bg_canvas'):
                frame.bg_canvas.update_background_color()
        
        self.save_settings()

    def toggle_sound(self):
        self.settings['sound'] = self.sound_switch.get()
        self.save_settings()
        
        # Update sound state immediately in MainPage
        main_page = self.controller.frames[MainPage]
        if main_page:
            main_page.settings = self.settings  # Update MainPage settings
            main_page.toggle_background_music(self.sound_switch.get())

    def change_progress_style(self, choice):
        self.settings['progress_style'] = choice
        self.save_settings()
        
        # Immediately update MainPage settings
        if self.controller.frames[MainPage]:
            self.controller.frames[MainPage].settings = self.settings

    def refresh_settings_from_database(self):
        """Reload settings from database and update UI elements"""
        if self.controller.data_handler:
            self.settings = self.controller.data_handler.get_settings()
            self.notification_settings = self.controller.data_handler.get_notification_settings()
            
            # Update UI to reflect current settings
            self.theme_switch.select() if self.settings['theme'] == 'dark' else self.theme_switch.deselect()
            self.sound_switch.select() if self.settings.get('sound', True) else self.sound_switch.deselect()
            
            # Update breathing times
            self.inhale_entry.delete(0, 'end')
            self.inhale_entry.insert(0, str(self.settings['breathing_times']['inhale']))
            self.hold_entry.delete(0, 'end')
            self.hold_entry.insert(0, str(self.settings['breathing_times']['hold']))
            self.exhale_entry.delete(0, 'end')
            self.exhale_entry.insert(0, str(self.settings['breathing_times']['exhale']))
            
            # Update progress style dropdown
            self.style_var.set(self.settings['progress_style'])
            
            # Update notification settings
            self.notification_switch.select() if self.notification_settings['enabled'] else self.notification_switch.deselect()
            time_parts = self.notification_settings['time'].split(':')
            if len(time_parts) == 2:
                self.hours_var.set(time_parts[0])
                self.minutes_var.set(time_parts[1])
    
    def save_changes(self):
        try:
            self.settings['breathing_times']['inhale'] = int(self.inhale_entry.get())
            self.settings['breathing_times']['hold'] = int(self.hold_entry.get())
            self.settings['breathing_times']['exhale'] = int(self.exhale_entry.get())
            self.save_settings()
            messagebox.showinfo("Success", "Settings saved successfully!")
            
            # Immediately apply settings to MainPage
            if self.controller.frames[MainPage]:
                self.controller.frames[MainPage].settings = self.settings
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for breathing times")
    
    def change_progress_style(self, choice):
        self.settings['progress_style'] = choice
        self.save_settings()
        
        # Immediately update MainPage settings
        if self.controller.frames[MainPage]:
            self.controller.frames[MainPage].settings = self.settings
    
    def save_settings(self):
        if self.controller.data_handler:
            self.controller.data_handler.save_settings(self.settings)
        # If no data handler, settings won't be saved (logged out state)

    def toggle_notifications(self):
        self.notification_settings['enabled'] = self.notification_switch.get()
        self.save_notification_settings()
    
    def update_notification_time(self, *args):
        hour = self.hours_var.get()
        minute = self.minutes_var.get()
        new_time = f"{hour}:{minute}"
        
        if new_time != self.notification_settings['time']:
            self.notification_settings['time'] = new_time
            self.save_notification_settings()
    
    def save_notification_settings(self):
        if self.controller.data_handler:
            self.controller.data_handler.save_notification_settings(self.notification_settings)
        # If no data handler, settings won't be saved (logged out state)

class CircleProgress(ctk.CTkCanvas):
    def __init__(self, parent, size=200, **kwargs):
        super().__init__(parent, width=size, height=size, highlightthickness=0, borderwidth=0, bg="#333333", **kwargs)
        self.size = size
        self.segments = 3
        self.current_segment = 0
        self.progress = 0
        self.draw_circle()
    
    def draw_circle(self):
        self.delete("all")
        center = self.size // 2
        radius = (self.size - 20) // 2
        
        for i in range(self.segments):
            start = i * (360 / self.segments)
            end = (i + 1) * (360 / self.segments)
            
            if i < self.current_segment:
                fill = "green"
            elif i == self.current_segment:
                fill = "green"
                end = start + (end - start) * self.progress
            else:
                fill = "gray"
                
            start_rad = math.radians(start - 90)
            end_rad = math.radians(end - 90)
            
            x1 = center + radius * math.cos(start_rad)
            y1 = center + radius * math.sin(start_rad)
            x2 = center + radius * math.cos(end_rad)
            y2 = center + radius * math.sin(end_rad)
            
            self.create_arc(
                20, 20, self.size-20, self.size-20,
                start=start-90, extent=end-start,
                fill=fill, outline="white"
            )
    
    def set_progress(self, segment, progress):
        self.current_segment = segment
        self.progress = progress
        self.draw_circle()

class TriangleProgress(ctk.CTkCanvas):
    def __init__(self, parent, size=200, **kwargs):
        super().__init__(parent, width=size, height=size, highlightthickness=0, borderwidth=0, bg="#333333", **kwargs)
        self.size = size
        self.current_side = 0
        self.progress = 0
        self.draw_triangle()
    
    def draw_triangle(self):
        self.delete("all")
        padding = 20
        height = self.size - 2 * padding
        width = height * math.sqrt(3) / 2
        
        top = (self.size/2, padding)
        bottom_left = (self.size/2 - width/2, self.size - padding)
        bottom_right = (self.size/2 + width/2, self.size - padding)
        
        sides = [
            (top, bottom_right),
            (bottom_right, bottom_left),
            (bottom_left, top)
        ]
        
        # Draw each side with thicker lines (increased from 3 to 8)
        for i, (start, end) in enumerate(sides):
            if i < self.current_side:
                color = "green"  # Completed sides
            elif i == self.current_side:
                # Current side - partially filled
                mid_x = start[0] + (end[0] - start[0]) * self.progress
                mid_y = start[1] + (end[1] - start[1]) * self.progress
                self.create_line(start[0], start[1], mid_x, mid_y, fill="green", width=8)
                self.create_line(mid_x, mid_y, end[0], end[1], fill="gray", width=8)
                continue
            else:
                color = "gray"  # Future sides
            
            self.create_line(start[0], start[1], end[0], end[1], fill=color, width=8)
    
    def set_progress(self, side, progress):
        self.current_side = side
        self.progress = progress
        self.draw_triangle()

class AchievementsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Define achievements dictionary - this is our achievement definitions, not unlocked achievements
        self.achievements = {
            "first_breath": {
                "name": "First Breath",
                "description": "Complete your first breathing exercise",
                "icon": "🌱",
                "requirement": 1
            },
            "beginner": {
                "name": "Beginner",
                "description": "Complete 10 breathing exercises",
                "icon": "🌿",
                "requirement": 10
            },
            "intermediate": {
                "name": "Intermediate",
                "description": "Complete 50 breathing exercises",
                "icon": "🌳",
                "requirement": 50
            },
            "advanced": {
                "name": "Advanced",
                "description": "Complete 100 breathing exercises",
                "icon": "🌲",
                "requirement": 100
            },
            "master": {
                "name": "Breath Master",
                "description": "Complete 500 breathing exercises",
                "icon": "🏆",
                "requirement": 500
            },
            "streak_3": {
                "name": "Consistent",
                "description": "Maintain a 3-day streak",
                "icon": "📆",
                "requirement": 3
            },
            "streak_7": {
                "name": "Dedicated",
                "description": "Maintain a 7-day streak",
                "icon": "🔥",
                "requirement": 7
            },
            "streak_30": {
                "name": "Committed",
                "description": "Maintain a 30-day streak",
                "icon": "⭐",
                "requirement": 30
            }
        }
        
        # Add background canvas
        self.bg_canvas = BackgroundCanvas(self)
        self.bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self, text="Achievements", font=("Arial", 30, "bold")
        )
        self.title_label.place(relx=0.5, rely=0.05, anchor="center")
        self.title_label.lift()

        # Create scrollable frame for achievements
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            width=700,
            height=400
        )
        self.scrollable_frame.place(relx=0.5, rely=0.45, anchor="center")

        # Back button
        self.back_button = ctk.CTkButton(
            self,
            text="Back",
            image=ctk.CTkImage(Image.open(get_resource_path("icons/back.png")), size=(20, 20)),
            command=lambda: controller.show_frame(StartingPage)
        )
        self.back_button.place(relx=0.5, rely=0.9, anchor="center")
        self.back_button.lift()

        self.update_achievements()

    def calculate_streak(self, stats):
        # Calculate the current streak of consecutive days
        today = datetime.now().date()
        dates = sorted([datetime.strptime(date, '%Y-%m-%d').date() for date in stats.keys()])
        
        if not dates:
            return 0
            
        # Check if today is in the stats
        if today in dates:
            streak = 1
        else:
            return 0  # No exercise today, no streak
            
        prev_date = today
        for date in sorted(dates, reverse=True):
            if (prev_date - date).days == 1:
                streak += 1
                prev_date = date
            elif (prev_date - date).days > 1:
                break
                
        return streak

    def update_achievements(self):
        # Clear existing achievements display
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Load user stats
        stats = {}
        if hasattr(self.controller, 'data_handler') and self.controller.data_handler:
            stats = self.controller.data_handler.get_stats()

        # Calculate total cycles and current streak
        total_cycles = sum(stats.values()) if stats else 0
        current_streak = self.calculate_streak(stats)

        # Load unlocked achievements from database
        unlocked_achievements = {}
        if hasattr(self.controller, 'data_handler') and self.controller.data_handler:
            unlocked_achievements = self.controller.data_handler.get_achievements()
            print(f"Loaded achievements from database: {unlocked_achievements}")  # Debugging

        # Display achievements
        for i, (achievement_id, achievement) in enumerate(self.achievements.items()):
            # Check if achievement is unlocked
            is_unlocked = False
            unlock_date = None
            
            # If already in unlocked achievements
            if achievement_id in unlocked_achievements:
                is_unlocked = True
                # Handle the unlocked_at value - it could be a string or a nested dictionary
                if isinstance(unlocked_achievements[achievement_id], dict):
                    unlock_date = unlocked_achievements[achievement_id].get('unlocked_at', 'Unknown date')
                else:
                    unlock_date = unlocked_achievements[achievement_id]
            # Or if meets requirements now
            elif achievement_id.startswith("streak_"):
                req_streak = achievement["requirement"]
                if current_streak >= req_streak:
                    is_unlocked = True
            else:
                # Check total cycles for other achievements
                if total_cycles >= achievement["requirement"]:
                    is_unlocked = True
            
            # Update unlocked achievements in database if newly unlocked
            if is_unlocked and achievement_id not in unlocked_achievements and hasattr(self.controller, 'data_handler') and self.controller.data_handler:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                unlocked_achievements[achievement_id] = {
                    'unlocked_at': current_time
                }
                # Save to database
                self.controller.data_handler.save_achievements(unlocked_achievements)
                unlock_date = current_time
                print(f"New achievement unlocked: {achievement_id} at {unlock_date}")  # Debugging
            
            # Create achievement frame
            achievement_frame = ctk.CTkFrame(self.scrollable_frame)
            achievement_frame.pack(fill="x", padx=10, pady=5, ipady=5)
            
            # Icon
            icon_label = ctk.CTkLabel(
                achievement_frame, 
                text=achievement["icon"], 
                font=("Arial", 28)
            )
            icon_label.pack(side="left", padx=10)
            
            # Achievement info
            info_frame = ctk.CTkFrame(achievement_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, padx=10)
            
            # Title
            title_label = ctk.CTkLabel(
                info_frame, 
                text=achievement["name"], 
                font=("Arial", 16, "bold")
            )
            title_label.pack(anchor="w")
            
            # Description
            desc_label = ctk.CTkLabel(
                info_frame, 
                text=achievement["description"],
                font=("Arial", 12)
            )
            desc_label.pack(anchor="w")
            
            # Status
            status_frame = ctk.CTkFrame(achievement_frame, fg_color="transparent")
            status_frame.pack(side="right", padx=10)
            
            if is_unlocked:
                status_label = ctk.CTkLabel(
                    status_frame, 
                    text="UNLOCKED", 
                    font=("Arial", 14, "bold"),
                    text_color="#4CAF50"
                )
                status_label.pack()
                
                if unlock_date:
                    try:
                        # Handle different date formats
                        if isinstance(unlock_date, str):
                            if ' ' in unlock_date:
                                # Format like "2023-01-01 12:34:56"
                                date_part = unlock_date.split(' ')[0]
                            else:
                                # Already just the date part
                                date_part = unlock_date
                        else:
                            date_part = str(unlock_date)
                            
                        date_label = ctk.CTkLabel(
                            status_frame,
                            text=f"on {date_part}",
                            font=("Arial", 10)
                        )
                        date_label.pack()
                    except Exception as e:
                        print(f"Error displaying date: {e}, date value: {unlock_date}")
            else:
                status_label = ctk.CTkLabel(
                    status_frame, 
                    text="LOCKED", 
                    font=("Arial", 14, "bold"),
                    text_color="#F44336"
                )
                status_label.pack()
                
                if achievement_id.startswith("streak_"):
                    progress_label = ctk.CTkLabel(
                        status_frame,
                        text=f"{current_streak}/{achievement['requirement']} days",
                        font=("Arial", 10)
                    )
                    progress_label.pack()
                else:
                    progress_label = ctk.CTkLabel(
                        status_frame,
                        text=f"{total_cycles}/{achievement['requirement']} cycles",
                        font=("Arial", 10)
                    )
                    progress_label.pack()

class HelpPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Add background canvas
        self.bg_canvas = BackgroundCanvas(self)
        self.bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Title
        self.title = ctk.CTkLabel(
            self,
            text="Help & Information",
            font=("Arial", 30, "bold")
        )
        self.title.place(relx=0.5, rely=0.05, anchor="center")
        self.title.lift()

        # Create scrollable frame for help content
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            width=700,
            height=400
        )
        self.scrollable_frame.place(relx=0.5, rely=0.45, anchor="center")
        self.scrollable_frame.lift()

        # Help content
        help_sections = {
            "Getting Started": [
                "Click 'Start' to begin a breathing exercise",
                "Follow the on-screen instructions for inhaling, holding, and exhaling",
                "Complete cycles to earn achievements"
            ],
            "Features": [
                "Track your progress in the Stats page",
                "Earn achievements as you practice",
                "Customize your experience in Settings",
                "Choose different progress indicators"
            ],
            "Settings": [
                "Toggle Dark/Light mode",
                "Enable/Disable sounds",
                "Adjust breathing times",
                "Change progress style"
            ],
            "Tips": [
                "Practice regularly for best results",
                "Find a quiet, comfortable space",
                "Maintain good posture while breathing",
                "Stay consistent to build streaks"
            ]
        }

        for section, items in help_sections.items():
            # Section header
            section_label = ctk.CTkLabel(
                self.scrollable_frame,
                text=section,
                font=("Arial", 20, "bold")
            )
            section_label.pack(anchor="w", pady=(20, 10), padx=20)

            # Section items
            for item in items:
                item_label = ctk.CTkLabel(
                    self.scrollable_frame,
                    text=f"• {item}",
                    font=("Arial", 14),
                    wraplength=650,
                    justify="left"
                )
                item_label.pack(anchor="w", pady=5, padx=40)

        # Back button with icon
        self.back_button = ctk.CTkButton(
            self,
            text="Back",
            image=ctk.CTkImage(Image.open(get_resource_path("icons/back.png")), size=(20, 20)),
            command=lambda: controller.show_frame(StartingPage)
        )
        self.back_button.place(relx=0.5, rely=0.9, anchor="center")
        self.back_button.lift()

class AccountPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Add background canvas
        self.bg_canvas = BackgroundCanvas(self)
        self.bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self, text="Account Settings", font=("Arial", 30, "bold")
        )
        self.title_label.place(relx=0.5, rely=0.1, anchor="center")
        self.title_label.lift()
        
        # Create main frame
        self.main_frame = ctk.CTkFrame(self, width=500, height=300)
        self.main_frame.place(relx=0.5, rely=0.45, anchor="center")
        
        # We'll load the user info when the page is shown, not in init
        
        # Back button
        self.back_button = ctk.CTkButton(
            self,
            text="Back",
            image=ctk.CTkImage(Image.open(get_resource_path("icons/back.png")), size=(20, 20)),
            command=lambda: controller.show_frame(StartingPage)
        )
        self.back_button.place(relx=0.5, rely=0.85, anchor="center")
    
    def load_user_info(self):
        """Load user info from Supabase"""
        # Clear previous content
        for widget in self.main_frame.winfo_children():
            widget.destroy()
            
        # Check if logged in
        if not hasattr(self.controller, 'data_handler') or self.controller.data_handler is None:
            not_logged_in = ctk.CTkLabel(
                self.main_frame,
                text="You are not logged in",
                font=("Arial", 16)
            )
            not_logged_in.pack(pady=50)
            return
            
        try:
            # Get user info from Supabase
            user = supabase.auth.get_user()
            email = user.user.email if user and hasattr(user, 'user') else "Unknown"
            
            email_label = ctk.CTkLabel(
                self.main_frame,
                text=f"Email: {email}",
                font=("Arial", 16)
            )
            email_label.pack(pady=20)
            
            # Add logout button
            logout_button = ctk.CTkButton(
                self.main_frame,
                text="Logout",
                command=self.logout
            )
            logout_button.pack(pady=10)
            
            # Add reset password button 
            reset_password_button = ctk.CTkButton(
                self.main_frame,
                text="Reset Password",
                command=self.reset_password
            )
            reset_password_button.pack(pady=20)
            
            # Add delete account button with warning
            delete_account_button = ctk.CTkButton(
                self.main_frame,
                text="Delete Account",
                fg_color="#FF5252",
                hover_color="#FF0000",
                command=self.confirm_delete_account
            )
            delete_account_button.pack(pady=10)
            
        except Exception as e:
            error_label = ctk.CTkLabel(
                self.main_frame,
                text=f"Error loading user info: {str(e)}",
                text_color="#FF0000"
            )
            error_label.pack(pady=20)
    
    def logout(self):
        """Log out the current user"""
        self.controller.logout()
    
    def reset_password(self):
        """Show password reset dialog"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Reset Password")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self)  # Set to be on top of the parent window
        dialog.grab_set()  # Modal
        
        # New password
        new_label = ctk.CTkLabel(dialog, text="New Password:")
        new_label.pack(pady=(20, 5))
        new_entry = ctk.CTkEntry(dialog, width=300, show="*")
        new_entry.pack()
        
        # Confirm new password
        confirm_label = ctk.CTkLabel(dialog, text="Confirm New Password:")
        confirm_label.pack(pady=(10, 5))
        confirm_entry = ctk.CTkEntry(dialog, width=300, show="*")
        confirm_entry.pack()
        
        # Status message
        status_label = ctk.CTkLabel(dialog, text="")
        status_label.pack(pady=10)
        
        # Submit button
        def change_password():
            new = new_entry.get()
            confirm = confirm_entry.get()
            
            if not new or not confirm:
                status_label.configure(text="Please fill all fields", text_color="#FF0000")
                return
                
            if new != confirm:
                status_label.configure(text="New passwords don't match", text_color="#FF0000")
                return
                
            try:
                # Change password using Supabase
                response = supabase.auth.update_user({"password": new})
                status_label.configure(text="Password changed successfully!", text_color="#00FF00")
                self.controller.after(2000, dialog.destroy)
            except Exception as e:
                status_label.configure(text=f"Error: {str(e)}", text_color="#FF0000")
        
        submit_button = ctk.CTkButton(dialog, text="Change Password", command=change_password)
        submit_button.pack(pady=10)
    
    def confirm_delete_account(self):
        """Show confirmation dialog for account deletion"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirm Account Deletion")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        warning_label = ctk.CTkLabel(
            dialog,
            text="WARNING: This action cannot be undone!\nAll your data will be permanently deleted.",
            text_color="#FF0000",
            font=("Arial", 14, "bold")
        )
        warning_label.pack(pady=20)
        
        # Password confirmation
        password_label = ctk.CTkLabel(dialog, text="Enter your password to confirm:")
        password_label.pack(pady=5)
        password_entry = ctk.CTkEntry(dialog, width=300, show="*")
        password_entry.pack()
        
        status_label = ctk.CTkLabel(dialog, text="")
        status_label.pack(pady=10)
        
        def delete_account():
            password = password_entry.get()
            if not password:
                status_label.configure(text="Please enter your password", text_color="#FF0000")
                return
                
            try:
                # Delete account from Supabase
                supabase.auth.delete_user()
                
                # Delete all user data from tables
                if self.controller.data_handler:
                    user_id = self.controller.data_handler.user_id
                    supabase.table("app_settings").delete().eq("user_id", user_id).execute()
                    supabase.table("breathing_stats").delete().eq("user_id", user_id).execute()
                    supabase.table("achievements").delete().eq("user_id", user_id).execute()
                    supabase.table("notification_settings").delete().eq("user_id", user_id).execute()
                
                status_label.configure(text="Account deleted successfully!", text_color="#00FF00")
                self.controller.after(2000, lambda: [dialog.destroy(), self.controller.logout()])
            except Exception as e:
                status_label.configure(text=f"Error: {str(e)}", text_color="#FF0000")
        
        buttons_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons_frame.pack(pady=10, fill="x")
        
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            command=dialog.destroy
        )
        cancel_button.pack(side="left", padx=20, expand=True)
        
        delete_button = ctk.CTkButton(
            buttons_frame,
            text="Delete Account",
            fg_color="#FF5252",
            hover_color="#FF0000",
            command=delete_account
        )
        delete_button.pack(side="right", padx=20, expand=True)

if __name__ == "__main__":
    app = App()
    app.mainloop() 