from gi.repository import Gtk
from pydispatch import dispatcher

class SignalEnabledToolButton(Gtk.ToolButton):
    '''
        SignalEnabledToolButton is a special version of ToolButton which
        accepts pydispatcher signals to enables/disables it. This is useful for
        buttons which may not always be able to be clickable, such as undo and
        redo when their respective stacks are empty, or save when there are no
        changes in the document.
        
        disableSignal: The signal which, when recieved, disables the button,
                       which prevents it from being clicked.
        enableSignal:  The signal which, when recieved, enables the button,
                       which allows it to be clicked.
    '''
    def __init__(self, disableSignal, enableSignal, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dispatcher.connect(self.onDisable, signal=disableSignal, sender=dispatcher.Any)
        dispatcher.connect(self.onEnable, signal=enableSignal, sender=dispatcher.Any)
    
    def onDisable(self):
        self.set_sensitive(False)
    
    def onEnable(self):
        self.set_sensitive(True)

class SignalToggledToolButton(Gtk.ToggleToolButton):
    '''
        SignalToggledToolButton is a special version of ToggleToolButton which
        accepts pydispatcher signals to activate/deactivate it. In addition,
        it will send signals whenever the user toggles the button. This is
        useful for formatting buttons like Bold, Italic, and Underline.
        
        activateSignal:    The signal which, when recieved, will activate the
                           button.
        deactivateSignal:  The signal which, when recieved, will deactivate the
                           button.
        activeSignal:      The signal which is sent when the user activates the
                           button.
        inactiveSignal:    The signal which is sent when the user deactivates
                           the button.
    '''
    def __init__(self, tag_name, activateSignal, deactivateSignal, activeSignal, inactiveSignal, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dispatcher.connect(self.onDeactivate, signal=deactivateSignal, sender=dispatcher.Any)
        dispatcher.connect(self.onActivate, signal=activateSignal, sender=dispatcher.Any)
        self.activeSignal = activeSignal
        self.inactiveSignal = inactiveSignal
        self.tag_name = tag_name
        self.connect_after('clicked', self.onClicked)
    
    def onDeactivate(self):
        self.set_active(False)
    
    def onActivate(self):
        self.set_active(True)

    def onClicked(self, widget):
        if self.get_active():
            self.onActive()
        else:
            self.onInactive()

    def onActive(self):
        dispatcher.send(signal=self.activeSignal, sender=self, tag_name=self.tag_name)

    def onInactive(self):
        dispatcher.send(signal=self.inactiveSignal, sender=self, tag_name=self.tag_name)
