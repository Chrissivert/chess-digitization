# import customtkinter as ctk

# import chess
# import chess.svg
# from PIL import Image, ImageTk
# import io
# import cairosvg  # to convert svg to png


# def update_board_from_fen(self):
#     fen = self.fen_entry.get().strip()
#     try:
#         board = chess.Board(fen)
#         self.display_board(board.fen())
#         self.highlight_entry_label("Board updated.", CtkTypeEnum.WARNING)
#     except Exception as e:
#         self.highlight_status_and_entry("Invalid FEN string.", CtkTypeEnum.ERROR)
#         print(f"Invalid FEN: {e}")

# def display_board(self, fen):
#     """ Render FEN to image and display it on the canvas. """
#     board = chess.Board(fen)
#     svg_data = chess.svg.board(board=board)

#     # Convert SVG to PNG using cairosvg
#     png_data = cairosvg.svg2png(bytestring=svg_data)
#     image = Image.open(io.BytesIO(png_data))
#     image = image.resize((400, 400), Image.ANTIALIAS)
#     self.board_img = ImageTk.PhotoImage(image)

#     self.board_canvas.create_image(0, 0, anchor="nw", image=self.board_img)
