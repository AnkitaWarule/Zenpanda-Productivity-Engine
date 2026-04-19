import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import cv2
import os
import winsound
import threading
import time

class ZenPandaPro:
    def __init__(self):
        # --- 1. CONFIGURATION LAYER ---
        self.settings = {
            "res": (180, 180),
            "win_pos": "200x200+100+100",
            "bg": "#abcdef",
            "sense_rate": 5,  # Process AI every 5 frames
            "dark_limit": 35
        }

        self.root = tk.Tk()
        self._init_window()
        
        # --- 2. STATE MANAGEMENT ---
        self.is_active = True
        self.has_greeted = False
        self.current_state = "panda_normal.gif"
        self.frames = []
        self.frame_idx = 0
        self.tick_counter = 0 

        # --- 3. HARDWARE LAYER ---
        # Using CAP_DSHOW on Windows prevents the long camera-init delay
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.face_engine = cv2.CascadeClassifier("face_brain.xml")
        
        self._load_assets(self.current_state)
        self._build_ui()
        
        # Start Engine
        self.update_loop()
        self.root.mainloop()

    def _init_window(self):
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", self.settings["bg"])
        self.root.config(bg=self.settings["bg"])
        self.root.geometry(self.settings["win_pos"])

    def _build_ui(self):
        self.canvas = tk.Label(self.root, bg=self.settings["bg"])
        self.canvas.pack(expand=True)

        self.exit_btn = tk.Label(self.root, text="✕", bg="#ff4d4d", fg="white", 
                                font=("Arial", 9, "bold"), width=3, cursor="hand2")
        self.exit_btn.place(x=150, y=10)
        self.exit_btn.place_forget()

        # Modern Bindings
        self.canvas.bind("<Enter>", lambda e: self.exit_btn.place(x=150, y=10))
        self.canvas.bind("<Leave>", self._hide_exit_delayed)
        self.canvas.bind("<Button-1>", self._start_move)
        self.canvas.bind("<B1-Motion>", self._on_move)
        self.exit_btn.bind("<Button-1>", lambda e: self.terminate())

    def _load_assets(self, filename):
        """Memory-efficient asset loading."""
        if not os.path.exists(filename): return
        
        img = Image.open(filename)
        # Clear existing frames to prevent memory bloat
        self.frames = [ImageTk.PhotoImage(f.copy().convert("RGBA").resize(self.settings["res"])) 
                       for f in ImageSequence.Iterator(img)]
        self.frame_idx = 0

    def _async_sound(self, file):
        """Senior fix: Audio must never touch the UI thread's timing."""
        if os.path.exists(file):
            threading.Thread(target=winsound.PlaySound, args=(file, winsound.SND_FILENAME), daemon=True).start()

    def _run_vibration(self, count=0):
        if count < 10 and self.is_active:
            x, y = self.root.winfo_x(), self.root.winfo_y()
            offset = 4 if count % 2 == 0 else -4
            self.root.geometry(f"+{x + offset}+{y}")
            self.root.after(25, lambda: self._run_vibration(count + 1))

    def update_loop(self):
        if not self.is_active: return

        # --- AI & VISION LOGIC (THROTTLED) ---
        self.tick_counter += 1
        if self.tick_counter % self.settings["sense_rate"] == 0:
            self._process_vision()

        # --- ANIMATION RENDERING (FULL SPEED) ---
        if self.frames:
            self.frame_idx = (self.frame_idx + 1) % len(self.frames)
            self.canvas.config(image=self.frames[self.frame_idx])

        self.root.after(50, self.update_loop)

    def _process_vision(self):
        success, frame = self.cap.read()
        if not success: return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = gray.mean()
        
        # Priority 1: Environment (Sleep)
        if brightness < self.settings["dark_limit"]:
            new_state = "panda_sleep.gif"
            self.has_greeted = False
        
        # Priority 2: Presence (Smile)
        else:
            faces = self.face_engine.detectMultiScale(gray, 1.3, 5)
            if len(faces) > 0:
                new_state = "panda_smile.gif"
                if not self.has_greeted:
                    self._async_sound("hello_sound.wav")
                    self._run_vibration()
                    self.has_greeted = True
            else:
                new_state = "panda_normal.gif"
                # Logic choice: do we reset greeting when user leaves?
                # self.has_greeted = False 

        if new_state != self.current_state:
            self.current_state = new_state
            self._load_assets(new_state)

    # Window Management
    def _start_move(self, event):
        self.offset_x, self.offset_y = event.x, event.y

    def _on_move(self, event):
        x = self.root.winfo_x() + (event.x - self.offset_x)
        y = self.root.winfo_y() + (event.y - self.offset_y)
        self.root.geometry(f"+{x}+{y}")

    def _hide_exit_delayed(self, event):
        self.root.after(1000, self._finalize_hide)

    def _finalize_hide(self):
        x, y = self.root.winfo_pointerxy()
        wx, wy = self.root.winfo_rootx(), self.root.winfo_rooty()
        if not (wx <= x <= wx+200 and wy <= y <= wy+200):
            self.exit_btn.place_forget()

    def terminate(self):
        self.is_active = False
        self._async_sound("click_sound.wav")
        self.cap.release()
        self.root.destroy()

if __name__ == "__main__":
    ZenPandaPro()