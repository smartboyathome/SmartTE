from SmartTE.Widgets.UndoableTextBuffer import TextBuffer
from SmartTE.Signals import ToolbarSignals, FormatSignals
from pydispatch import dispatcher
from gi.repository import Pango, Gtk

class FormattableTextBuffer(TextBuffer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initializeDefaultTags()
        self.connectFormattingSignals()

    def initializeDefaultTags(self):
        self.generateTag('bold', property_args=[('weight', Pango.Weight.BOLD)])
        self.generateTag('italic', property_args=[('style', Pango.Style.ITALIC)])
        self.generateTag('underline', property_args=[('underline', Pango.Underline.SINGLE)])
        self.generateTag('error', property_args=[('underline', Pango.Underline.ERROR)])
        self.generateTag('ignore')

    def generateTag(self, name, property_args=[]):
        tag = Gtk.TextTag.new(name)
        for arg_set in property_args:
            tag.set_property(*arg_set)
        self.get_tag_table().add(tag)

    def connectFormattingSignals(self):
        dispatcher.connect(self.onBoldActive, signal=ToolbarSignals.BOLD_ACTIVE, sender=dispatcher.Any)
        dispatcher.connect(self.onBoldInactive, signal=ToolbarSignals.BOLD_INACTIVE, sender=dispatcher.Any)
        dispatcher.connect(self.onItalicActive, signal=ToolbarSignals.ITALIC_ACTIVE, sender=dispatcher.Any)
        dispatcher.connect(self.onItalicInactive, signal=ToolbarSignals.ITALIC_INACTIVE, sender=dispatcher.Any)
        dispatcher.connect(self.onUnderlineActive, signal=ToolbarSignals.UNDERLINE_ACTIVE, sender=dispatcher.Any)
        dispatcher.connect(self.onUnderlineInactive, signal=ToolbarSignals.UNDERLINE_INACTIVE, sender=dispatcher.Any)
        dispatcher.connect(self.onFamilyChange, signal=ToolbarSignals.FAMILY_CHANGE, sender=dispatcher.Any)
        dispatcher.connect(self.onSizeChange, signal=ToolbarSignals.SIZE_CHANGE, sender=dispatcher.Any)

    def activateTag(self, name):
        if self.get_has_selection():
            bounds = self.get_selection_bounds()
            self.apply_tag_by_name(name, bounds[0], bounds[1])

    def deactivateTag(self, name):
        if self.get_has_selection():
            bounds = self.get_selection_bounds()
            self.remove_tag_by_name(name, bounds[0], bounds[1])

    def onBoldActive(self):
        self.activateTag('bold')

    def onBoldInactive(self):
        self.deactivateTag('bold')

    def onItalicActive(self):
        self.activateTag('italic')

    def onItalicInactive(self):
        self.deactivateTag('italic')

    def onUnderlineActive(self):
        self.activateTag('underline')

    def onUnderlineInactive(self):
        self.deactivateTag('underline')

    def onFamilyChange(self):
        pass

    def onSizeChange(self):
        pass
