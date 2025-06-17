import customtkinter as ctk
import json
import asyncio
from logic.view.ctk_type_enum import CtkTypeEnum
from logic.api.entity.camera import CameraDoesNotExistError
import logic.api.services.board_storage as storage
from logic.api.services.board_service import BoardService
from logic.api.entity.board_factory import BoardFactory
import logic.view.state as state
from logic.view.progress_bar_view import ProgressBarTopLevel
from logic.view.reset_specific_board_view import BoardResetSelectorTopLevel
import chess
import chess.svg
from PIL import Image, ImageTk
import io
import cairosvg  # to convert svg to png
import concurrent.futures
executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("resources/themes/custom_colours.json")

def load_theme_from_file(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

class App(ctk.CTk):
    def __init__(self, reset_board_function=None, reset_all_boards_function=None):
        super().__init__()
        self.title("ChessCamera | Control Panel")
        self.geometry("1000x600")
        self.minsize(600, 400)

        self.reset_board_command = reset_board_function
        self.reset_all_boards_command = reset_all_boards_function

        # Main container holds two frames side by side
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # Configure grid in container for resizing behavior
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)

        # LEFT FRAME - for FEN input, board, update button
        self.left_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Configure left_frame grid for dynamic resizing
        self.left_frame.grid_columnconfigure(0, weight=1)
        self.left_frame.grid_rowconfigure(0, weight=1)  # for board canvas
        self.left_frame.grid_rowconfigure(1, weight=0)  # fen label
        self.left_frame.grid_rowconfigure(2, weight=0)  # fen entry
        self.left_frame.grid_rowconfigure(3, weight=0)  # update button

        # RIGHT FRAME - for camera controls
        self.right_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # Configure right_frame grid for dynamic resizing
        self.right_frame.grid_columnconfigure(0, weight=1)
        # Optional: Add row weights if needed, e.g. for scrollable or flexible content

        ### Left Frame Widgets ###

        # Board Canvas
        self.board_canvas = ctk.CTkCanvas(self.left_frame, bg="white", highlightthickness=0, width=700, height=400)
        self.board_canvas.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        # FEN Label
        self.fen_label = ctk.CTkLabel(self.left_frame, text="Paste FEN", font=("Segoe UI", 14))
        self.fen_label.grid(row=1, column=0, pady=(0, 5))

        # FEN Entry
        self.fen_entry = ctk.CTkEntry(self.left_frame, font=("Segoe UI", 14))
        self.fen_entry.insert(0, chess.STARTING_FEN)
        self.fen_entry.grid(row=2, column=0, pady=(0, 10), sticky="ew")

        # Update Button
        self.update_fen_button = ctk.CTkButton(
            self.left_frame,
            text="Update Board from FEN",
            command=self.update_board_from_fen,
            font=("Segoe UI", 16),
            height = 40
        )
        self.update_fen_button.grid(row=3, column=0, pady=(0, 10))

        # Display the initial board
        self.display_board(chess.STARTING_FEN)

        ### Right Frame Widgets ###

        ctk.CTkLabel(self.right_frame, text="Control Panel", font=("Segoe UI", 28, "bold")).pack(pady=(0, 10))

        self.number_of_cameras_entry = ctk.CTkEntry(
            self.right_frame,
            font=("Segoe UI", 16),
            fg_color=("#ffffff","#333333"),
            border_width=0,
            height=40
        )
        self.number_of_cameras_entry.insert(0, "Number of Cameras")
        self.number_of_cameras_entry.pack(fill="x", pady=(5, 15), padx=20)

        self.error_label = ctk.CTkLabel(
            self.right_frame,
            text="",
            text_color="red",
            font=("Segoe UI", 12)
        )
        self.error_label.pack(pady=(0, 10), padx=20)

        def on_focus_in(event):
            if event.widget.get() == "Number of Cameras":
                event.widget.delete(0, "end")

        def on_focus_out(event):
            if not event.widget.get():
                event.widget.insert(0, "Number of Cameras")

        self.number_of_cameras_entry.bind("<FocusIn>", on_focus_in)
        self.number_of_cameras_entry.bind("<FocusOut>", on_focus_out)

        self.apply_button = ctk.CTkButton(
            self.right_frame,
            text="Apply Camera Count",
            font=("Segoe UI", 18),
            command=self.apply_number_of_cameras,
            height=75
        )
        self.apply_button.pack(pady=(5, 20), padx=20, fill="x")
        self.apply_button.focus_set()

        button_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        button_frame.pack(pady=10, padx=20, fill="x")

        self.reset_select_button = ctk.CTkButton(
            button_frame,
            text="Select Which Board to Reset",
            font=("Segoe UI", 18),
            state="disabled",
            command=self.open_board_reset_window,
            height=75
        )
        self.reset_select_button.pack(side="left", padx=(0, 20), expand=True, fill="x")

        self.reset_button = ctk.CTkButton(
            button_frame,
            text="Reset All Boards",
            font=("Segoe UI", 18),
            state="disabled",
            command=lambda: self.reset_all_boards(),
            height=75
        )
        self.reset_button.pack(side="left", expand=True, fill="x")

        self.start_button = ctk.CTkButton(
            self.right_frame,
            text="Start Tournament",
            font=("Segoe UI", 18),
            state="disabled",
            height=100,
            command=self.start_tournament
        )
        self.start_button.pack(pady=(10, 10), padx=20, fill="x")

        self.bind('<Return>', lambda e: self.apply_number_of_cameras())

        # Bind configure event to dynamically resize chessboard
        self.board_canvas.bind("<Configure>", self._on_board_canvas_resize)
        self.current_board_image = None  # Keep track of current board image for resize

    def _on_board_canvas_resize(self, event):
        if hasattr(self, '_resize_after_id'):
            self.after_cancel(self._resize_after_id)
        self._resize_after_id = self.after(100, self.resize_and_show_board)

    def generate_board_image_async(self, fen):
        board = chess.Board(fen)
        svg_data = chess.svg.board(board=board, size=400)
        png_data = cairosvg.svg2png(bytestring=svg_data)
        return Image.open(io.BytesIO(png_data))

    def display_board(self, fen):
        self.current_fen = fen
        # Generate new board image async only when fen changes
        future = executor.submit(self.generate_board_image_async, fen)

        def on_done(future):
            try:
                image = future.result()
                self.base_board_image = image
                self.resize_and_show_board()  # Display resized image immediately
            except Exception as e:
                print("Error generating board image:", e)

        future.add_done_callback(lambda f: self.after(0, on_done, f))

    def resize_and_show_board(self):
        if self.base_board_image is None:
            return
        width = self.board_canvas.winfo_width()
        height = self.board_canvas.winfo_height()
        if width <= 0 or height <= 0:
            return

        resized_image = self.base_board_image.resize((width, height), Image.Resampling.LANCZOS)
        self.board_img = ImageTk.PhotoImage(resized_image)

        self.board_canvas.delete("all")
        self.board_canvas.create_image(0, 0, anchor="nw", image=self.board_img)

    def update_board_from_fen(self):
        fen = self.fen_entry.get().strip()
        try:
            self.display_board(fen)
            self.highlight_entry_label("Board updated.", CtkTypeEnum.WARNING)
        except Exception as e:
            self.highlight_status_and_entry("Invalid FEN string.", CtkTypeEnum.ERROR)
            print(f"Invalid FEN: {e}")

     

    def reset_all_boards(self) -> None:
        self.highlight_entry_label("All boards reset successfully.", CtkTypeEnum.WARNING)
        asyncio.run_coroutine_threadsafe(self._async_reset_all_boards(), state.event_loop)

    async def _async_reset_all_boards(self) -> None:
        try:
            await self.reset_all_boards_command()
        except Exception as e:
            import traceback
            print(f"Error resetting all boards: {e}")
            traceback.print_exc()

    def validate_entry(self, value: any) -> bool:
        """ Validate the entry to only allow digits and empty string. """
        return value.isdigit() or value == ""

    def highlight_status_and_entry(self, msg: str, type: CtkTypeEnum = CtkTypeEnum.ERROR) -> None:
        self.number_of_cameras_entry.configure(border_color=type.value["color"], border_width=2)
        self.highlight_entry_label(msg, type)

    def highlight_entry_label(self, msg: str, type: CtkTypeEnum = CtkTypeEnum.ERROR) -> None:
        self.error_label.configure(text=msg, text_color=type.value["color"])
        self.after(3000, self.clear_entry_label)

    def clear_entry_label(self) -> None:
        self.number_of_cameras_entry.configure(border_color="", border_width=0)
        self.error_label.configure(text="")

    def apply_number_of_cameras(self) -> None:
        """ Apply the number of cameras and start the connection. """
        number = self.number_of_cameras_entry.get().strip()

        if number.isdigit() and int(number) > 0:
            self.clear_entry_label()

            try:
                self.number_of_cameras = int(number)
                board_factory = BoardFactory()
                self.boards = board_factory.create_boards(self.number_of_cameras, self.fen_entry.get().strip())
                self.board_service = BoardService()
                storage.boards = self.boards

            except CameraDoesNotExistError as e:
                self.highlight_status_and_entry(f"Error: {e}", CtkTypeEnum.ERROR)
                self.number_of_cameras = 0
                return

            self.disable_main_buttons()
            self.progress_window = ProgressBarTopLevel(self, self.number_of_cameras, self.on_connection_finished)
        else:
            self.highlight_status_and_entry("Please enter a valid number of cameras.", CtkTypeEnum.ERROR)
            self.number_of_cameras = 0

    def start_tournament(self) -> None:
        """ Start the tournament if cameras are connected. """
        if self.number_of_cameras > 0 and self.board_service:
            self.reset_select_button.configure(state="normal")
            self.reset_button.configure(state="normal")
            self.board_service.start_detectors()
            self.start_button.configure(state="normal")

    def disable_main_buttons(self) -> None:
        """ Disable main buttons during connection. """
        self.apply_button.configure(state="disabled")
        self.start_button.configure(state="disabled")
        self.reset_select_button.configure(state="disabled")
        self.reset_button.configure(state="disabled")
        self.number_of_cameras_entry.configure(state="disabled")

    def enable_main_buttons(self) -> None:
        """ Enable main buttons after connection. """
        self.apply_button.configure(state="normal")
        self.start_button.configure(state="normal")
        self.number_of_cameras_entry.configure(state="normal")

    def enable_all_buttons(self) -> None:
        """ Enable all buttons. """
        self.apply_button.configure(state="normal")
        self.start_button.configure(state="normal")
        self.reset_select_button.configure(state="normal")
        self.reset_button.configure(state="normal")
        self.number_of_cameras_entry.configure(state="normal")

    def on_connection_finished(self) -> None:
        """ Callback when the connection is finished. """
        self.highlight_status_and_entry("Connection finished.", CtkTypeEnum.OK)
        self.enable_main_buttons()

    def open_board_reset_window(self) -> None:
        """ Open the board reset selector window. """
        if self.number_of_cameras > 0:
            self.disable_main_buttons()
            BoardResetSelectorTopLevel(self, self.number_of_cameras, self.enable_all_buttons, func=self.reset_board_command)
        else:
            self.highlight_entry_label("No cameras connected.", CtkTypeEnum.ERROR)
