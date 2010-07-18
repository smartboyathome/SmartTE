#!/usr/bin/env python
# Thanks a lot to nemo_ on irc.gnome.org for help on this and Kuleshov Alexander for undostack!

import pygtk, gtk, os, re, sys, gobject, imp, pango, undostack
pygtk.require('2.0')
if not os.path.exists(os.path.join(os.path.expanduser('~'), '.smartte', 'Default.conf')):
    os.makedirs(os.path.join(os.path.expanduser('~'), '.smartte'))
    confFile = open(os.path.join(os.path.expanduser('~'), '.smartte', 'Default.conf'), 'wb')
    confFile.write("customTemplate = False\ncustomHeader = None\ncustomFooter = None")
    confFile.close()
imp.load_source('config', os.path.join(os.path.expanduser('~'), '.smartte', 'Default.conf'))
import config


def delete_module(modname, paranoid=None):
    from sys import modules
    try:
        thismod = modules[modname]
    except KeyError:
        raise ValueError(modname)
    these_symbols = dir(thismod)
    if paranoid:
        try:
            paranoid[:]  # sequence support
        except:
            raise ValueError('must supply a finite list for paranoid')
        else:
            these_symbols = paranoid[:]
    del modules[modname]
    for mod in modules.values():
        try:
            delattr(mod, modname)
        except AttributeError:
            pass
        if paranoid:
            for symbol in these_symbols:
                if symbol[:2] == '__':  # ignore special symbols
                    continue
                try:
                    delattr(mod, symbol)
                except AttributeError:
                    pass


class MainWindow(object):
    class BindedTextView(gtk.TextView):
        __gsignals__ = dict(
            keybinding = (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION,
                None,
                (str,))
        )
    gobject.type_register(BindedTextView)
    gtk.binding_entry_add_signal(BindedTextView, gtk.keysyms.C, gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK, 'keybinding', str, 'ctrl+shift+c')
    gtk.binding_entry_add_signal(BindedTextView, gtk.keysyms.X, gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK, 'keybinding', str, 'ctrl+shift+x')
    gtk.binding_entry_add_signal(BindedTextView, gtk.keysyms.V, gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK, 'keybinding', str, 'ctrl+shift+v')


    def keyBindings(self, widget, keyCombo):
        print keyCombo
        if keyCombo == 'ctrl+shift+c':
            self.textConvertFrom(widget)
        elif keyCombo == 'ctrl+shift+x':
            self.textConvertFrom(widget)
            outputStart, outputEnd = self.textBuffer.get_selection_bounds()
            self.textBuffer.delete(outputStart, outputEnd)


    def changeJust(self, widget, data=None):
        if self.justLeftButton.get_active():
            self.textView.set_justification(gtk.JUSTIFY_LEFT)
        elif self.justCenterButton.get_active():
            self.textView.set_justification(gtk.JUSTIFY_CENTER)
        elif self.justRightButton.get_active():
            self.textView.set_justification(gtk.JUSTIFY_RIGHT)
        elif self.justFillButton.get_active():
            self.textView.set_justification(gtk.JUSTIFY_FILL)


    def newFile(self, widget, data=None):
        self.textBuffer.set_text('')
        del self.filename


    def openFile(self, widget, data=None):
        fileSel =  gtk.FileChooserDialog(title='Open File', action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        response = fileSel.run()
        if response == gtk.RESPONSE_OK:
            self.openFileCli(fileSel.get_filename())
            fileSel.destroy()


    def openFileCli(self, filename):
        self.filename = filename
        File = open(self.filename, 'r')
        FileData = File.read()
        File.close()
        self.textConvertFrom(FileData)
        self.textBuffer.set_modified(False)


    def saveAsFile(self, widget, data=None):
        fileSel =  gtk.FileChooserDialog(title='Save File', action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        response = fileSel.run()
        if response == gtk.RESPONSE_OK:
            self.filename = fileSel.get_filename()
            if os.path.exists(self.filename):
                checkDialog = gtk.MessageDialog(fileSel,gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_NONE, 'The file ' + os.path.basename(self.filename) + ' already exists, are you sure you want to overwrite it?')
                checkDialog.add_button(gtk.STOCK_NO, gtk.RESPONSE_NO)
                checkDialog.add_button(gtk.STOCK_YES, gtk.RESPONSE_YES)
                checkResponse = checkDialog.run()
                if checkResponse == gtk.RESPONSE_YES:
                    fileSel.destroy()
                    checkDialog.destroy()
                    File = open(self.filename, 'w')
                    File.write(self.textConvertTo())
                    File.close()
                    self.textBuffer.set_modified(False)
                elif checkResponse == gtk.RESPONSE_NO:
                    fileSel.destroy()
                    checkDialog.destroy()
            else:
                fileSel.destroy()
                outputStart, outputEnd = self.textBuffer.get_bounds()
                File = open(self.filename, 'w')
                File.write(self.textBuffer.get_text(outputStart, outputEnd, True))
                File.close()
                self.textBuffer.set_modified(False)
        elif response == gtk.RESPONSE_CANCEL:
            fileSel.destroy()


    def saveFile(self, widget, data=None):
        try: self.filename
        except AttributeError:
            self.saveAsFile(widget)
        else:
            outputStart, outputEnd = self.textBuffer.get_bounds()
            File = open(self.filename, 'w')
            File.write(self.textConvertTo())
            File.close()
            self.textBuffer.set_modified(False)


    def textConvertTo(self, pos=0):
        def apply_tag(self):
            iter = self.tmpBuffer.get_iter_at_mark(self.beginMark)
            if iter.begins_tag(self.boldTag) and not self.boldLock:
                self.tmpBuffer.insert(iter, '[b]')
                self.boldLock = True
            iter = self.tmpBuffer.get_iter_at_mark(self.beginMark)
            if iter.begins_tag(self.italTag) and not self.italLock:
                self.tmpBuffer.insert(iter, '[i]')
                self.italLock = True
            iter = self.tmpBuffer.get_iter_at_mark(self.beginMark)
            if iter.begins_tag(self.undlTag) and not self.undlLock:
                self.tmpBuffer.insert(iter, '[u]')
                self.undlLock = True
            iter = self.tmpBuffer.get_iter_at_mark(self.endMark)
            if iter.ends_tag(self.boldTag) and self.boldLock:
                self.tmpBuffer.insert(iter, '[/b]')
                self.boldLock = False
            iter = self.tmpBuffer.get_iter_at_mark(self.endMark)
            if iter.ends_tag(self.italTag) and self.italLock:
                self.tmpBuffer.insert(iter, '[/i]')
                self.italLock = False
            iter = self.tmpBuffer.get_iter_at_mark(self.endMark)
            if iter.ends_tag(self.undlTag) and self.undlLock:
                self.tmpBuffer.insert(iter, '[/u]')
                self.undlLock = False
        self.tmpBuffer = gtk.TextBuffer(self.textTags)
        deserialization = self.tmpBuffer.register_deserialize_tagset()
        self.tmpBuffer.deserialize(self.tmpBuffer, deserialization, self.tmpBuffer.get_start_iter(), self.textBuffer.serialize(self.textBuffer, "application/x-gtk-text-buffer-rich-text", self.textBuffer.get_start_iter(), self.textBuffer.get_end_iter()))
        self.boldLock = False
        self.italLock = False
        self.undlLock = False
        self.beginMark = self.tmpBuffer.create_mark(None, self.tmpBuffer.get_start_iter(), False)
        self.endMark = self.tmpBuffer.create_mark(None, self.tmpBuffer.get_start_iter(), True)
        apply_tag(self)
        tmpIter = self.tmpBuffer.get_iter_at_mark(self.beginMark)
        tmpVar = tmpIter.forward_to_tag_toggle(None)
        while tmpVar:
            self.beginMark = self.tmpBuffer.create_mark(None, tmpIter, False)
            self.endMark = self.tmpBuffer.create_mark(None, tmpIter, True)
            apply_tag(self)
            tmpIter = self.tmpBuffer.get_iter_at_mark(self.endMark)
            tmpVar = tmpIter.forward_to_tag_toggle(None)
        text = self.tmpBuffer.get_text(self.tmpBuffer.get_start_iter(), self.tmpBuffer.get_end_iter())
        del(self.beginMark, self.endMark, self.boldLock, self.italLock, self.undlLock, self.tmpBuffer)
        return text


    def textCopyTo(self, event, data=None):
        def apply_tag(self):
            iter = self.tmpBuffer.get_iter_at_mark(self.beginMark)
            if iter.begins_tag(self.boldTag) and not self.boldLock:
                self.tmpBuffer.insert(iter, '[b]')
                self.boldLock = True
            iter = self.tmpBuffer.get_iter_at_mark(self.beginMark)
            if iter.begins_tag(self.italTag) and not self.italLock:
                self.tmpBuffer.insert(iter, '[i]')
                self.italLock = True
            iter = self.tmpBuffer.get_iter_at_mark(self.beginMark)
            if iter.begins_tag(self.undlTag) and not self.undlLock:
                self.tmpBuffer.insert(iter, '[u]')
                self.undlLock = True
            iter = self.tmpBuffer.get_iter_at_mark(self.endMark)
            if iter.ends_tag(self.boldTag) and self.boldLock:
                self.tmpBuffer.insert(iter, '[/b]')
                self.boldLock = False
            iter = self.tmpBuffer.get_iter_at_mark(self.endMark)
            if iter.ends_tag(self.italTag) and self.italLock:
                self.tmpBuffer.insert(iter, '[/i]')
                self.italLock = False
            iter = self.tmpBuffer.get_iter_at_mark(self.endMark)
            if iter.ends_tag(self.undlTag) and self.undlLock:
                self.tmpBuffer.insert(iter, '[/u]')
                self.undlLock = False
        self.tmpBuffer = gtk.TextBuffer(self.textTags)
        selStart, selEnd = self.textBuffer.get_selection_bounds()
        selStart = selStart.get_offset()
        selEnd = selEnd.get_offset()
        deserialization = self.tmpBuffer.register_deserialize_tagset()
        self.tmpBuffer.deserialize(self.tmpBuffer, deserialization, self.tmpBuffer.get_start_iter(), self.textBuffer.serialize(self.textBuffer, "application/x-gtk-text-buffer-rich-text", self.textBuffer.get_start_iter(), self.textBuffer.get_end_iter()))
        selStart = self.tmpBuffer.get_iter_at_offset(selStart)
        selEnd = self.tmpBuffer.create_mark(None, self.tmpBuffer.get_iter_at_offset(selEnd))
        self.tmpBuffer.delete(self.tmpBuffer.get_start_iter(), selStart)
        self.tmpBuffer.delete(self.tmpBuffer.get_iter_at_mark(selEnd), self.tmpBuffer.get_end_iter())
        self.boldLock = False
        self.italLock = False
        self.undlLock = False
        self.beginMark = self.tmpBuffer.create_mark(None, self.tmpBuffer.get_start_iter(), False)
        self.endMark = self.tmpBuffer.create_mark(None, self.tmpBuffer.get_start_iter(), True)
        apply_tag(self)
        tmpIter = self.tmpBuffer.get_iter_at_mark(self.beginMark)
        tmpVar = tmpIter.forward_to_tag_toggle(None)
        while tmpVar:
            self.beginMark = self.tmpBuffer.create_mark(None, tmpIter, False)
            self.endMark = self.tmpBuffer.create_mark(None, tmpIter, True)
            apply_tag(self)
            tmpIter = self.tmpBuffer.get_iter_at_mark(self.endMark)
            tmpVar = tmpIter.forward_to_tag_toggle(None)
        text = self.tmpBuffer.get_text(self.tmpBuffer.get_start_iter(), self.tmpBuffer.get_end_iter())
        del(self.beginMark, self.endMark, self.boldLock, self.italLock, self.undlLock, self.tmpBuffer)
        self.clipboard.set_text(text)


    def textConvertFrom(self, text):
        tmpBuffer = gtk.TextBuffer(self.textTags)
        tmpBuffer.set_text(text)
        boldStarts = []
        boldEnds = []
        italStarts = []
        italEnds = []
        undlStarts = []
        undlEnds = []
        while tmpBuffer.get_text(tmpBuffer.get_start_iter(), tmpBuffer.get_end_iter()).find('[/u]') > -1:
            tmpPos = tmpBuffer.get_text(tmpBuffer.get_start_iter(), tmpBuffer.get_end_iter()).find('[u]')
            undlStarts.append(tmpBuffer.create_mark(None, tmpBuffer.get_iter_at_offset(tmpPos), True))
            tmpBuffer.delete(tmpBuffer.get_iter_at_offset(tmpPos), tmpBuffer.get_iter_at_offset(tmpPos+3))
            tmpPos = tmpBuffer.get_text(tmpBuffer.get_start_iter(), tmpBuffer.get_end_iter()).find('[/u]')
            undlEnds.append(tmpBuffer.create_mark(None, tmpBuffer.get_iter_at_offset(tmpPos), True))
            tmpBuffer.delete(tmpBuffer.get_iter_at_offset(tmpPos), tmpBuffer.get_iter_at_offset(tmpPos+4))
        while tmpBuffer.get_text(tmpBuffer.get_start_iter(), tmpBuffer.get_end_iter()).find('[/i]') > -1:
            tmpPos = tmpBuffer.get_text(tmpBuffer.get_start_iter(), tmpBuffer.get_end_iter()).find('[i]')
            italStarts.append(tmpBuffer.create_mark(None, tmpBuffer.get_iter_at_offset(tmpPos), True))
            tmpBuffer.delete(tmpBuffer.get_iter_at_offset(tmpPos), tmpBuffer.get_iter_at_offset(tmpPos+3))
            tmpPos = tmpBuffer.get_text(tmpBuffer.get_start_iter(), tmpBuffer.get_end_iter()).find('[/i]')
            italEnds.append(tmpBuffer.create_mark(None, tmpBuffer.get_iter_at_offset(tmpPos), True))
            tmpBuffer.delete(tmpBuffer.get_iter_at_offset(tmpPos), tmpBuffer.get_iter_at_offset(tmpPos+4))
        while tmpBuffer.get_text(tmpBuffer.get_start_iter(), tmpBuffer.get_end_iter()).find('[/b]') > -1:
            tmpPos = tmpBuffer.get_text(tmpBuffer.get_start_iter(), tmpBuffer.get_end_iter()).find('[b]')
            boldStarts.append(tmpBuffer.create_mark(None, tmpBuffer.get_iter_at_offset(tmpPos), True))
            tmpBuffer.delete(tmpBuffer.get_iter_at_offset(tmpPos), tmpBuffer.get_iter_at_offset(tmpPos+3))
            tmpPos = tmpBuffer.get_text(tmpBuffer.get_start_iter(), tmpBuffer.get_end_iter()).find('[/b]')
            boldEnds.append(tmpBuffer.create_mark(None, tmpBuffer.get_iter_at_offset(tmpPos), True))
            tmpBuffer.delete(tmpBuffer.get_iter_at_offset(tmpPos), tmpBuffer.get_iter_at_offset(tmpPos+4))
        for start, end in zip(boldStarts, boldEnds):
            tmpBuffer.apply_tag_by_name('bold', tmpBuffer.get_iter_at_mark(start), tmpBuffer.get_iter_at_mark(end))
        for start, end in zip(italStarts, italEnds):
            tmpBuffer.apply_tag_by_name('italic', tmpBuffer.get_iter_at_mark(start), tmpBuffer.get_iter_at_mark(end))
        for start, end in zip(undlStarts, undlEnds):
            tmpBuffer.apply_tag_by_name('underline', tmpBuffer.get_iter_at_mark(start), tmpBuffer.get_iter_at_mark(end))
        self.textBuffer.set_text('')
        deserialization = self.textBuffer.register_deserialize_tagset()
        self.textBuffer.deserialize(self.textBuffer, deserialization, self.textBuffer.get_start_iter(), tmpBuffer.serialize(tmpBuffer, "application/x-gtk-text-buffer-rich-text", tmpBuffer.get_start_iter(), tmpBuffer.get_end_iter()))


    def startPrefs(self, widget, data=None):
        pref_window = prefWindow()
        pref_window.main()


    def hidePane(self, widget, data=None):
        self.toggleText2 = "%s" % ((False, True)[widget.get_active()])
        if self.toggleText2:
            print 'Showing'
            self.textScroll2.show_all()
        else:
            print 'Hiding'
            self.textScroll2.hide_all()


    def undoEntry(self, widget, data=None):
        self.textBuffer.undo()


    def redoEntry(self, widget, data=None):
        self.textBuffer.redo()


    def saveCurPos(self):
        if self.curOldPos != self.curPos:
            self.curOldPos = self.curPos
        self.curPos = self.textBuffer.get_insert()


    def persistAttr(self, widget, iter, text, num):
        self.saveCurPos()
        try: self.boldStart
        except AttributeError:
            pass
        else:
            self.textBuffer.apply_tag_by_name('bold', self.textBuffer.get_iter_at_mark(self.boldStart), self.textBuffer.get_iter_at_mark(self.boldEnd))
        try: self.italStart
        except AttributeError:
            pass
        else:
            self.textBuffer.apply_tag_by_name('italic', self.textBuffer.get_iter_at_mark(self.italStart), self.textBuffer.get_iter_at_mark(self.italEnd))
        try: self.undlStart
        except AttributeError:
            pass
        else:
            self.textBuffer.apply_tag_by_name('underline', self.textBuffer.get_iter_at_mark(self.undlStart), self.textBuffer.get_iter_at_mark(self.undlEnd))


    def boldText(self, widget, data=None):
        if widget.get_active():
            if self.textBuffer.get_selection_bounds() != ():
                start, end = self.textBuffer.get_selection_bounds()
                self.textBuffer.apply_tag_by_name('bold', start, end)
            else:
                self.boldStart = self.textBuffer.create_mark(None, self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()), True)
                self.boldEnd = self.textBuffer.create_mark(None, self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()), False)
        else:
            if self.textBuffer.get_selection_bounds() != ():
                start,end = self.textBuffer.get_selection_bounds()
                self.textBuffer.remove_tag_by_name('bold', start, end)
            else:
                try: self.boldStart
                except AttributeError:
                    pass
                else:
                    del(self.boldStart)
                    del(self.boldEnd)


    def italText(self, widget, data=None):
        if widget.get_active():
            if self.textBuffer.get_selection_bounds() != ():
                start, end = self.textBuffer.get_selection_bounds()
                self.textBuffer.apply_tag_by_name('italic', start, end)
            else:
                self.italStart = self.textBuffer.create_mark(None, self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()), True)
                self.italEnd = self.textBuffer.create_mark(None, self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()), False)
        else:
            if self.textBuffer.get_selection_bounds() != ():
                start,end = self.textBuffer.get_selection_bounds()
                self.textBuffer.remove_tag_by_name('italic', start, end)
            else:
                try: self.italStart
                except AttributeError:
                    pass
                else:
                    del(self.italStart)
                    del(self.italEnd)


    def undlText(self, widget, data=None):
        if widget.get_active():
            if self.textBuffer.get_selection_bounds() != ():
                start, end = self.textBuffer.get_selection_bounds()
                self.textBuffer.apply_tag_by_name('underline', start, end)
            else:
                self.undlStart = self.textBuffer.create_mark(None, self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()), True)
                self.undlEnd = self.textBuffer.create_mark(None, self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()), False)
        else:
            if self.textBuffer.get_selection_bounds() != ():
                start,end = self.textBuffer.get_selection_bounds()
                self.textBuffer.remove_tag_by_name('underline', start, end)
            else:
                try: self.undlStart
                except AttributeError:
                    pass
                else:
                    del(self.undlStart)
                    del(self.undlEnd)


    def dectForm(self, widget, event, *user):
        if self.textBuffer.get_iter_at_offset(self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()).get_offset()-1).has_tag(self.boldTag) and not self.boldButton.get_active():
            self.boldButton.handler_block(self.boldHandId)
            self.boldButton.set_active(True)
            self.boldButton.handler_unblock(self.boldHandId)
        elif self.italButton.get_active() and not self.textBuffer.get_iter_at_offset(self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()).get_offset()-1).has_tag(self.boldTag):
            self.boldButton.handler_block(self.boldHandId)
            self.boldButton.set_active(False)
            self.boldButton.handler_unblock(self.boldHandId)
        if self.textBuffer.get_iter_at_offset(self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()).get_offset()-1).has_tag(self.italTag) and not self.italButton.get_active():
            self.italButton.handler_block(self.italHandId)
            self.italButton.set_active(True)
            self.italButton.handler_unblock(self.italHandId)
        elif self.italButton.get_active() and not self.textBuffer.get_iter_at_offset(self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()).get_offset()-1).has_tag(self.italTag):
            self.italButton.handler_block(self.italHandId)
            self.italButton.set_active(False)
            self.italButton.handler_unblock(self.italHandId)
        if self.textBuffer.get_iter_at_offset(self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()).get_offset()-1).has_tag(self.undlTag) and not self.undlButton.get_active():
            self.undlButton.handler_block(self.undlHandId)
            self.undlButton.set_active(True)
            self.undlButton.handler_unblock(self.undlHandId)
        elif self.undlButton.get_active() and not self.textBuffer.get_iter_at_offset(self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()).get_offset()-1).has_tag(self.undlTag):
            self.undlButton.handler_block(self.undlHandId)
            self.undlButton.set_active(False)
            self.undlButton.handler_unblock(self.undlHandId)


    def __init__(self):
        self.window = gtk.Window()
        self.window.set_border_width(0)
        self.window.set_resizable(True)
        self.window.set_default_size(400, 300)
        self.window.set_title("SmartTE, Smartboy's Text Editor")
        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy)
        self.clipboard = gtk.Clipboard()

        self.textView = self.BindedTextView()
        self.textTags = gtk.TextTagTable()
        self.textBuffer = undostack.TextBuffer(self.textTags)
        self.textView.set_buffer(self.textBuffer)
        self.textView.set_wrap_mode(gtk.WRAP_WORD)
        textScroll = gtk.ScrolledWindow(None, None)
        textScroll.add(self.textView)
        textScroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.textView.connect_after('move-cursor', self.dectForm)
        self.textView.connect('button-release-event', self.dectForm)
        self.textBuffer.connect_after('insert-text', self.persistAttr)

        self.curPos = self.textBuffer.get_insert()
        self.curOldPos = self.curPos

        newButton = gtk.ToolButton(gtk.STOCK_NEW)
        newButton.connect('clicked', self.newFile)
        newButton.set_tooltip_text('Create new file')
        openButton = gtk.ToolButton(gtk.STOCK_OPEN)
        openButton.connect('clicked', self.openFile)
        openButton.set_tooltip_text('Open existing file')
        saveButton = gtk.ToolButton(gtk.STOCK_SAVE)
        saveButton.connect('clicked', self.saveFile)
        saveButton.set_tooltip_text('Save current file')
        saveAsButton = gtk.ToolButton(gtk.STOCK_SAVE_AS)
        saveAsButton.connect('clicked', self.saveAsFile)
        saveAsButton.set_tooltip_text('Save current file under a new name')
        #prefButton = gtk.ToolButton(gtk.STOCK_PREFERENCES)
        #prefButton.connect('clicked', self.startPrefs)
        copyButton = gtk.ToolButton(gtk.STOCK_COPY)
        copyButton.connect('clicked', self.textCopyTo)
        copyButton.set_tooltip_text('Copy to BBCode')
        #paneToggle = gtk.ToggleToolButton(gtk.STOCK_FILE)
        #paneToggle.set_active(True)
        #paneToggle.connect('toggled', self.hidePane)
        undoButton = gtk.ToolButton(gtk.STOCK_UNDO)
        undoButton.connect('clicked', self.undoEntry)
        undoButton.set_tooltip_text('Undo previous action')
        redoButton = gtk.ToolButton(gtk.STOCK_REDO)
        redoButton.connect('clicked', self.redoEntry)
        redoButton.set_tooltip_text('Redo undone action')
        quitButton = gtk.ToolButton(gtk.STOCK_QUIT)
        quitButton.connect('clicked', self.destroy)
        quitButton.set_tooltip_text('Quit SmartTE')
        filebar = gtk.Toolbar()
        filebar.set_style(gtk.TOOLBAR_ICONS)
        filebar.insert(newButton, 0)
        filebar.insert(openButton, 1)
        filebar.insert(saveButton, 2)
        filebar.insert(saveAsButton, 3)
        #filebar.insert(prefButton, 4)
        filebar.insert(copyButton, 4)
        #filebar.insert(paneToggle, 5)
        filebar.insert(undoButton, 5)
        filebar.insert(redoButton, 6)
        filebar.insert(quitButton, 7)
        fileLabel = gtk.Label('File')

        self.boldButton = gtk.ToggleToolButton(gtk.STOCK_BOLD)
        self.boldHandId = self.boldButton.connect('toggled', self.boldText)
        self.boldButton.set_tooltip_text('Bold selected text')
        self.italButton = gtk.ToggleToolButton(gtk.STOCK_ITALIC)
        self.italHandId = self.italButton.connect('toggled', self.italText)
        self.italButton.set_tooltip_text('Italicize selected text')
        self.undlButton = gtk.ToggleToolButton(gtk.STOCK_UNDERLINE)
        self.undlHandId = self.undlButton.connect('toggled', self.undlText)
        self.undlButton.set_tooltip_text('Underline selected text')
        sep1 = gtk.SeparatorToolItem()
        sep1.set_tooltip_text('I\'m just a lonely, little separator. :\'(')
        justLeftButton = gtk.RadioToolButton(None, gtk.STOCK_JUSTIFY_LEFT)
        justLeftButton.connect('toggled', self.changeJust)
        justLeftButton.set_tooltip_text('Justify text to the left')
        justCenterButton = gtk.RadioToolButton(justLeftButton, gtk.STOCK_JUSTIFY_CENTER)
        justCenterButton.connect('toggled', self.changeJust)
        justCenterButton.set_tooltip_text('Justify text to the center')
        justRightButton = gtk.RadioToolButton(justLeftButton, gtk.STOCK_JUSTIFY_RIGHT)
        justRightButton.connect('toggled', self.changeJust)
        justRightButton.set_tooltip_text('Justify text to the right')
        justFillButton = gtk.RadioToolButton(justLeftButton, gtk.STOCK_JUSTIFY_FILL)
        justFillButton.connect('toggled', self.changeJust)
        justFillButton.set_tooltip_text('Justify text so it fills window')
        formbar = gtk.Toolbar()
        formbar.set_style(gtk.TOOLBAR_ICONS)
        formbar.insert(self.boldButton, 0)
        formbar.insert(self.italButton, 1)
        formbar.insert(self.undlButton, 2)
        formbar.insert(sep1, 3)
        formbar.insert(justLeftButton, 4)
        formbar.insert(justCenterButton, 5)
        formbar.insert(justRightButton, 6)
        formbar.insert(justFillButton, 7)
        formLabel = gtk.Label('Format')

        self.boldTag = gtk.TextTag('bold')
        self.boldTag.set_property('weight', pango.WEIGHT_BOLD)
        self.textTags.add(self.boldTag)
        self.italTag = gtk.TextTag('italic')
        self.italTag.set_property('style', pango.STYLE_ITALIC)
        self.textTags.add(self.italTag)
        self.undlTag = gtk.TextTag('underline')
        self.undlTag.set_property('underline', pango.UNDERLINE_SINGLE)
        self.textTags.add(self.undlTag)

        notebook = gtk.Notebook()
        notebook.set_tab_pos(gtk.POS_TOP)
        notebook.append_page(filebar, fileLabel)
        notebook.append_page(formbar, formLabel)

        statusbar = gtk.Statusbar()
        statusbar.set_has_resize_grip(False)
        #self.colorEntry = gtk.Entry()
        #self.colorEntry.set_text('Color')
        #self.colorEntry.set_size_request(100, -1)
        statusHBox = gtk.HBox(False, 0)
        statusHBox.pack_start(statusbar, True)
        #statusHBox.pack_start(self.colorEntry, False)

        vbox = gtk.VBox()
        vbox.pack_start(notebook, False)
        vbox.pack_start(textScroll, True)
        vbox.pack_start(statusHBox, False)

        self.window.add(vbox)
        self.window.show_all()


    def delete_event(self, widget, event, data=None):
        self.destroy(widget)
        return True


    def destroy(self, widget, data=None):
        if self.textBuffer.get_modified():
            checkDialog = gtk.MessageDialog(None,gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_NONE, 'The current file has been modified, would you like to save it?')
            checkDialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            checkDialog.add_button(gtk.STOCK_NO, gtk.RESPONSE_NO)
            checkDialog.add_button(gtk.STOCK_YES, gtk.RESPONSE_YES)
            checkResponse = checkDialog.run()
            if checkResponse == gtk.RESPONSE_CANCEL:
                checkDialog.destroy()
            elif checkResponse == gtk.RESPONSE_YES:
                self.saveFile(widget)
                gtk.main_quit()
            elif checkResponse == gtk.RESPONSE_NO:
                gtk.main_quit()
        else:
            gtk.main_quit()


    def main(self):
        gtk.main()



class prefWindow(object):
    def toggle(self, widget, data=None):
        self.wantTemplate = "%s" % ((False, True)[widget.get_active()])
        #if self.wantTemplate == True:
        #    self.headerView.set_sensitive(True)
        #    self.footerView.set_sensitive(True)
        #else:
        #    self.headerView.set_sensitive(False)
        #    self.footerView.set_sensitive(False)


    def savePrefs(self, widget, data=None):
        confFile = open(os.path.join(os.path.expanduser('~'), '.smartte.conf'), 'wb')
        print self.wantTemplate
        if self.wantTemplate == True:
            confFile.write("customTemplate = " + self.wantTemplate + "\ncustomHeader = '" + self.headerBuffer.get_text() + "'\ncustomFooter = '" + self.footerBuffer.get_text() + "'\nconvLanguage = 'bbcode'")
        else:
            confFile.write("customTemplate = False\ncustomHeader = None\ncustomFooter = None\nconvLanguage = 'bbcode'")
        confFile.close()
        self.prefWindow.destroy()


    def __init__(self):
        self.prefWindow = gtk.Window()
        self.prefWindow.set_border_width(3)
        self.prefWindow.set_resizable(True)
        self.prefWindow.set_default_size(200,150)
        self.prefWindow.set_title("SmartTE Preferences")

        self.toggleTemplate = gtk.CheckButton('Enable Custom Template?')
        self.toggleTemplate.connect('clicked', self.toggle)

        self.headerLabel = gtk.Label('Header:')
        self.headerView = gtk.TextView()
        self.headerBuffer = self.headerView.get_buffer()
        self.headerScroll = gtk.ScrolledWindow(None, None)
        self.headerScroll.add(self.headerView)
        self.headerScroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self.footerLabel = gtk.Label('Footer:')
        self.footerView = gtk.TextView()
        self.footerBuffer = self.footerView.get_buffer()
        self.footerScroll = gtk.ScrolledWindow(None, None)
        self.footerScroll.add(self.footerView)
        self.footerScroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self.okButton = gtk.Button('Ok')
        self.okButton.connect('clicked', self.savePrefs)

        self.cancelButton = gtk.Button('Cancel')
        self.cancelButton.connect('clicked', self.cancel)

        self.buttonHBox = gtk.HBox(False, 0)
        self.buttonHBox.add(self.cancelButton)
        self.buttonHBox.add(self.okButton)
        self.buttonAlign = gtk.Alignment(1, 0, 0, 0)
        self.buttonAlign.add(self.buttonHBox)

        self.table = gtk.Table(2, 2, True)
        self.table.attach(self.headerLabel, 0, 1, 0, 1)
        self.table.attach(self.headerScroll, 1, 2, 0, 1)
        self.table.attach(self.footerLabel, 0, 1, 1, 2)
        self.table.attach(self.footerScroll, 1, 2, 1, 2)

        self.vbox = gtk.VBox(False, 0)
        self.vbox.add(self.toggleTemplate)
        self.vbox.add(self.table)
        self.vbox.add(self.buttonAlign)
        self.prefWindow.add(self.vbox)
        self.prefWindow.show_all()


    def cancel(self, widget, data=None):
        self.prefWindow.destroy()
        gtk.main_quit()

    def delete_event(self, widget, event, data=None):
        return False

    def destroy(self, widget, data=None):
        gtk.main_quit()

    def main(self):
        gtk.main()

if __name__ == '__main__':
    try: sys.argv[1]
    except IndexError:
        startup = MainWindow()
        startup.main()
    else:
        try: sys.argv[2]
        except IndexError:
            pass
        else:
            delete_module('config')
            imp.load_source('config', os.path.join(os.path.expanduser('~'), '.smartte', sys.argv[2] + '.conf'))
            import config
        startup = MainWindow()
        startup.openFileCli(sys.argv[1])
        startup.main()
