from gi.repository import Gtk

class UndoableTextBuffer(Gtk.TextBuffer):
    def __init__(self):
        super().__init__()
        
