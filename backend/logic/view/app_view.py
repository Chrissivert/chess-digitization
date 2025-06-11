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

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("resources/themes/custom_colours.json")

def load_theme_from_file(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

class App(ctk.CTk):
  """ Main application class for the ChessCamera control panel. """
  def __init__(self, reset_board_function=None, reset_all_boards_function=None):
    super().__init__()
    self.title("ChessCamera | Control Panel")
    self.geometry("800x500")
    self.minsize(600, 400)
    
    self.number_of_cameras = 0
    self.boards = None
    self.board_service = None
    self.progress_window = None
    
    self.reset_board_command = reset_board_function
    self.reset_all_boards_command = reset_all_boards_function
    
    container = ctk.CTkFrame(self, fg_color="transparent")
    container.pack(expand=True)
    
    ctk.CTkLabel(container, text="Control Panel", font=("Segoe UI", 28, "bold")).pack(pady=(10, 10))
    vcmd = self.register(self.validate_entry)

    self.number_of_cameras_entry = ctk.CTkEntry(
        container,
        width=300,
        height=40,
        font=("Segoe UI", 14),
        fg_color=("#ffffff","#333333"),
        border_width=0
    )
    self.number_of_cameras_entry.insert(0, "Number of Cameras")
    self.number_of_cameras_entry.pack(pady=(5, 15))
    
    self.error_label = ctk.CTkLabel(
      container,
      text="",
      text_color="red",
      font=("Segoe UI", 12)
    )
    self.error_label.pack(pady=(0, 10))

    def on_focus_in(event):
        if event.widget.get() == "Number of Cameras":
            event.widget.delete(0, "end")

    def on_focus_out(event):
        if not event.widget.get():
            event.widget.insert(0, "Number of Cameras")

    self.number_of_cameras_entry.bind("<FocusIn>", on_focus_in)
    self.number_of_cameras_entry.bind("<FocusOut>", on_focus_out)

    
    self.apply_button = ctk.CTkButton(
      container,
      text="Apply Camera Count",
      width=200,
      height=45,
      font=("Segoe UI", 14),
      command=self.apply_number_of_cameras
    )
    self.apply_button.pack(pady=(5, 20))
    self.apply_button.focus_set()
    
    button_frame = ctk.CTkFrame(container, fg_color="transparent")
    button_frame.pack(pady=10)
    
    self.reset_select_button = ctk.CTkButton(
      button_frame,
      text="Select Which Board to Reset",
      width=200,
      height=45,
      font=("Segoe UI", 14),
      state="disabled",
      command=self.open_board_reset_window
    )
    self.reset_select_button.pack(side="left", padx=(0, 20))
    
    self.reset_button = ctk.CTkButton(
      button_frame,
      text="Reset All Boards",
      width=200,
      height=45,
      font=("Segoe UI", 14),
      state="disabled",
      command=lambda: self.reset_all_boards()
    )
    self.reset_button.pack(side="left")
    
    self.start_button = ctk.CTkButton(
      container,
      text="Start Tournament",
      width=200,
      height=45,
      font=("Segoe UI", 14),
      state="disabled",
      command=self.start_tournament
    )
    self.start_button.pack(pady=(10, 10))
    
    self.bind('<Return>', lambda e: self.apply_number_of_cameras())
    
  def reset_all_boards(self) -> None:
    self.highlight_entry_label("All boards reset succesfully.", CtkTypeEnum.WARNING)
    asyncio.run_coroutine_threadsafe(self._async_reset_all_boards(), state.event_loop)
    
  async def _async_reset_all_boards(self) -> None:
    try:
      await self.reset_all_boards_command()
    except Exception as e:
      import traceback
      print(f"Error resetting all boards: {e}")
      traceback.print_exc()
    
  def validate_entry(self, value:any) -> bool:
    """ Validate the entry to only allow digits and empty string. """
    return value.isdigit() or value == ""
  
  def highlight_status_and_entry(self, msg: str, type: CtkTypeEnum=CtkTypeEnum.ERROR) -> None:
    self.number_of_cameras_entry.configure(border_color=type.value["color"], border_width=2)
    self.highlight_entry_label(msg, type)
  
  def highlight_entry_label(self, msg: str, type: CtkTypeEnum=CtkTypeEnum.ERROR) -> None:
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
        self.boards = board_factory.create_boards(self.number_of_cameras)
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
