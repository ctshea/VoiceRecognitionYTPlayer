from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

import speech_recognition as sr
import pyttsx3
import threading
import queue

#TODO remove this later as input will be voice
import keyboard

#This class is to run pyttsx3 RunAndWait method without slowing down process in main thread
class TTSBackground:
    def __init__(self):
        self.queue = queue.Queue()
        self.running = True
        self.thread = threading.Thread(target=self._process_queue, daemon=True)
        self.thread.start()

    def _process_queue(self):
        try:
            while self.running:
                #print("Running")  # Debugging line: Should continuously print
                try:
                    phrase = self.queue.get(timeout=1)  # Wait for input
                    if phrase is None:  # Stop condition
                        break
                    # Have to create new engine each time to avoid inconsistencies with mulithreaded pyttsx3
                    engine = pyttsx3.init()
                    voices = engine.getProperty('voices')
                    engine.setProperty('voice', voices[1].id)
                    engine.setProperty('volume', 0.3)

                    engine.say(phrase)
                    engine.runAndWait()

                    del engine  # Cleanup to free resources

                except queue.Empty:
                    time.sleep(0.1)  # Prevent CPU overuse
        except Exception as e:
            print(f"⚠️ TTS Thread Error: {e}")  # Print any unexpected errors
        finally:
            print("❌ TTS Thread Exiting!")

    def speak(self, phrase):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._process_queue, daemon=True)
            self.thread.start()
        self.queue.put(phrase)

    def shutdown(self):
        self.running = False
        self.queue.put(None)  # Send termination signal
        self.thread.join()  # Wait for thread to finish

# class TTSBackground:
#     def __init__(self):
#         self.engine = pyttsx3.init()
#         voices = self.engine.getProperty('voices')
#         self.engine.setProperty('voice', voices[1].id)
#         self.engine.setProperty('volume', 0.3)  # Set volume to 30%
#         self.queue = queue.Queue()
#         # self.thread = threading.Thread(target=self._process_queue, daemon=True)
#         self.thread = threading.Thread(target=self.test, daemon=True)
#         self.running = True
#         self.thread.start()
#
#     def test(self):
#         while self.running:
#             print("RUNNING")
#             if self.queue.empty():
#                 time.sleep(0.1)
#             else:
#                 phrase = self.queue.get(timeout=1)
#                 self.engine.say(phrase)
#                 self.engine.runAndWait()
#                 self.engine.stop()
#                 continue
#
#     def _process_queue(self):
#         print("IN PROCESS QUEUE")
#         print(self.running)
#         while self.running:
#             try:
#                 print("AYO")
#                 print(self.queue)
#                 phrase = self.queue.get(timeout=1)  # Wait for input (with a timeout to allow graceful exit)
#                 if phrase is None:
#                     print("BREAKING THREAD LOOP")
#                     break
#                 self.engine.say(phrase)
#                 self.engine.runAndWait()  # Ensure the speech is fully processed
#                 #self.engine.stop()  # Clear out any residual events
#             except queue.Empty:
#                 continue  # If no phrases in queue, continue looping
#
#
#
#     def speak(self, phrase):
#         self.queue.put(phrase)  # Add phrase to queue
#         # self.engine.say(phrase)
#         # self.engine.runAndWait()  # Ensure the speech is fully processed
#         # self.engine.stop()  # Clear out any residual events
#
#     def stop(self):
#         self.queue.put(None)  # Stop signal
#         self.thread.join()

def hide_unwanted_content(driver):
    # JavaScript to hide YouTube Shorts, Playlists, and Sponsored content
    print("Hiding content")
    script = """
    // JavaScript to hide YouTube Shorts
    var shorts = document.querySelectorAll('ytd-reel-shelf-renderer.style-scope.ytd-item-section-renderer');
    shorts.forEach(function(item) {
        item.style.display = 'none';  // Hide the Shorts shelf
    });
    
    // Hide sponsored content using the specific class and id
    var sponsored = document.querySelectorAll('div#main-container.style-scope.ytd-promoted-video-renderer');
    sponsored.forEach(function(item) {
        item.style.display = 'none';  // Hide sponsored content
    });

    // Hide Playlists
    //var playlists = document.querySelectorAll('ytd-playlist-renderer');
    //playlists.forEach(function(item) {
    //    item.style.display = 'none';
    //});

    // Hide Sponsored content (based on typical attributes like 'ad')
    //var sponsored = document.querySelectorAll('[class*="ad"]');
    //sponsored.forEach(function(item) {
    //    item.style.display = 'none';
    //});

    // You can also target other specific elements like comments, recommendations, etc.
    """
    driver.execute_script(script)


#def get_user_input(engine, recognizer, source):
def get_user_input(recognizer, source):
        while True:
            try:
                print("here in user input")
                audio = recognizer.listen(source, phrase_time_limit=7)
                print(recognizer.recognize_google(audio))
                return recognizer.recognize_google(audio)
            except sr.UnknownValueError:
                # engine.say("Unknown command, please try again")
                # engine.runAndWait()
                pass
            except sr.RequestError:
                # engine.say("Error with the system")
                # engine.runAndWait()
                break

#TODO next -> fix search function to work for just search or full sentence, call search function with query
# def listen_for_command(driver, engine, recognizer, tts):
def listen_for_command(driver, recognizer, tts):
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        # tts_async(engine, "Enter command")
        # tts_async(tts_queue, "Enter command")
        tts.speak("Enter command")
        # tts.speak("Test")
        while True:
            try:
                print("here in listen command")
                keyboard.add_hotkey('t', lambda: hide_unwanted_content(driver))
                print("Press 't' to hide unwanted content...")
                audio = recognizer.listen(source, phrase_time_limit=7)
                text = recognizer.recognize_google(audio)
                print(text)
                request = text.split()

                if "search" in request: #search function
                    #search_youtube(driver, engine, request, recognizer, source)
                    search_youtube(driver, request, recognizer, source, tts)
                elif "play" in request: #select video function
                    select_video(driver)
            except sr.UnknownValueError:
                # engine.say("Unknown command, please try again")
                # engine.runAndWait()
                pass
            except sr.RequestError:
                # engine.say("Error with the system")
                # engine.runAndWait()
                break

#TODO add volume up/down, fullscreen/exit, rewind/forward via voice

# def scroll_down(driver):
#


#TODO add skip adds via voice
def skip_adds(driver):
    button = driver.find_element(By.CLASS_NAME, "ytp-skip-ad-button")
    button.click()


#TODO select via voice
def select_video(driver):
    # Select the second video (or modify as needed)
    video = driver.find_element(By.XPATH, '(//a[@id="video-title"])[2]')
    video.click()  # Click on the second video

    # Wait for the video to load
    time.sleep(3)


#TODO search via voice
#def search_youtube(driver, engine, query, recognizer, source):
def search_youtube(driver, query, recognizer, source, tts):
    video_choices = []
    # Find the search bar and input the search query
    search_box = driver.find_element(By.NAME, "search_query")
    if len(query) > 1: #searching for user input
        query = " ".join(query[1:])
    else:                  #user just said search, prompt user for search input
        tts.speak("What do you want to search")
        print("should have said what do you want to search")
        query = get_user_input(recognizer, source)
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)  # Press Enter

    # Wait for search results to load
    time.sleep(3)

    #hide shorts, sponsored content, and playlists
    hide_unwanted_content(driver)

    #create and send array of videos to select_video function
    videos = driver.find_elements(By.XPATH, '//a[@id="video-title"]')
    for i, video in enumerate(videos[:10], start=1):
        title = video.get_attribute("title")
        video_choices.append((i, title, video))

    for i in video_choices:
        index, title, video = i
        print(f"Index: {index}, Title: {title}")
    # print(len(video_choices))




def setup_driver():
    # Set up options for Chrome (removed --headless to make the window visible)
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Comment this out or remove it
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration (optional)
    chrome_options.add_argument("--no-sandbox")  # Disable sandboxing (optional)

    # Set the path to chromedriver manually
    chromedriver_path = './chromedriver.exe'  # Ensure this is the correct relative path

    # Check if the chromedriver file exists at the specified path
    if not os.path.exists(chromedriver_path):
        raise ValueError(f"The chromedriver at path '{chromedriver_path}' does not exist. Please check the path.")

    # Create a Service object with the path to chromedriver
    service = Service(chromedriver_path)

    # Initialize the webdriver with the service and options
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Open YouTube
    driver.get("https://www.youtube.com")

    # #initialize and return array of videos
    # videos = driver.find_elements(By.XPATH,'//a[@id="video-title"]')
    # video_choices = []
    # for i, video in enumerate(videos[:10], start=1):
    #     title = video.get_attribute("title")
    #     video_choices.append(i, title, video)

    return driver

def main():
    #setup driver and open youtube. Setup main array of videos for case that user selects without searching
    driver = setup_driver()

    #setup TTS engine and speech recognition
    tts = TTSBackground()
    recognizer = sr.Recognizer()

    #set up initial 10 videos into array


    #listen for user command
    listen_for_command(driver, recognizer, tts)


    #select_video(driver)


    # Listen for spacebar press in the background
    keyboard.add_hotkey("space", lambda: skip_adds(driver))
    # Keep the program running
    keyboard.wait("esc")  # Keeps the program alive until you press "Esc"

    # Wait for the video to play for a bit (optional)
    time.sleep(10)

# Run the main function
if __name__ == "__main__":
    main()
