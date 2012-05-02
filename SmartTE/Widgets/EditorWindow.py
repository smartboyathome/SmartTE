from gi.repository import Gtk
from pydispatch import dispatcher
from SmartTE.Signals import EditorWindowSignals, ToolbarSignals

class EditorWindow(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.set_default_size(675, 300)
        self.set_title('SmartTE, Smartboy\'s Text Editor')
        self.connect('delete-event', self.onDelete)
        self.connect('destroy', self.onDestroy)
        dispatcher.connect(self.onDestroy, signal=ToolbarSignals.QUIT, sender=dispatcher.Any)

    def onDelete(self, widget, event, data=None):
        return self.onDestroy(widget)

    def onDestroy(self, widget=None, data=None):
        results = dispatcher.send(signal=EditorWindowSignals.QUIT, sender=self)
        for result in results:
            if not result[1]:
                return False
        Gtk.main_quit()
        return True
