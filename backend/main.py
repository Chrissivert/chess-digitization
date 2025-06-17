import asyncio
import threading
import logic.view.state as state
from fastapi import FastAPI
from logic.api.routes import admin_routes, video_routes, websocket_routes
from logic.api.routes.admin_routes import reset_board, reset_all_boards
from logic.api.entity.ml_simulator import fake_ml_moves, simulate_multiple_fake_ml_moves
from logic.view.app_view import App
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(video_routes.router)
app.include_router(websocket_routes.router)
app.include_router(admin_routes.router)

def start_gui():
  """ Start the GUI in a separate thread. """
  window = App(reset_board_function=reset_board, reset_all_boards_function=reset_all_boards)
  window.mainloop()

@app.on_event("startup")
async def main():
  """ Main function to start the FastAPI server and GUI. """
  # asyncio.create_task(simulate_multiple_fake_ml_moves())
  state.event_loop = asyncio.get_event_loop()
  gui_thread = threading.Thread(target=start_gui, daemon=True)
  gui_thread.start()
  
