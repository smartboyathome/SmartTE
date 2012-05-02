from gi.repository import Gtk
from pydispatch import dispatcher

class SignalToggledToolButton(Gtk.ToolButton):
    def __init__(self, disableSignal, enableSignal, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dispatcher.connect(self.onDisable, signal=disableSignal, sender=dispatcher.Any)
        dispatcher.connect(self.onEnable, signal=enableSignal, sender=dispatcher.Any)
    
    def onDisable(self):
        self.set_sensitive(False)
    
    def onEnable(self):
        self.set_sensitive(True)
