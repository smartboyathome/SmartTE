from pydispatch import dispatcher
from gi.repository import Pango, Gtk
from SmartTE.Signals import TextViewSignals

class FormattableTextView(Gtk.TextView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connect_after('move-cursor', self.onMoveCursor)
        self.connect('button-release-event', self.onMoveCursor)

    def onMoveCursor(self, widget=None, event=None, count=None, extend_selection=None):
        dispatcher.send(signal=TextViewSignals.CURSOR_MOVED, sender=self)
