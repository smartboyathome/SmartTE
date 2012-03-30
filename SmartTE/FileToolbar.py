from gi.repository import Gtk
from SmartTE import Toolbar, ToolbarSignals

class FileToolbar(Toolbar.Toolbar):
    def __init__(self):
        super().__init__('File')
        self.appendButton(Gtk.STOCK_NEW, 'New Document', ToolbarSignals.NEW_FILE, 'Create a new document')
        self.appendButton(Gtk.STOCK_OPEN, 'Open Document', ToolbarSignals.OPEN_FILE, 'Open an existing document')
        self.appendButton(Gtk.STOCK_SAVE, 'Save Document', ToolbarSignals.SAVE_FILE, 'Save the current file to disk')
        self.appendButton(Gtk.STOCK_SAVE_AS, 'Save Document As', ToolbarSignals.SAVE_FILE_AS, 'Save the current document under a new name')
        self.appendButton(Gtk.STOCK_COPY, 'Copy to BBCode', ToolbarSignals.COPY_BBCODE, 'Copy the current selection to BBCode')
        self.appendButton(Gtk.STOCK_UNDO, 'Undo action', ToolbarSignals.UNDO, 'Undo the last action')
        self.appendButton(Gtk.STOCK_REDO, 'Redo action', ToolbarSignals.REDO, 'Redo an undone action')
        self.appendButton(Gtk.STOCK_QUIT, 'Quit SmartTE', ToolbarSignals.QUIT, 'Exit the SmartTE application')

    def appendButton(self, stock, label, callbackSignal, tooltip):
        button = Gtk.ToolButton.new_from_stock(stock)
        button.set_label(label)
        button.connect('clicked', self.widgetCallback, callbackSignal)
        button.set_tooltip_text(tooltip)
        self.appendWidget(button)
