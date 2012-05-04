from SmartTE.Widgets import UndoableTextBuffer
from SmartTE.Signals import ToolbarSignals, FormatSignals
from pydispatch import dispatcher

class FormattableTextBuffer(UndoableTextBuffer.TextBuffer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dispatcher.connect(self.onBoldActive, signal=ToolbarSignals.BOLD_ACTIVE, sender=dispatcher.Any)
        dispatcher.connect(self.onBoldInactive, signal=ToolbarSignals.BOLD_INACTIVE, sender=dispatcher.Any)
        dispatcher.connect(self.onItalicActive, signal=ToolbarSignals.ITALIC_ACTIVE, sender=dispatcher.Any)
        dispatcher.connect(self.onItalicInactive, signal=ToolbarSignals.ITALIC_INACTIVE, sender=dispatcher.Any)
        dispatcher.connect(self.onUnderlineActive, signal=ToolbarSignals.UNDERLINE_ACTIVE, sender=dispatcher.Any)
        dispatcher.connect(self.onUnderlineInactive, signal=ToolbarSignals.UNDERLINE_INACTIVE, sender=dispatcher.Any)
        dispatcher.connect(self.onFamilyChange, signal=ToolbarSignals.FAMILY_CHANGE, sender=dispatcher.Any)
        dispatcher.connect(self.onSizeChange, signal=ToolbarSignals.SIZE_CHANGE, sender=dispatcher.Any)
    
    def onBoldActive(self):
        pass
    
    def onBoldInactive(self):
        pass

    def onItalicActive(self):
        pass

    def onItalicInactive(self):
        pass

    def onUnderlineActive(self):
        pass

    def onUnderlineInactive(self):
        pass

    def onFamilyChange(self):
        pass

    def onSizeChange(self):
        pass
