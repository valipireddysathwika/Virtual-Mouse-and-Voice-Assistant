import cv2
import numpy as np
import pyautogui
import time
import speech_recognition as sr
import threading
import math
from pynput.mouse import Button, Controller

# Initialize mouse controller
mouse = Controller()

# Constants for thumb tracking
THUMB_TIP_ID = 4  # MediaPipe thumb tip landmark
INDEX_TIP_ID = 8  # MediaPipe index finger tip landmark
ACTIVATION_DISTANCE = 50  # pixels distance to activate mouse movement
CLICK_DISTANCE = 30  # pixels distance to register a click

# Voice command flags
voice_control_active = False
last_voice_command_time = 0

# Initialize hand tracking
try:
    import mediapipe as mp
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    )
    mp_drawing = mp.solutions.drawing_utils
    hand_tracking_available = True
except ImportError:
    print("MediaPipe not available. Thumb tracking will be disabled.")
    hand_tracking_available = False

def process_voice_commands():
    global voice_control_active, last_voice_command_time
    
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
    
    while True:
        try:
            with microphone as source:
                print("Listening for voice commands...")
                audio = recognizer.listen(source, timeout=3, phrase_time_limit=3)
            
            try:
                command = recognizer.recognize_google(audio).lower()
                print("You said:", command)
                
                if "mouse" in command and ("start" in command or "begin" in command):
                    voice_control_active = True
                    print("Voice control activated")
                    last_voice_command_time = time.time()
                elif "mouse" in command and ("stop" in command or "end" in command):
                    voice_control_active = False
                    print("Voice control deactivated")
                    last_voice_command_time = time.time()
                elif voice_control_active:
                    last_voice_command_time = time.time()
                    if "click" in command:
                        mouse.click(Button.left)
                        print("Left click executed")
                    elif "right click" in command:
                        mouse.click(Button.right)
                        print("Right click executed")
                    elif "double click" in command:
                        mouse.click(Button.left, 2)
                        print("Double click executed")
                    elif "scroll up" in command:
                        mouse.scroll(0, 2)
                        print("Scrolled up")
                    elif "scroll down" in command:
                        mouse.scroll(0, -2)
                        print("Scrolled down")
                    elif "drag" in command:
                        pyautogui.mouseDown()
                        print("Drag started")
                    elif "release" in command:
                        pyautogui.mouseUp()
                        print("Drag released")
                    elif "move" in command:
                        # This will be handled by the thumb tracking
                        pass
            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
                
        except Exception as e:
            print(f"Voice command error: {e}")

def calculate_distance(point1, point2):
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def main():
    global voice_control_active, last_voice_command_time
    
    # Start voice command thread
    voice_thread = threading.Thread(target=process_voice_commands, daemon=True)
    voice_thread.start()
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return
    
    # Get screen size
    screen_width, screen_height = pyautogui.size()
    
    # Variables for smoothing mouse movement
    prev_x, prev_y = 0, 0
    smoothing_factor = 0.5
    
    # Variables for click detection
    click_threshold = 0.9
    click_counter = 0
    
    print("Virtual Mouse Control Started")
    print("Voice Commands:")
    print("- 'Start mouse' / 'Begin mouse': Enable voice control")
    print("- 'Stop mouse' / 'End mouse': Disable voice control")
    print("- 'Click': Left click")
    print("- 'Right click': Right click")
    print("- 'Double click': Double click")
    print("- 'Scroll up/down': Scroll")
    print("- 'Drag' / 'Release': Drag and drop")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break
        
        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        frame_height, frame_width, _ = frame.shape
        
        # Process hand tracking if available
        if hand_tracking_available:
            # Convert to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw hand landmarks
                    mp_drawing.draw_landmarks(
                        frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    
                    # Get thumb and index finger positions
                    thumb_tip = hand_landmarks.landmark[THUMB_TIP_ID]
                    index_tip = hand_landmarks.landmark[INDEX_TIP_ID]
                    
                    # Convert to pixel coordinates
                    thumb_x = int(thumb_tip.x * frame_width)
                    thumb_y = int(thumb_tip.y * frame_height)
                    index_x = int(index_tip.x * frame_width)
                    index_y = int(index_tip.y * frame_height)
                    
                    # Draw circles at thumb and index finger tips
                    cv2.circle(frame, (thumb_x, thumb_y), 10, (0, 255, 0), -1)
                    cv2.circle(frame, (index_x, index_y), 10, (0, 0, 255), -1)
                    
                    # Calculate distance between thumb and index finger
                    distance = calculate_distance((thumb_x, thumb_y), (index_x, index_y))
                    
                    # If distance is small, it's a click gesture
                    if distance < CLICK_DISTANCE:
                        click_counter += 1
                        if click_counter > 5:  # Require gesture to be held for a few frames
                            cv2.putText(frame, "Click Gesture", (50, 50), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                            if click_counter == 6:  # Only click once per gesture
                                mouse.click(Button.left)
                                print("Left click by thumb gesture")
                    else:
                        click_counter = 0
                    
                    # If distance is in activation range, move mouse
                    if ACTIVATION_DISTANCE < distance < 300:
                        # Map hand position to screen coordinates
                        screen_x = np.interp(thumb_x, (0, frame_width), (0, screen_width))
                        screen_y = np.interp(thumb_y, (0, frame_height), (0, screen_height))
                        
                        # Smooth mouse movement
                        smooth_x = prev_x + (screen_x - prev_x) * smoothing_factor
                        smooth_y = prev_y + (screen_y - prev_y) * smoothing_factor
                        
                        # Move mouse
                        mouse.position = (smooth_x, smooth_y)
                        prev_x, prev_y = smooth_x, smooth_y
                        
                        cv2.putText(frame, "Moving Mouse", (50, 100), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        
        # Display voice control status
        status_text = "Voice Control: " + ("ON" if voice_control_active else "OFF")
        cv2.putText(frame, status_text, (50, frame_height - 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Auto-disable voice control after 30 seconds of inactivity
        if voice_control_active and (time.time() - last_voice_command_time > 30):
            voice_control_active = False
            print("Voice control auto-disabled due to inactivity")
        
        # Show the frame
        cv2.imshow('Virtual Mouse Control', frame)
        
        # Exit on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()
    if hand_tracking_available:
        hands.close()

if __name__ == "__main__":
    # Disable PyAutoGUI fail-safe
    pyautogui.FAILSAFE = False
    
    # Start the application
    main()