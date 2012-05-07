from SmartTE.Widgets.UndoableTextBuffer import TextBuffer
from SmartTE.Signals import ToolbarSignals, FormatSignals, FormatTags, TextViewSignals
from SmartTE.CustomCollections import OneToOneDict
from pydispatch import dispatcher
from gi.repository import Pango, Gtk

class FormattableTextBuffer(TextBuffer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initializeDefaultTags()
        self.connectFormattingSignals()

    def initializeDefaultTags(self):
        self.tagsToSignals = OneToOneDict()
        self.tagSet = set()
        self.generateTag(FormatTags.BOLD, property_args=[('weight', Pango.Weight.BOLD)],
            activateSignal=FormatSignals.BOLD_ACTIVATE, deactivateSignal=FormatSignals.BOLD_DEACTIVATE)
        self.generateTag(FormatTags.ITALIC, property_args=[('style', Pango.Style.ITALIC)],
            activateSignal=FormatSignals.ITALIC_ACTIVATE, deactivateSignal=FormatSignals.ITALIC_DEACTIVATE)
        self.generateTag(FormatTags.UNDERLINE, property_args=[('underline', Pango.Underline.SINGLE)],
            activateSignal=FormatSignals.UNDERLINE_ACTIVATE, deactivateSignal=FormatSignals.UNDERLINE_DEACTIVATE)
        self.generateTag(FormatTags.ERROR, property_args=[('underline', Pango.Underline.ERROR)])
        self.generateTag(FormatTags.IGNORE)

    def generateTag(self, tag_name, property_args=[], activateSignal=None, deactivateSignal=None):
        tag = Gtk.TextTag.new(tag_name)
        for arg_set in property_args:
            tag.set_property(*arg_set)
        self.get_tag_table().add(tag)
        if not activateSignal is None and not deactivateSignal is None:
            self.tagSet.add(tag_name)
            self.tagsToSignals[tag_name] = {'activate':activateSignal, 'deactivate':deactivateSignal}

    def connectFormattingSignals(self):
        dispatcher.connect(self.activateTag, signal=ToolbarSignals.FORMATTING_ACTIVE, sender=dispatcher.Any)
        dispatcher.connect(self.deactivateTag, signal=ToolbarSignals.FORMATTING_INACTIVE, sender=dispatcher.Any)
        dispatcher.connect(self.onFamilyChange, signal=ToolbarSignals.FAMILY_CHANGE, sender=dispatcher.Any)
        dispatcher.connect(self.onSizeChange, signal=ToolbarSignals.SIZE_CHANGE, sender=dispatcher.Any)
        dispatcher.connect(self.onCursorMoved, signal=TextViewSignals.CURSOR_MOVED, sender=dispatcher.Any)

    def activateTag(self, tag_name):
        if self.get_has_selection():
            bounds = self.get_selection_bounds()
            self.apply_tag_by_name(tag_name, bounds[0], bounds[1])

    def deactivateTag(self, tag_name):
        if self.get_has_selection():
            bounds = self.get_selection_bounds()
            self.remove_tag_by_name(tag_name, bounds[0], bounds[1])

    def onFamilyChange(self):
        pass

    def onSizeChange(self):
        pass

    def onCursorMoved(self):
        if not self.get_has_selection():
            cursorIter = self.get_iter_at_mark(self.get_insert())
            cursorTags = cursorIter.get_tags()
            activeTagNames = set([tag.get_property('name') for tag in cursorTags])
            for tag_name in activeTagNames:
                self.sendTagActive(tag_name)
            for tag_name in self.tagSet.difference(activeTagNames):
                self.sendTagInactive(tag_name)

    def sendTagActive(self, tag_name):
        dispatcher.send(signal=self.tagsToSignals[tag_name]['activate'], sender=self)

    def sendTagInactive(self, tag_name):
        dispatcher.send(signal=self.tagsToSignals[tag_name]['deactivate'], sender=self)
