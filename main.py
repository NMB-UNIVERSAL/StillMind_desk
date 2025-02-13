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
except Exception as e:
    with open('startup_error.txt', 'w') as f:
        traceback.print_exc(file=f)
    print("Error during startup! Check startup_error.txt")
    input("Press Enter to exit...")

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
        logging.info("Starting StillMind application")
        with open("startup_test.txt", "w") as f:
            f.write("Program started\n")
            f.write(f"Running from: {os.getcwd()}\n")
            f.write(f"Executable path: {sys.executable}\n")
        try:
            super().__init__()
            logging.info("Initialized parent class")
            
            # Log resource paths
            logging.info(f"Current working directory: {os.getcwd()}")
            logging.info(f"Executable path: {sys.executable if getattr(sys, 'frozen', False) else 'Running in development'}")
            
            # Continue with your initialization
            self.title("StillMind")
            logging.info("Set window title")
            
            self.geometry("800x600")
            icon_path = get_resource_path("StillMind_icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
            
            # Initialize notification manager and start thread
            self.notification_manager = NotificationManager()
            self.notification_manager.start_notification_thread()
            
            self.container = ctk.CTkFrame(self)
            self.container.pack(side="top", fill="both", expand=True)
            
            self.container.grid_rowconfigure(0, weight=1)
            self.container.grid_columnconfigure(0, weight=1)
            
            self.frames = {}
            
            for F in (StartingPage, MainPage, StatsPage, SettingsPage, AchievementsPage, HelpPage):
                frame = F(self.container, self)
                self.frames[F] = frame
                frame.grid(row=0, column=0, sticky="nsew")
            
            self.show_frame(StartingPage)
            
            # Bind the closing event
            self.protocol("WM_DELETE_WINDOW", self.on_closing)
            
        except Exception as e:
            logging.error(f"Error during initialization: {str(e)}", exc_info=True)
            raise
    
    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()
        if hasattr(frame, 'bg_canvas'):
            frame.bg_canvas.update_background_color()
        if cont == MainPage:
            self.frames[MainPage].create_progress_indicators()
            self.frames[MainPage].start_countdown()
        elif cont == StatsPage:
            self.frames[MainPage].stop_exercise()
            self.frames[StatsPage].update_graph()
    
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
        
        # Load settings first
        try:
            with open(get_app_data_path('app_settings.json'), 'r') as f:
                self.settings = json.load(f)
        except FileNotFoundError:
            self.settings = {
                'progress_style': 'bars',
                'sound': True
            }
        
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

        try:
            with open(get_app_data_path('app_settings.json'), 'r') as f:
                self.settings = json.load(f)
        except FileNotFoundError:
            self.settings = {'progress_style': 'bars'}

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
        try:
            with open(get_app_data_path('breathing_stats.json'), 'r') as f:
                stats = json.load(f)
        except FileNotFoundError:
            stats = {}
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        if today in stats:
            stats[today] += 1
        else:
            stats[today] = 1
            
        with open(get_app_data_path('breathing_stats.json'), 'w') as f:
            json.dump(stats, f)
            
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
        self.display_statistics()

    def update_graph(self):
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

        try:
            with open(get_app_data_path('breathing_stats.json'), 'r') as f:
                stats = json.load(f)
        except FileNotFoundError:
            stats = {}

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
        
        ax.bar(dates, counts)
        ax.set_xlabel('Date')
        ax.set_ylabel('Completed Cycles')
        ax.set_title('Breathing Exercises Per Day')
        plt.xticks(rotation=45)
        
        canvas = FigureCanvasTkAgg(fig, self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def display_statistics(self):
        # Create a frame for statistics
        stats_frame = ctk.CTkFrame(self)
        stats_frame.place(relx=0.5, rely=0.8, anchor="center")

        # Load statistics from the JSON file
        try:
            with open(get_app_data_path('breathing_stats.json'), 'r') as f:
                stats = json.load(f)
        except FileNotFoundError:
            stats = {}

        # Calculate total cycles and streak
        total_cycles = sum(stats.values())
        streak = self.calculate_streak(stats)

        # Display statistics
        cycle_label = ctk.CTkLabel(stats_frame, text=f"Total Cycles: {total_cycles}", font=("Arial", 16))
        cycle_label.pack(pady=5)

        streak_label = ctk.CTkLabel(stats_frame, text=f"Current Streak: {streak}", font=("Arial", 16))
        streak_label.pack(pady=5)

        # You can add duration if you have a way to track it
        # For now, we'll just display a placeholder
        duration_label = ctk.CTkLabel(stats_frame, text="Average Duration: N/A", font=("Arial", 16))
        duration_label.pack(pady=5)

    def calculate_streak(self, stats):
        # Calculate the current streak of consecutive days
        streak = 0
        sorted_dates = sorted(stats.keys())
        for i in range(len(sorted_dates) - 1):
            if (datetime.strptime(sorted_dates[i + 1], '%Y-%m-%d') - 
                datetime.strptime(sorted_dates[i], '%Y-%m-%d')).days == 1:
                streak += 1
            else:
                break
        return streak + 1 if sorted_dates else 0  # Add 1 for the current day if there are any stats

class NotificationManager:
    def __init__(self):
        print("Initializing NotificationManager...")
        self.notification_thread = None
        self.is_running = False
        self.last_notification_time = None
        self.settings_last_modified = None
        try:
            with open(get_app_data_path('notification_settings.json'), 'r') as f:
                self.settings = json.load(f)
                print(f"Loaded notification settings: {self.settings}")
        except FileNotFoundError:
            self.settings = {
                'enabled': True,
                'time': '09:00'
            }
            print("No settings file found, using defaults:", self.settings)
            self.save_settings()

    def save_settings(self):
        print("Saving notification settings...")
        try:
            with open(get_app_data_path('notification_settings.json'), 'w') as f:
                json.dump(self.settings, f)
            print("Settings saved successfully")
            self.last_notification_time = None  # Reset last notification time
        except Exception as e:
            print(f"Error saving settings: {e}")

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
        try:
            current_mtime = os.path.getmtime(get_app_data_path('notification_settings.json'))
            if self.settings_last_modified != current_mtime:
                with open(get_app_data_path('notification_settings.json'), 'r') as f:
                    self.settings = json.load(f)
                self.settings_last_modified = current_mtime
                self.last_notification_time = None  # Reset last notification time
                print("Settings updated:", self.settings)
                return True
        except Exception as e:
            print(f"Error checking settings: {e}")
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
        try:
            with open(get_app_data_path('app_settings.json'), 'r') as f:
                self.settings = json.load(f)
        except FileNotFoundError:
            self.settings = {
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
            self.save_settings()

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
        try:
            with open(get_app_data_path('notification_settings.json'), 'r') as f:
                self.notification_settings = json.load(f)
        except FileNotFoundError:
            self.notification_settings = {
                'enabled': True,
                'time': '09:00'
            }

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
        
        # Update sound state immediately
        main_page = self.controller.frames[MainPage]
        main_page.toggle_background_music(self.settings['sound'])

    def change_progress_style(self, choice):
        self.settings['progress_style'] = choice
        self.save_settings()

    def save_changes(self):
        try:
            self.settings['breathing_times']['inhale'] = int(self.inhale_entry.get())
            self.settings['breathing_times']['hold'] = int(self.hold_entry.get())
            self.settings['breathing_times']['exhale'] = int(self.exhale_entry.get())
            self.save_settings()
            messagebox.showinfo("Success", "Settings saved successfully!")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for breathing times")

    def save_settings(self):
        with open(get_app_data_path('app_settings.json'), 'w') as f:
            json.dump(self.settings, f)

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
        with open(get_app_data_path('notification_settings.json'), 'w') as f:
            json.dump(self.notification_settings, f)

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
        
        # Add background canvas
        self.bg_canvas = BackgroundCanvas(self)
        self.bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Title
        self.title = ctk.CTkLabel(
            self,
            text="Achievements",
            font=("Arial", 30, "bold")
        )
        self.title.place(relx=0.5, rely=0.05, anchor="center")
        self.title.lift()

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

        # Define achievements
        self.achievements = {
            'beginner': {
                'name': 'Getting Started',
                'description': 'Complete your first breathing exercise',
                'requirement': 1,
                'icon': '🌱'
            },
            'intermediate': {
                'name': 'Regular Breather',
                'description': 'Complete 50 breathing exercises',
                'requirement': 50,
                'icon': '🌿'
            },
            'advanced': {
                'name': 'Breathing Master',
                'description': 'Complete 100 breathing exercises',
                'requirement': 100,
                'icon': '🌳'
            },
            'streak_3': {
                'name': 'Consistent',
                'description': 'Maintain a 3-day streak',
                'requirement': 3,
                'icon': '🔥'
            },
            'streak_7': {
                'name': 'Weekly Warrior',
                'description': 'Maintain a 7-day streak',
                'requirement': 7,
                'icon': '🏆'
            },
            'streak_30': {
                'name': 'Monthly Master',
                'description': 'Maintain a 30-day streak',
                'requirement': 30,
                'icon': '👑'
            }
        }

        self.update_achievements()

    def update_achievements(self):
        # Clear existing achievements display
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Load user stats
        try:
            with open(get_app_data_path('breathing_stats.json'), 'r') as f:
                stats = json.load(f)
        except FileNotFoundError:
            stats = {}

        # Calculate total cycles and current streak
        total_cycles = sum(stats.values())
        current_streak = self.calculate_streak(stats)

        # Load unlocked achievements
        try:
            with open(get_app_data_path('achievements.json'), 'r') as f:
                unlocked = json.load(f)
        except FileNotFoundError:
            unlocked = {}

        # Check and display each achievement
        for i, (achievement_id, achievement) in enumerate(self.achievements.items()):
            # Create frame for each achievement
            achievement_frame = ctk.CTkFrame(self.scrollable_frame)
            achievement_frame.pack(fill="x", padx=10, pady=5)

            # Icon and name
            icon_label = ctk.CTkLabel(
                achievement_frame,
                text=achievement['icon'],
                font=("Arial", 24)
            )
            icon_label.pack(side="left", padx=10)

            # Achievement details
            details_frame = ctk.CTkFrame(achievement_frame)
            details_frame.pack(side="left", fill="x", expand=True, padx=10)

            name_label = ctk.CTkLabel(
                details_frame,
                text=achievement['name'],
                font=("Arial", 16, "bold")
            )
            name_label.pack(anchor="w")

            desc_label = ctk.CTkLabel(
                details_frame,
                text=achievement['description'],
                font=("Arial", 12)
            )
            desc_label.pack(anchor="w")

            # Check if achievement is unlocked
            is_unlocked = False
            if 'streak' in achievement_id:
                requirement = achievement['requirement']
                is_unlocked = current_streak >= requirement
            else:
                is_unlocked = total_cycles >= achievement['requirement']

            # Status indicator
            status_label = ctk.CTkLabel(
                achievement_frame,
                text="✅" if is_unlocked else "🔒",
                font=("Arial", 24)
            )
            status_label.pack(side="right", padx=10)

            # Update unlocked achievements
            if is_unlocked and achievement_id not in unlocked:
                unlocked[achievement_id] = {
                    'unlocked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                # Save updated achievements
                with open(get_app_data_path('achievements.json'), 'w') as f:
                    json.dump(unlocked, f)

    def calculate_streak(self, stats):
        streak = 0
        sorted_dates = sorted(stats.keys())
        for i in range(len(sorted_dates) - 1):
            if (datetime.strptime(sorted_dates[i + 1], '%Y-%m-%d') - 
                datetime.strptime(sorted_dates[i], '%Y-%m-%d')).days == 1:
                streak += 1
            else:
                break
        return streak + 1 if sorted_dates else 0

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

if __name__ == "__main__":
    app = App()
    app.mainloop() 