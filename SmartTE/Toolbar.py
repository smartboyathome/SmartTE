from gi.repository import Gtk
from pydispatch import dispatcher

class Toolbar(Gtk.Toolbar):
    def __init__(self, label):
        super().__init__()
        self.set_style(Gtk.ToolbarStyle.ICONS)
        self.label = Gtk.Label(label)
        self.buttons = []
        
    def appendWidget(self, widget):
        self.insert(widget, -1)
        self.buttons.append(widget)

    def widgetCallback(self, widget, signal):
        dispatcher.send(signal=signal, sender=widget)
