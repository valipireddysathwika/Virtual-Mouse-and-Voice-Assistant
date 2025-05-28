import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
import pyautogui
import speech_recognition as sr
import threading
import math
from pynput.mouse import Button, Controller
import platform
import time
import mediapipe as mp
from PIL import Image, ImageTk

class VirtualMouseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gesture & Voice Controlled Mouse")
        self.root.geometry("600x400")
        
        # System check
        self.os_name = platform.system()
        
        # Control variables
        self.hand_control_active = False
        self.voice_control_active = False
        self.running = True
        self.last_voice_time = 0
        
        # Camera window variables
        self.camera_window = None
        self.show_camera = False
        
        # Initialize controllers
        self.mouse = Controller()
        self.recognizer = sr.Recognizer()
        
        # MediaPipe setup
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Constants
        self.THUMB_TIP_ID = 4
        self.INDEX_TIP_ID = 8
        self.MIDDLE_TIP_ID = 12
        self.RING_TIP_ID = 16
        self.PINKY_TIP_ID = 20
        self.ACTIVATION_DISTANCE = 50
        self.CLICK_DISTANCE = 30
        self.VOICE_MOVE_SPEED = 100
        
        # Create UI
        self.create_ui()
        
        # Start threads
        self.camera_thread = threading.Thread(target=self.camera_loop, daemon=True)
        self.camera_thread.start()
        
        self.voice_thread = threading.Thread(target=self.voice_loop, daemon=True)
        self.voice_thread.start()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="Gesture & Voice Controlled Mouse", 
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Control buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        # Hand control button
        self.hand_btn = ttk.Button(
            btn_frame,
            text="Enable Hand Control",
            command=self.toggle_hand_control,
            width=20
        )
        self.hand_btn.pack(side=tk.LEFT, padx=10)
        
        # Voice control button
        self.voice_btn = ttk.Button(
            btn_frame,
            text="Enable Voice Control",
            command=self.toggle_voice_control,
            width=20
        )
        self.voice_btn.pack(side=tk.LEFT, padx=10)
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(pady=20)
        
        # Hand control status
        self.hand_status = ttk.Label(
            status_frame,
            text="Hand Control: OFF",
            font=("Helvetica", 12)
        )
        self.hand_status.pack(pady=5)
        
        # Voice control status
        self.voice_status = ttk.Label(
            status_frame,
            text="Voice Control: OFF",
            font=("Helvetica", 12)
        )
        self.voice_status.pack(pady=5)
        
        # Instructions
        instr_frame = ttk.LabelFrame(main_frame, text="Instructions", padding=10)
        instr_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        instructions = """
        Hand Control:
        - Show your hand to camera
        - Thumb moves cursor
        - Pinch (thumb to index) to click
        
        Voice Commands:
        - "click", "right click", "double click"
        - "scroll up", "scroll down"
        - "drag", "release"
        - "start voice", "stop voice"
        - "move up/down/left/right"
        """
        instr_label = ttk.Label(instr_frame, text=instructions, justify=tk.LEFT)
        instr_label.pack()
    
    def create_camera_window(self):
        """Create a separate window for camera feed with tracking tips"""
        if self.camera_window is None or not self.camera_window.winfo_exists():
            self.camera_window = tk.Toplevel(self.root)
            self.camera_window.title("Hand Tracking View")
            self.camera_window.geometry("640x580")
            
            # Camera frame
            self.camera_frame = ttk.Frame(self.camera_window)
            self.camera_frame.pack(fill=tk.BOTH, expand=True)
            
            # Camera label
            self.camera_label = ttk.Label(self.camera_frame)
            self.camera_label.pack()
            
            # Tips frame
            tips_frame = ttk.LabelFrame(self.camera_window, text="Hand Tracking Tips", padding=10)
            tips_frame.pack(fill=tk.X, padx=10, pady=10)
            
            tips = """
            1. Keep your hand in the frame with fingers spread
            2. Move your thumb to control cursor position
            3. Bring thumb and index finger close to click
            4. Keep background simple for better tracking
            5. Ensure good lighting conditions
            """
            tips_label = ttk.Label(tips_frame, text=tips, justify=tk.LEFT)
            tips_label.pack()
            
            # Close button
            close_btn = ttk.Button(
                self.camera_window,
                text="Close Camera",
                command=self.close_camera_window
            )
            close_btn.pack(pady=10)
            
            self.camera_window.protocol("WM_DELETE_WINDOW", self.close_camera_window)
    
    def close_camera_window(self):
        """Close the camera window and disable hand control"""
        if self.hand_control_active:
            self.toggle_hand_control()
        if self.camera_window:
            self.camera_window.destroy()
            self.camera_window = None
    
    def toggle_hand_control(self):
        self.hand_control_active = not self.hand_control_active
        status = "ON" if self.hand_control_active else "OFF"
        self.hand_status.config(text=f"Hand Control: {status}")
        self.hand_btn.config(
            text="Disable Hand Control" if self.hand_control_active else "Enable Hand Control"
        )
        
        if self.hand_control_active:
            self.create_camera_window()
            if self.voice_control_active:
                self.voice_control_active = False
                self.voice_status.config(text="Voice Control: OFF")
                self.voice_btn.config(text="Enable Voice Control")
        else:
            if self.camera_window:
                self.camera_window.destroy()
                self.camera_window = None
    
    def toggle_voice_control(self):
        self.voice_control_active = not self.voice_control_active
        status = "ON" if self.voice_control_active else "OFF"
        self.voice_status.config(text=f"Voice Control: {status}")
        self.voice_btn.config(
            text="Disable Voice Control" if self.voice_control_active else "Enable Voice Control"
        )
        
        if self.voice_control_active and self.hand_control_active:
            self.hand_control_active = False
            self.hand_status.config(text="Hand Control: OFF")
            self.hand_btn.config(text="Enable Hand Control")
            if self.camera_window:
                self.camera_window.destroy()
                self.camera_window = None
    
    def camera_loop(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Error", "Could not open camera")
            return
        
        screen_width, screen_height = pyautogui.size()
        prev_x, prev_y = 0, 0
        smoothing_factor = 0.5
        click_counter = 0
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue
            
            frame = cv2.flip(frame, 1)
            frame_height, frame_width, _ = frame.shape
            
            if self.hand_control_active:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(rgb_frame)
                
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        # Draw hand landmarks and connections
                        self.mp_drawing.draw_landmarks(
                            frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                        
                        # Get finger positions
                        thumb_tip = hand_landmarks.landmark[self.THUMB_TIP_ID]
                        index_tip = hand_landmarks.landmark[self.INDEX_TIP_ID]
                        middle_tip = hand_landmarks.landmark[self.MIDDLE_TIP_ID]
                        ring_tip = hand_landmarks.landmark[self.RING_TIP_ID]
                        pinky_tip = hand_landmarks.landmark[self.PINKY_TIP_ID]
                        
                        # Convert to pixel coordinates
                        thumb_x = int(thumb_tip.x * frame_width)
                        thumb_y = int(thumb_tip.y * frame_height)
                        index_x = int(index_tip.x * frame_width)
                        index_y = int(index_tip.y * frame_height)
                        middle_x = int(middle_tip.x * frame_width)
                        middle_y = int(middle_tip.y * frame_height)
                        ring_x = int(ring_tip.x * frame_width)
                        ring_y = int(ring_tip.y * frame_height)
                        pinky_x = int(pinky_tip.x * frame_width)
                        pinky_y = int(pinky_tip.y * frame_height)
                        
                        # Draw colored circles at finger tips
                        cv2.circle(frame, (thumb_x, thumb_y), 10, (0, 255, 0), -1)  # Green - thumb
                        cv2.circle(frame, (index_x, index_y), 10, (0, 0, 255), -1)   # Red - index
                        cv2.circle(frame, (middle_x, middle_y), 8, (255, 0, 0), -1)  # Blue - middle
                        cv2.circle(frame, (ring_x, ring_y), 8, (255, 255, 0), -1)    # Cyan - ring
                        cv2.circle(frame, (pinky_x, pinky_y), 8, (255, 0, 255), -1) # Magenta - pinky
                        
                        # Draw line between thumb and index when close
                        distance = math.sqrt((thumb_x - index_x)**2 + (thumb_y - index_y)**2)
                        if distance < self.CLICK_DISTANCE * 1.5:
                            cv2.line(frame, (thumb_x, thumb_y), (index_x, index_y), (0, 255, 255), 2)
                        
                        # Click detection
                        if distance < self.CLICK_DISTANCE:
                            click_counter += 1
                            if click_counter > 5:
                                cv2.putText(frame, "CLICK", (50, 50), 
                                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                                if click_counter == 6:
                                    self.mouse.click(Button.left)
                        else:
                            click_counter = 0
                        
                        # Cursor movement
                        if self.ACTIVATION_DISTANCE < distance < 300:
                            screen_x = np.interp(thumb_x, (0, frame_width), (0, screen_width))
                            screen_y = np.interp(thumb_y, (0, frame_height), (0, screen_height))
                            
                            smooth_x = prev_x + (screen_x - prev_x) * smoothing_factor
                            smooth_y = prev_y + (screen_y - prev_y) * smoothing_factor
                            
                            self.mouse.position = (smooth_x, smooth_y)
                            prev_x, prev_y = smooth_x, smooth_y
                            
                            cv2.putText(frame, "MOVING", (50, 100), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            
            # Display mode status
            mode_text = "HAND MODE" if self.hand_control_active else "VOICE MODE" if self.voice_control_active else "IDLE"
            cv2.putText(frame, mode_text, (frame_width - 200, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Show in camera window if active
            if self.hand_control_active and self.camera_window:
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = cv2.resize(img, (640, 480))
                img_tk = ImageTk.PhotoImage(image=Image.fromarray(img))
                self.camera_label.config(image=img_tk)
                self.camera_label.image = img_tk
        
        cap.release()
    
    def take_screenshot(self): 
        screenshot = pyautogui.screenshot()
        screenshot.save("screenshot.png")
    def voice_loop(self):
        while self.running:
            if not self.voice_control_active:
                time.sleep(0.1)
                continue
            
            try:
                with sr.Microphone() as source:
                    print("Listening...")
                    audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=3)
                
                try:
                    command = self.recognizer.recognize_google(audio).lower()
                    print("Voice command:", command)
                    self.last_voice_time = time.time()
                    
                    if "start voice" in command or "begin voice" in command:
                        self.voice_control_active = True
                        self.update_ui_status()
                    elif "stop voice" in command or "end voice" in command:
                        self.voice_control_active = False
                        self.update_ui_status()
                    elif self.voice_control_active:
                        if "click" in command:
                            self.mouse.click(Button.left)
                        elif "right click" in command:
                            self.mouse.click(Button.right)
                        elif "double click" in command:
                            self.mouse.click(Button.left, 2)
                        elif "scroll up" in command:
                            self.mouse.scroll(0, 30)
                        elif "scroll down" in command:
                            self.mouse.scroll(0, -30)
                        elif "drag" in command:
                            pyautogui.mouseDown()
                        elif "release" in command:
                            pyautogui.mouseUp()
                        elif "move up" in command:
                            self.move_cursor('up')
                        elif "move down" in command:
                            self.move_cursor('down')
                        elif "move left" in command:
                            self.move_cursor('left')
                        elif "move right" in command:
                            self.move_cursor('right')
                        elif "screenshot" in command:
                            self.take_screenshot()
                        elif "hod" in command:
                            print('Senthil Murugan Sir....')
                
                except sr.UnknownValueError:
                    print("Could not understand audio")
                except sr.RequestError as e:
                    print(f"Could not request results; {e}")
            
            except Exception as e:
                print(f"Voice error: {e}")
    
    def move_cursor(self, direction):
        """Move cursor in specified direction"""
        current_x, current_y = self.mouse.position
        move_map = {
            'up': (0, -self.VOICE_MOVE_SPEED),
            'down': (0, self.VOICE_MOVE_SPEED),
            'left': (-self.VOICE_MOVE_SPEED, 0),
            'right': (self.VOICE_MOVE_SPEED, 0)
        }
        
        dx, dy = move_map[direction]
        new_x = current_x + dx
        new_y = current_y + dy
        
        # Ensure cursor stays on screen
        screen_width, screen_height = pyautogui.size()
        new_x = max(0, min(screen_width, new_x))
        new_y = max(0, min(screen_height, new_y))
        
        self.mouse.position = (new_x, new_y)
    
    def update_ui_status(self):
        """Update the status labels in the UI"""
        hand_status = "ON" if self.hand_control_active else "OFF"
        self.hand_status.config(text=f"Hand Control: {hand_status}")
        
        voice_status = "ON" if self.voice_control_active else "OFF"
        self.voice_status.config(text=f"Voice Control: {voice_status}")
    
    def on_close(self):
        """Clean up when closing the application"""
        self.running = False
        if self.camera_window:
            self.camera_window.destroy()
        self.root.destroy()

if __name__ == "__main__":
    pyautogui.FAILSAFE = False
    root = tk.Tk()
    app = VirtualMouseApp(root)
    root.mainloop()