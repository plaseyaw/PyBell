import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
from datetime import datetime
import json
import os
import pygame
import pystray
from pystray import Icon, MenuItem, Menu
from PIL import Image
import logging
import queue
import webbrowser


class SoundScheduler:
    def __init__(self, master): 
        self.master = master
        self.master.title("PyBell")
        self.schedules = []
        self.running = True
        self.error_queue = queue.Queue()
        
        # Logger
        self.logger = logging.getLogger("pybell")
        self.logger.setLevel(logging.INFO)
        
        # Create a file handler
        file_handler = logging.FileHandler("pybell.log")
        file_handler.setLevel(logging.INFO)
        
        # Format the log
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add the file handler to the logger
        self.logger.addHandler(file_handler)

        main_frame = ttk.Frame(master, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        time_frame = tk.Frame(main_frame)
        time_frame.grid(row=0, column=0, padx=0, pady=5)
        # Time input (row 0)
        time_label = ttk.Label(main_frame, text="Time (HH:MM:SS):")
        time_label.grid(row=0, column=0, sticky="w")

        self.hour_var = tk.StringVar(value="00")
        self.minute_var = tk.StringVar(value="00")
        self.second_var = tk.StringVar(value="00")

        hour_combo = ttk.Combobox(main_frame, textvariable=self.hour_var, width=2, values=[f"{i:02d}" for i in range(24)], state="readonly")
        hour_combo.grid(row=0, column=1, padx=0, pady=5,sticky="we")
        hour_combo.set(self.hour_var.get())
        
        minute_combo = ttk.Combobox(main_frame, textvariable=self.minute_var, width=2, values=[f"{i:02d}" for i in range(60)], state="readonly")
        minute_combo.grid(row=0, column=2, padx=0, pady=5, sticky="we")
        minute_combo.set(self.minute_var.get())
        
        second_combo = ttk.Combobox(main_frame, textvariable=self.second_var, width=2, values=[f"{i:02d}" for i in range(60)], state="readonly")
        second_combo.grid(row=0, column=3, padx=0, columnspan=3, pady=5, sticky="ew")
        second_combo.set(self.second_var.get())

        # Sound input (row 1)
        sound_label = ttk.Label(main_frame, text="Sound File:")
        sound_label.grid(row=1, column=0, sticky="w")
        self.sound_entry = ttk.Entry(main_frame)
        self.sound_entry.grid(row=1, column=1, columnspan=5, pady=5, sticky="ew")
        self.sound_entry.insert(0, "Path to sound files")
        self.browse_button = ttk.Button(main_frame, text="Browse...", command=self.browse_files)
        self.browse_button.grid(row=1, column=6, padx=5)

        # Days selection
        days_label = ttk.Label(main_frame, text="Days:")
        days_label.grid(row=2, column=0, sticky="nw")
        days_frame = ttk.Frame(main_frame)
        days_frame.grid(row=2, column=1, columnspan=2, sticky="w")
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self.day_vars = [tk.BooleanVar() for _ in self.days]
        for i, day in enumerate(self.days):
            ttk.Checkbutton(days_frame, text=day, variable=self.day_vars[i]).grid(row=0, column=i, sticky="w")

        # Buttons
        self.add_button = ttk.Button(main_frame, text="Add Schedule", command=self.add_schedule)
        self.add_button.grid(row=3, column=0, pady=10, sticky="ew")
        self.save_button = ttk.Button(main_frame, text="Save Schedules", command=self.save_schedules)
        self.save_button.grid(row=3, column=1, pady=10, sticky="ew")

        self.modify_btn = ttk.Button(main_frame, text="Modify Selected", command=self.modify_schedule)
        self.modify_btn.grid(row=4, column=0, pady=5, sticky="ew")
        self.delete_btn = ttk.Button(main_frame, text="Delete Selected", command=self.delete_schedule)
        self.delete_btn.grid(row=4, column=1, pady=5, sticky="ew")
        self.toggle_btn = ttk.Button(main_frame, text="Activate/Deactivate", command=self.toggle_schedule)
        self.toggle_btn.grid(row=4, column=2, pady=5, sticky="ew")

        # Schedule list
        self.schedule_list_frame = tk.Frame(main_frame)
        self.schedule_list_frame.grid(row=5, column=1, columnspan=2, pady=10, sticky="ew")
        self.schedule_list = tk.Listbox(self.schedule_list_frame, width=50, height=8)
        self.schedule_list.pack(side="left", fill="both", expand=True)
        self.schedule_list_scrollbar = ttk.Scrollbar(self.schedule_list_frame, orient="vertical", command=self.schedule_list.yview)
        self.schedule_list_scrollbar.pack(side="right", fill="y")
        self.schedule_list.config(yscrollcommand=self.schedule_list_scrollbar.set)
        
        # Button to open about window
        self.about_window_btn = ttk.Button(main_frame, text="About", command=self.about_window)
        self.about_window_btn.grid(row=10, column=2, pady=10, sticky="e")

        # Button to duplicate schedule
        self.duplicate_schedule_btn = ttk.Button(main_frame, text="Duplicate Schedule", command=self.duplicate_schedule)
        self.duplicate_schedule_btn.grid(row=3, column=2, pady=10, sticky="ew")

        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)

        self.load_schedules()
        self.start_scheduler()
        self.process_error_queue()
        self.master.protocol("WM_DELETE_WINDOW",self.confirmation)

    def browse_files(self):
        file_path = filedialog.askopenfilename(title="Select Sound File", filetypes=[("Audio Files", "*.mp3;*.wav;*.ogg")])
        if file_path:
            self.sound_entry.delete(0, tk.END)
            self.sound_entry.insert(0, file_path)
            
    def add_schedule(self):
        time_str = f"{self.hour_var.get()}:{self.minute_var.get()}:{self.second_var.get()}"
        sound_path = self.sound_entry.get()
        selected_days = [day for i, day in enumerate(self.days) if self.day_vars[i].get()]

        if sound_path and sound_path != "Path to sound files" and any([self.hour_var.get(), self.minute_var.get(), self.second_var.get()]) and selected_days:
            try:
                self.schedules.append({
                    "time": time_str,
                    "sound": sound_path,
                    "days": selected_days,
                    "active": True
                })
                self.refresh_schedule_list()
                # Reset Inputs
                self.hour_var.set("00")
                self.minute_var.set("00")
                self.second_var.set("00")
                self.sound_entry.delete(0, tk.END)
                self.sound_entry.insert(0, "Path to sound files")
                for var in self.day_vars:
                    var.set(False)
            except ValueError as e:
                messagebox.showwarning("Input Error", str(e))
        else:
            messagebox.showwarning("Input Error", "Please enter a valid time, sound path, and select at least one day.")

    def start_scheduler(self):
        threading.Thread(target=self.run_scheduler, daemon=True).start()

    def run_scheduler(self):
        while self.running:
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            current_day = now.strftime("%A")
            for sched in self.schedules:
                if (
                    sched["active"] and
                    sched["time"] == current_time and
                    current_day in sched["days"]
                ):
                    self.play_sound(sched["sound"])
            
            # Calculate sleep time to wake up at the start of the next second
            now = datetime.now()
            sleep_duration = 1.0 - (now.microsecond / 1_000_000.0)
            time.sleep(sleep_duration)

    def save_schedules(self):
        """
        Saves the current schedule to the "Schedule Data.json" file.
        
        If the file does not exist, it will be created.
        If the file does exist, it will be overwritten.
        
        A message box will be shown to indicate success or failure.
        """
        try:
            with open("Schedule Data.json", "w") as file:
                # Use json.dump to save the list of dictionaries
                json.dump(self.schedules, file)
            messagebox.showinfo("Success", "Schedule Saved Successfully")
        except Exception as e:
            # Show an error message if something goes wrong
            messagebox.showerror("Save Error", f"Error Saving Schedule: {e}")

    def load_schedules(self):
        self.schedules = []
        try:
            if os.path.exists("Schedule Data.json"):
                with open("Schedule Data.json", "r") as file:
                    loaded_schedules = json.load(file)
                
                if isinstance(loaded_schedules, list):
                    # Validate each schedule
                    validated_schedules = []
                    for sched in loaded_schedules:
                        if isinstance(sched, dict) and all(k in sched for k in ["time", "sound", "days", "active"]):
                            validated_schedules.append(sched)
                        else:
                            # Optionally warn about a specific invalid entry
                            self.logger.warning(f"Skipping invalid schedule entry: {sched}")
                    self.schedules = validated_schedules
                elif loaded_schedules is not None:
                     messagebox.showwarning("Load Warning", "Schedule data is corrupt or not a list. Starting fresh.")

        except (json.JSONDecodeError, IOError) as e:
            messagebox.showerror("Loading Error", f"Error loading schedule data: {e}")
        
        self.refresh_schedule_list()

    def modify_schedule(self):
        selected = self.schedule_list.curselection()
        if not selected:
            messagebox.showwarning("Select Schedule", "Please select a schedule to modify.")
            return
        idx = selected[0]
        schedule = self.schedules[idx]
        
        #draw a new window for modification
        mod_win = tk.Toplevel(self.master)
        mod_win.title("Modify Schedule")
        mod_win.geometry("600x300")
        
        # Time input
        ttk.Label(mod_win, text="Time:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        hour_var = tk.StringVar(value=schedule["time"].split(":")[0])
        minute_var = tk.StringVar(value=schedule["time"].split(":")[1])
        second_var = tk.StringVar(value=schedule["time"].split(":")[2])
        
        hour_combo = ttk.Combobox(mod_win, textvariable=hour_var, width=3, values=[f"{i:02d}" for i in range(24)], state="readonly")
        hour_combo.grid(row=0, column=1, padx=(0,2), pady=5, sticky="we")
        minute_combo = ttk.Combobox(mod_win, textvariable=minute_var, width=3, values=[f"{i:02d}" for i in range(60)], state="readonly")
        minute_combo.grid(row=0, column=2, padx=(2,2), pady=5, sticky="we")
        second_combo = ttk.Combobox(mod_win, textvariable=second_var, width=3, values=[f"{i:02d}" for i in range(60)], state="readonly")
        second_combo.grid(row=0, column=3, padx=(2,0), pady=5, sticky="ew")
        
        # Sound input
        ttk.Label(mod_win, text="Sound File:").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        sound_entry = ttk.Entry(mod_win, width=40)
        sound_entry.grid(row=1, column=1, columnspan=2, pady=5, padx=10, sticky="ew")
        sound_entry.insert(0, schedule["sound"])
        
        def browse_for_sound():
            path = filedialog.askopenfilename(title="Select Sound File", filetypes=[("Audio Files", "*.mp3;*.wav;*.ogg")])
            if path:
                sound_entry.delete(0, tk.END)
                sound_entry.insert(0, path)

        browse_button = ttk.Button(mod_win, text="Browse...", command=browse_for_sound)
        browse_button.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        # Days selection
        ttk.Label(mod_win, text="Days:").grid(row=2, column=0, sticky="w", padx=10, pady=10)
        days_frame = ttk.Frame(mod_win)
        days_frame.grid(row=2, column=1, columnspan=3, sticky="w")
        day_vars = [tk.BooleanVar(value=day in schedule["days"]) for day in self.days]
        for i, day in enumerate(self.days):
            ttk.Checkbutton(days_frame, text=day, variable=day_vars[i]).grid(row=0, column=i, sticky="w")
        
        def save_modification():
            new_time = f"{hour_var.get()}:{minute_var.get()}:{second_var.get()}"
            new_sound = sound_entry.get()
            new_days = [day for i, day in enumerate(self.days) if day_vars[i].get()]
            if not new_sound or not new_days:
                messagebox.showwarning("Input Error", "Please fill all fields.")
                return
            # Update Schedule
            self.schedules[idx]["time"] = new_time
            self.schedules[idx]["sound"] = new_sound
            self.schedules[idx]["days"] = new_days
            self.refresh_schedule_list()
            mod_win.destroy()
        
        save_btn = ttk.Button(mod_win, text="Save", command=save_modification)
        save_btn.grid(row=3, column=0, columnspan=4, pady=10)
        
        mod_win.columnconfigure(1, weight=1)
        mod_win.columnconfigure(2, weight=1)
        mod_win.columnconfigure(3, weight=1)
        mod_win.columnconfigure(4, weight=1)
        mod_win.columnconfigure(5, weight=1)

    def delete_schedule(self):
        selected = self.schedule_list.curselection()
        if not selected:
            messagebox.showwarning("Select Schedule", "Please select a schedule to delete.")
            return
        idx = selected[0]
        self.schedules.pop(idx)
        self.schedule_list.delete(idx)

    def toggle_schedule(self):
        selected = self.schedule_list.curselection()
        if not selected:
            messagebox.showwarning("Select Schedule", "Please select a schedule to activate/deactivate.")
            return
        idx = selected[0]
        self.schedules[idx]["active"] = not self.schedules[idx]["active"]
        self.refresh_schedule_list()
        self.schedule_list.selection_set(idx)
        self.schedule_list.see(idx)            

    def refresh_schedule_list(self):
        self.schedule_list.delete(0, tk.END)
        for sched in self.schedules:
            status = "Active" if sched["active"] else "Inactive"
            self.schedule_list.insert(
                tk.END,
                f"{sched['time']} - {sched['sound']} on {', '.join(sched['days'])} [{status}]"
            )
            
    def duplicate_schedule(self):
        selected = self.schedule_list.curselection()
        if not selected:
            messagebox.showwarning("Select Schedule", "Please select a schedule to duplicate.")
        else:
            idx = selected[0]
            new_schedule = self.schedules[idx].copy()
            new_schedule["active"] = True
            self.schedules.append(new_schedule)
            self.refresh_schedule_list()
            self.schedule_list.selection_set(idx)
            self.schedule_list.see(idx)

    def show_window(self):
        self.icon.stop()
        self.master.after(0, self.master.deiconify)

    def exit_app(self):
        self.icon.stop()
        self.running = False
        self.master.destroy()
        pygame.quit()
            
    def confirmation(self):
        self.master.withdraw()
        image = Image.open("icon.ico")
        menu = (MenuItem('Show', self.show_window, default=True),
                MenuItem('Exit', self.exit_app))
        self.icon = pystray.Icon("name", image, "PyBell", menu)
        self.icon.run()
            
    def play_sound(self, path):
        def _play():
            try: 
                if not os.path.exists(path):
                    self.logger.error(f"Sound file not found: {path}")
                    self.error_queue.put(f"Sound file not found: {path}")
                    return
                sound = pygame.mixer.Sound(path)
                sound.play()
                self.logger.info(f"Playing sound: {path}")
            except pygame.error as e:
                self.logger.error(f"Error playing sound {path}: {e}")
                self.error_queue.put(f"Could not play sound: {e}")

        playback_thread = threading.Thread(target=_play)
        playback_thread.daemon = True
        playback_thread.start()

    def process_error_queue(self):
        try:
            while True:
                message = self.error_queue.get_nowait()
                messagebox.showerror("Playback Error", message)
        except queue.Empty:
            pass
        self.master.after(100, self.process_error_queue)
        
    def about_window(self):
        mod_win = tk.Toplevel(self.master)
        mod_win.title("About: PyBell")
        mod_win.geometry("400x300")
        
        tk.Label(mod_win, text="version: 1.1", font=("Times New Roman", 12)).pack(pady=10)
        tk.Label(mod_win, text="Author: Zer0point(git: plaseyaw)", font=("Times New Roman", 12)).pack(pady=10)
        tk.Label(mod_win, text="Licence: GPG 3.0", font=("Times New Roman", 12)).pack(pady=10)
        
        tk.Button(mod_win, text="Usage Guide", command=self.manual_window).pack(pady=10)
        tk.Button(mod_win, text="Open Github Repo", command=lambda: webbrowser.open("https://github.com/plaseyaw/PyBell")).pack(padx=5, pady=10)

        
    def manual_window(self):
        mod_win = tk.Toplevel(self.master)
        mod_win.title("User Manual")
        mod_win.geometry("400x200")
        
        Frame = tk.Frame(mod_win)
        Frame.pack(fill="both", expand=True)
        
        text_box = tk.Text(Frame, wrap="word")
        text_box.pack(side="left", fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(Frame, command=text_box.yview)
        scrollbar.pack(side="right", fill="y")
        
        text_box.config(yscrollcommand=scrollbar.set)
        
        if os.path.exists("manual.md"):
            with open("manual.md", "r") as file:
                content = file.read()

        text_box.insert("end", content)
        text_box.config(state="disabled")
        
           
if __name__ == "__main__":
    pygame.init()
    pygame.mixer.init(channels=16)
    root = tk.Tk()
    app = SoundScheduler(root)
    root.mainloop()