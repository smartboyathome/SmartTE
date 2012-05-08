from SmartTE.Widgets.UndoableTextBuffer import TextBuffer
from SmartTE.Signals import ToolbarSignals, FormatSignals, FormatTags, TextViewSignals
from SmartTE.CustomCollections import OneToOneDict
from pydispatch import dispatcher
from gi.repository import Pango, Gtk

class FormattableTextBuffer(TextBuffer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tagsToSignals = OneToOneDict()
        self.toggleTagSet = set()
        self.dropdownTagSet = set()
        self.initializeDefaultTags()
        self.connectFormattingSignals()

    def initializeDefaultTags(self):
        self.generateTag(FormatTags.BOLD, ('weight', Pango.Weight.BOLD))
        self.setupToggleTag(FormatTags.BOLD, FormatSignals.BOLD_ACTIVATE, FormatSignals.BOLD_DEACTIVATE)
        self.generateTag(FormatTags.ITALIC, ('style', Pango.Style.ITALIC))
        self.setupToggleTag(FormatTags.ITALIC, FormatSignals.ITALIC_ACTIVATE, FormatSignals.ITALIC_DEACTIVATE)
        self.generateTag(FormatTags.UNDERLINE, ('underline', Pango.Underline.SINGLE))
        self.setupToggleTag(FormatTags.UNDERLINE, FormatSignals.UNDERLINE_ACTIVATE, FormatSignals.UNDERLINE_DEACTIVATE)
        self.generateTag(FormatTags.ERROR, ('underline', Pango.Underline.ERROR))
        self.generateTag(FormatTags.IGNORE)
        self.setupDropdownTag('font', FormatSignals.FONT_CHANGE)
        self.setupDropdownTag('size', FormatSignals.SIZE_CHANGE)

    def generateTag(self, tag_name, *args):
        tag = Gtk.TextTag.new(tag_name)
        for arg_set in args:
            tag.set_property(*arg_set)
        self.get_tag_table().add(tag)

    def setupToggleTag(self, tag_name, activateSignal, deactivateSignal):
        self.toggleTagSet.add(tag_name)
        self.tagsToSignals[tag_name] = {'activate':activateSignal, 'deactivate':deactivateSignal}

    def setupDropdownTag(self, tag_name, change_signal):
        self.dropdownTagSet.add(tag_name)
        self.tagsToSignals[tag_name] = {'changed':change_signal}

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

    def onFamilyChange(self, sender, font_name):
        tag_name = 'font:{}'.format(font_name)
        if self.get_tag_table().lookup(tag_name) is None:
            self.generateTag(tag_name, ('family', font_name))
        self.activateTag(tag_name)

    def onSizeChange(self, size):
        tag_name = 'size:{}pt'.format(size)
        if self.get_tag_table().lookup(tag_name) is None:
            self.generateTag(tag_name, ('size-points', int(size)))
        self.activateTag(tag_name)

    def onCursorMoved(self):
        if not self.get_has_selection():
            cursorIter = self.get_iter_at_mark(self.get_insert())
            cursorTags = cursorIter.get_tags()
            activeTagNames = set([tag.get_property('name') for tag in cursorTags])
            for tag_name in self.toggleTagSet.intersection(activeTagNames):
                self.sendTagActive(tag_name)
            dropdown_tags = {}
            for tag_name in self.toggleTagSet.difference(activeTagNames):
                split_tag = tag_name.split(':')
                if split_tag[0] in self.dropdownTagSet:
                    dropdown_tags[split_tag[0]] = split_tag[1:]
                else:
                    self.sendTagInactive(tag_name)
            activeDropdownTags = set(dropdown_tags.keys())
            for tag_name in self.dropdownTagSet.intersection(activeDropdownTags):
                self.sendTagChanged(tag_name, dropdown_tags[tag_name])
            for tag_name in self.dropdownTagSet.difference(activeDropdownTags):
                self.sendTagChanged(tag_name, '')

    def sendTagActive(self, tag_name):
        dispatcher.send(signal=self.tagsToSignals[tag_name]['activate'], sender=self)

    def sendTagInactive(self, tag_name):
        dispatcher.send(signal=self.tagsToSignals[tag_name]['deactivate'], sender=self)

    def sendTagChanged(self, tag_name, new_value):
        dispatcher.send(signal=self.tagsToSignals[tag_name]['changed'], sender=self, new_value=new_value)
