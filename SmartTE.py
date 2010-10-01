#!/usr/bin/env python
# Thanks a lot to nemo_ on irc.gnome.org for help on this and Kuleshov Alexander for undostack!

import pygtk, gtk, os, re, sys, gobject, copy, pango, ast, tempfile, enchant, undostack
pygtk.require('2.0')

if not os.path.exists(os.path.join(os.path.expanduser('~'), '.config', 'smartte')):
    os.mkdir(os.path.join(os.path.expanduser('~'), '.config', 'smartte'))



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
            self.textCopyTo()
        elif keyCombo == 'ctrl+shift+x':
            self.textConvertFrom(widget)
            outputStart, outputEnd = self.textBuffer.get_selection_bounds()
            self.textBuffer.delete(outputStart, outputEnd)


    def newFile(self, widget, data=None):
        self.textBuffer.set_text('')
        del self.filename


    def genFileFilters(self, fileSel):
        filter = gtk.FileFilter()
        filter.set_name('All Files')
        filter.add_pattern('*')
        fileSel.add_filter(filter)
        filter = gtk.FileFilter()
        filter.set_name('Plain Text+BBCode')
        filter.add_mime_type('text/plain')
        filter.add_pattern('*.txt')
        fileSel.add_filter(filter)


    def openFile(self, widget, data=None):
        fileSel =  gtk.FileChooserDialog(title='Open File', action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        self.genFileFilters(fileSel)
        response = fileSel.run()
        if response == gtk.RESPONSE_OK:
            self.openFileCli(fileSel.get_filename())
            fileSel.destroy()
        elif response == gtk.RESPONSE_CANCEL:
            fileSel.destroy()


    def openFileCli(self, filename):
        self.filename = filename
        File = open(self.filename, 'r')
        tmpFileData = File.read()
        File.close()
        firstLine = tmpFileData[:tmpFileData.find('\n')+1]
        tmpReg = re.compile(r'{*}\n')
        if not tmpReg.search(firstLine) == None:
            self.docSettings = ast.literal_eval(firstLine[:-1])
            fileData = tmpFileData[tmpFileData.find('\n')+1:]
            self.textConvertFrom(fileData)
            if not self.docSettings['ignoreList'] == []:
                for begin, end in self.docSettings['ignoreList']:
                    self.textBuffer.apply_tag_by_name('ignore', self.textBuffer.get_iter_at_offset(begin), self.textBuffer.get_iter_at_offset(end))
            del(self.docSettings['ignoreList'])
            for word in self.docSettings['docDict']:
                self.dict.add(word)
            if self.docSettings['justStyle'] == 'left':
                self.justLeftButton.set_active(True)
            elif self.docSettings['justStyle'] == 'center':
                self.justCenterButton.set_active(True)
            elif self.docSettings['justStyle'] == 'right':
                self.justRightButton.set_active(True)
            elif self.docSettings['justStyle'] == 'fill':
                self.justFillButton.set_active(True)
        else:
            fileData = tmpFileData
            self.textConvertFrom(fileData)
        self.openCheckSpelling()
        self.textBuffer.set_modified(False)
        self.curPos = self.textBuffer.create_mark(None, self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()))
        self.curOldPos = self.textBuffer.create_mark(None, self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()))


    def writeFile(self):
        docText = self.textConvertTo()
        tmpSettings = copy.deepcopy(self.docSettings)
        tmpSettings['ignoreList'] = []
        if tmpSettings['saveIgnore']:
            tmpIter = self.textBuffer.get_start_iter()
            if tmpIter.begins_tag(self.ignoreTag):
                beginIter = self.textBuffer.get_iter_at_offset(tmpIter.get_offset())
            else:
                tmpIter.forward_to_tag_toggle(self.ignoreTag)
                beginIter = self.textBuffer.get_iter_at_offset(tmpIter.get_offset())
            tmpIter.forward_to_tag_toggle(self.ignoreTag)
            endIter = tmpIter
            tmpSettings['ignoreList'].append((beginIter.get_offset(), endIter.get_offset()))
            tmpVar = tmpIter.forward_to_tag_toggle(self.ignoreTag)
            while tmpVar:
                beginIter = self.textBuffer.get_iter_at_offset(tmpIter.get_offset())
                tmpIter.forward_to_tag_toggle(self.ignoreTag)
                endIter = tmpIter
                tmpSettings['ignoreList'].append((beginIter.get_offset(), endIter.get_offset()))
                tmpVar = tmpIter.forward_to_tag_toggle(self.ignoreTag)
        finalDoc = str(tmpSettings) + '\n' + docText
        File = open(self.filename, 'w')
        File.write(finalDoc)
        File.close()
        self.textBuffer.set_modified(False)


    def saveAsFile(self, widget, data=None):
        fileSel =  gtk.FileChooserDialog(title='Save File', action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        self.genFileFilters(fileSel)
        saveIgnore = gtk.CheckButton('Save Ignore list with file?')
        saveIgnore.set_active(True)
        saveIgnore.set_tooltip_text('If you choose not to save the list, then you will have to remark them again when you reopen the file.')
        saveIgnore.show()
        fileSel.set_extra_widget(saveIgnore)
        response = fileSel.run()
        if response == gtk.RESPONSE_OK:
            self.filename = fileSel.get_filename()
            self.docSettings['saveIgnore'] = saveIgnore.get_active()
            if os.path.exists(self.filename):
                checkDialog = gtk.MessageDialog(fileSel,gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_NONE, 'The file ' + os.path.basename(self.filename) + ' already exists, are you sure you want to overwrite it?')
                checkDialog.add_button(gtk.STOCK_NO, gtk.RESPONSE_NO)
                checkDialog.add_button(gtk.STOCK_YES, gtk.RESPONSE_YES)
                checkResponse = checkDialog.run()
                if checkResponse == gtk.RESPONSE_YES:
                    fileSel.destroy()
                    checkDialog.destroy()
                    self.writeFile()
                elif checkResponse == gtk.RESPONSE_NO:
                    fileSel.destroy()
                    checkDialog.destroy()
            else:
                fileSel.destroy()
                self.writeFile()
        elif response == gtk.RESPONSE_CANCEL:
            fileSel.destroy()


    def saveFile(self, widget, data=None):
        try: self.filename
        except AttributeError:
            self.saveAsFile(widget)
        else:
            self.writeFile()


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
            for tagName in self.sizes:
                tag = self.sizes[tagName]
                iter = self.tmpBuffer.get_iter_at_mark(self.beginMark)
                if iter.begins_tag(tag) and not self.sizeLock[tagName]:
                    self.sizeLock[tagName] = True
                    if tag.get_property('size-set'):
                        self.tmpBuffer.insert(iter, '[size='+str(int(tag.get_property('size-points')))+'px]')
                    elif tag.get_property('scale-set'):
                        self.tmpBuffer.insert(iter, '[size='+str(int(tag.get_property('scale')))+']')
                iter = self.tmpBuffer.get_iter_at_mark(self.endMark)
                if iter.ends_tag(tag) and self.sizeLock[tagName]:
                    self.sizeLock[tagName] = False
                    self.tmpBuffer.insert(iter, '[/size]')
            for tagName in self.fonts:
                tag = self.fonts[tagName]
                iter = self.tmpBuffer.get_iter_at_mark(self.beginMark)
                if iter.begins_tag(tag) and not self.fontLock[tagName]:
                    self.fontLock[tagName] = True
                    self.tmpBuffer.insert(iter, '[font='+tag.get_property('family')+']')
                iter = self.tmpBuffer.get_iter_at_mark(self.endMark)
                if iter.ends_tag(tag) and self.fontLock[tagName]:
                    self.fontLock[tagName] = False
                    self.tmpBuffer.insert(iter, '[/font]')
        self.tmpBuffer = gtk.TextBuffer(self.textTags)
        deserialization = self.tmpBuffer.register_deserialize_tagset()
        self.tmpBuffer.deserialize(self.tmpBuffer, deserialization, self.tmpBuffer.get_start_iter(), self.textBuffer.serialize(self.textBuffer, "application/x-gtk-text-buffer-rich-text", self.textBuffer.get_start_iter(), self.textBuffer.get_end_iter()))
        self.boldLock = False
        self.italLock = False
        self.undlLock = False
        self.sizeLock = {}
        for tagName in self.sizes:
            self.sizeLock[tagName] = False
        self.fontLock = {}
        for tagName in self.fontList:
            self.fontLock[tagName] = False
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
            for tagName in self.sizes:
                tag = self.sizes[tagName]
                iter = self.tmpBuffer.get_iter_at_mark(self.beginMark)
                if iter.begins_tag(tag) and not self.sizeLock[tagName]:
                    self.sizeLock[tagName] = True
                    if tag.get_property('size-set'):
                        self.tmpBuffer.insert(iter, '[size='+str(int(tag.get_property('size-points')))+'px]')
                    elif tag.get_property('scale-set'):
                        self.tmpBuffer.insert(iter, '[size='+str(int(tag.get_property('scale')))+']')
                iter = self.tmpBuffer.get_iter_at_mark(self.endMark)
                if iter.ends_tag(tag) and self.sizeLock[tagName]:
                    self.sizeLock[tagName] = False
                    self.tmpBuffer.insert(iter, '[/size]')
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
        self.sizeLock = {}
        for tagName in self.sizes:
            self.sizeLock[tagName] = False
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
        sizeStarts = []
        sizeEnds = []
        sizeNum = []
        fontStarts = []
        fontEnds = []
        fontName = []
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
        while tmpBuffer.get_text(tmpBuffer.get_start_iter(), tmpBuffer.get_end_iter()).find('[/size]') > -1:
            match = re.search(r'\[size=(\d+(px)?)\]', tmpBuffer.get_text(tmpBuffer.get_start_iter(), tmpBuffer.get_end_iter()))
            sizeStarts.append(tmpBuffer.create_mark(None, tmpBuffer.get_iter_at_offset(match.start()), True))
            sizeNum.append(match.group(1))
            tmpBuffer.delete(tmpBuffer.get_iter_at_offset(match.start()), tmpBuffer.get_iter_at_offset(match.end()))
            match = re.search(r'\[/size\]', tmpBuffer.get_text(tmpBuffer.get_start_iter(), tmpBuffer.get_end_iter()))
            sizeEnds.append(tmpBuffer.create_mark(None, tmpBuffer.get_iter_at_offset(match.start()), True))
            tmpBuffer.delete(tmpBuffer.get_iter_at_offset(match.start()), tmpBuffer.get_iter_at_offset(match.end()))
        while tmpBuffer.get_text(tmpBuffer.get_start_iter(), tmpBuffer.get_end_iter()).find('[/font]') > -1:
            match = re.search(r'\[font=(\w+(?:\s\w+)*)\]', tmpBuffer.get_text(tmpBuffer.get_start_iter(), tmpBuffer.get_end_iter()))
            fontStarts.append(tmpBuffer.create_mark(None, tmpBuffer.get_iter_at_offset(match.start()), True))
            fontName.append(match.group(1))
            tmpBuffer.delete(tmpBuffer.get_iter_at_offset(match.start()), tmpBuffer.get_iter_at_offset(match.end()))
            match = re.search(r'\[/font\]', tmpBuffer.get_text(tmpBuffer.get_start_iter(), tmpBuffer.get_end_iter()))
            fontEnds.append(tmpBuffer.create_mark(None, tmpBuffer.get_iter_at_offset(match.start()), True))
            tmpBuffer.delete(tmpBuffer.get_iter_at_offset(match.start()), tmpBuffer.get_iter_at_offset(match.end()))
        for start, end in zip(boldStarts, boldEnds):
            tmpBuffer.apply_tag_by_name('bold', tmpBuffer.get_iter_at_mark(start), tmpBuffer.get_iter_at_mark(end))
        for start, end in zip(italStarts, italEnds):
            tmpBuffer.apply_tag_by_name('italic', tmpBuffer.get_iter_at_mark(start), tmpBuffer.get_iter_at_mark(end))
        for start, end in zip(undlStarts, undlEnds):
            tmpBuffer.apply_tag_by_name('underline', tmpBuffer.get_iter_at_mark(start), tmpBuffer.get_iter_at_mark(end))
        for start, end, num in zip(sizeStarts, sizeEnds, sizeNum):
            tmpBuffer.apply_tag(self.genSizeTag(num), tmpBuffer.get_iter_at_mark(start), tmpBuffer.get_iter_at_mark(end))
        for start, end, name in zip(fontStarts, fontEnds, fontName):
            tmpBuffer.apply_tag(self.genFontTag(name), tmpBuffer.get_iter_at_mark(start), tmpBuffer.get_iter_at_mark(end))
        self.textBuffer.set_text('')
        deserialization = self.textBuffer.register_deserialize_tagset()
        self.textBuffer.handler_block(self.insertId)
        self.textBuffer.deserialize(self.textBuffer, deserialization, self.textBuffer.get_start_iter(), tmpBuffer.serialize(tmpBuffer, "application/x-gtk-text-buffer-rich-text", tmpBuffer.get_start_iter(), tmpBuffer.get_end_iter()))
        self.textBuffer.handler_unblock(self.insertId)


    def genSizeTag(self, size):
        try: self.sizes[size]
        except KeyError:
            self.sizes[size] = gtk.TextTag('size'+size)
            try: int(size)
            except ValueError:
                self.sizes[size].set_property('size-points', int(size[:-2]))
            else:
                self.sizes[size].set_property('scale', pango.SCALE_LARGE**(int(size)-4))
            self.textTags.add(self.sizes[size])
            return self.sizes[size]
        else:
            return self.sizes[size]


    def genFontTag(self, font):
        try: self.fonts[font]
        except KeyError:
            self.fonts[font] = gtk.TextTag('font '+font)
            self.fonts[font].set_property('family', font)
            self.textTags.add(self.fonts[font])
            return self.fonts[font]
        else:
            return self.fonts[font]


    def changeJust(self, widget, data=None):
        if self.justLeftButton.get_active():
            self.textView.set_justification(gtk.JUSTIFY_LEFT)
            self.docSettings['justStyle'] = 'left'
        elif self.justCenterButton.get_active():
            self.textView.set_justification(gtk.JUSTIFY_CENTER)
            self.docSettings['justStyle'] = 'center'
        elif self.justRightButton.get_active():
            self.textView.set_justification(gtk.JUSTIFY_RIGHT)
            self.docSettings['justStyle'] = 'right'
        elif self.justFillButton.get_active():
            self.textView.set_justification(gtk.JUSTIFY_FILL)
            self.docSettings['justStyle'] = 'fill'


    def undoEntry(self, widget, data=None):
        self.textBuffer.undo()


    def redoEntry(self, widget, data=None):
        self.textBuffer.redo()


    def saveCurPos(self):
        if self.textBuffer.get_iter_at_mark(self.curOldPos) != self.textBuffer.get_iter_at_mark(self.curPos):
            self.textBuffer.delete_mark(self.curOldPos)
            self.curOldPos = self.textBuffer.create_mark(None, self.textBuffer.get_iter_at_mark(self.curPos))
            self.textBuffer.delete_mark(self.curPos)
        self.curPos = self.textBuffer.create_mark(None, self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()))


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
        try: self.sizeStart
        except AttributeError:
            pass
        else:
            if self.sizeTypeBox.get_active_text() == 'px':
                sizeType = 'px'
            self.textBuffer.apply_tag(self.genSizeTag(self.textSizeEntry.get_active_text()+sizeType), self.textBuffer.get_iter_at_mark(self.sizeStart), self.textBuffer.get_iter_at_mark(self.sizeEnd))
        try: self.fontStart
        except AttributeError:
            pass
        else:
            self.textBuffer.apply_tag(self.genFontTag(self.fontListBox.get_active_text()), self.textBuffer.get_iter_at_mark(self.fontStart), self.textBuffer.get_iter_at_mark(self.fontEnd))
        if text == ' ':
            beginWord = self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert())
            endWord = self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert())
            beginWord.backward_word_start()
            endWord.backward_word_start()
            endWord.forward_word_end()
            tmpIter1 = beginWord.copy()
            tmpIter1.backward_chars(2)
            tmpStr = self.textBuffer.get_text(tmpIter1, beginWord)
            try: tmpStr[1]
            except IndexError: pass
            else:
                if re.match(r'[a-zA-Z]', tmpStr[0]) and tmpStr[1] == "'":
                    beginWord.backward_word_start()
                else:
                    tmpIter1 = endWord.copy()
                    tmpIter1.forward_chars(2)
                    tmpStr = self.textBuffer.get_text(endWord, tmpIter1)
                    if tmpStr[0] == "'" and re.match(r'[a-zA-Z]', tmpStr[1]):
                        endWord.forward_word_end()
            word = self.textBuffer.get_text(beginWord, endWord)
            try: int(word)
            except ValueError:
                if not self.dict.check(word) and not beginWord.has_tag(self.ignoreTag):
                    self.textBuffer.apply_tag_by_name('error', beginWord, endWord)
                else:
                    self.textBuffer.remove_tag_by_name('error', beginWord, endWord)
            if endWord.get_char() == ' ' and endWord.has_tag(self.errTag):
                tmpIter1 = endWord.copy()
                tmpIter1.forward_char()
                self.textBuffer.remove_tag_by_name('error', endWord, tmpIter1)
                if tmpIter1.starts_word():
                    tmpIter2 = tmpIter1.copy()
                    tmpIter2.forward_word_end()
                    word = self.textBuffer.get_text(tmpIter1, tmpIter2)
                    try: int(word)
                    except ValueError:
                        if not self.dict.check(word)and not beginWord.has_tag(self.ignoreTag):
                            self.textBuffer.apply_tag_by_name('error', tmpIter1, tmpIter2)
                        else:
                            self.textBuffer.remove_tag_by_name('error', tmpIter1, tmpIter2)
        elif not self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()).is_end():
            self.typed = True


    def backspaceEvent(self, event):
        self.saveCurPos()
        self.typed = True


    def openCheckSpelling(self):
        beginWord = self.textBuffer.get_start_iter()
        endWord = self.textBuffer.get_start_iter()
        keepGoing = endWord.forward_word_end()
        if not beginWord.starts_word():
            beginWord.forward_word_end()
            beginWord.backward_word_start()
        if not self.dict.check(self.textBuffer.get_text(beginWord, endWord)):
            self.textBuffer.apply_tag_by_name('error', beginWord, endWord)
        while endWord.forward_word_end():
            beginWord.forward_word_ends(2)
            beginWord.backward_word_start()
            if not self.dict.check(self.textBuffer.get_text(beginWord, endWord)) and not beginWord.has_tag(self.ignoreTag):
                self.textBuffer.apply_tag_by_name('error', beginWord, endWord)


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


    def dectForm(self, widget=None, event=None, tmpVar=None, tmpVar2=None, beginWord=None, endWord=None):
        self.saveCurPos()
        curIter = self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert())
        curIter.backward_char()
        curTags = curIter.get_tags()
        bolded = False
        underlined = False
        italicized = False
        sizeSet = False
        size = self.defSize
        sizeType = 'px'
        fontSet = False
        fontName = self.defFont
        for tag in curTags:
            if tag.get_property('weight-set'):
                bolded = True
            elif tag.get_property('underline-set'):
                underlined = True
            elif tag.get_property('style-set'):
                italicized = True
            elif tag.get_property('size-set'):
                sizeSet = True
                size = tag.get_property('size-points')
                sizeType = 'px'
            elif tag.get_property('scale-set'):
                sizeSet = True
                size = tag.get_property('scale')
                sizeType = 'pt'
            elif tag.get_property('family-set'):
                fontSet = True
                fontName = tag.get_property('family')
        if bolded and not self.boldButton.get_active():
            self.boldButton.handler_block(self.boldHandId)
            self.boldButton.set_active(True)
            self.boldButton.handler_unblock(self.boldHandId)
        elif not bolded and self.boldButton.get_active():
            self.boldButton.handler_block(self.boldHandId)
            self.boldButton.set_active(False)
            self.boldButton.handler_unblock(self.boldHandId)
        if italicized and not self.italButton.get_active():
            self.italButton.handler_block(self.italHandId)
            self.italButton.set_active(True)
            self.italButton.handler_unblock(self.italHandId)
        elif not italicized and self.italButton.get_active():
            self.italButton.handler_block(self.italHandId)
            self.italButton.set_active(False)
            self.italButton.handler_unblock(self.italHandId)
        if underlined and not self.undlButton.get_active():
            self.undlButton.handler_block(self.undlHandId)
            self.undlButton.set_active(True)
            self.undlButton.handler_unblock(self.undlHandId)
        elif not underlined and self.italButton.get_active():
            self.undlButton.handler_block(self.undlHandId)
            self.undlButton.set_active(False)
            self.undlButton.handler_unblock(self.undlHandId)
        if sizeSet and not size == self.textSizeEntry.child.get_text():
            if sizeType == 'px':
                self.sizeTypeBox.set_active(0)
                self.textSizeEntry.child.handler_block(self.textHandId)
                self.textSizeEntry.child.set_text(str(int(size)))
                self.textSizeEntry.child.handler_unblock(self.textHandId)
            elif sizeType == 'pt':
                self.sizeTypeBox.set_active(1)
                self.textSizeEntry.child.handler_block(self.textHandId)
                self.textSizeEntry.child.set_text(str(int(size)))
                self.textSizeEntry.child.handler_unblock(self.textHandId)
        elif not sizeSet and not size == self.textSizeEntry.child.get_text():
            self.sizeTypeBox.set_active(0)
            self.textSizeEntry.child.handler_block(self.textHandId)
            self.textSizeEntry.child.set_text(str(int(size)))
            self.textSizeEntry.child.handler_unblock(self.textHandId)
        if fontSet and not fontName == self.fontListBox.get_text():
            self.fontListBox.handler_block(self.fontHandId)
            self.fontListBox.set_active(self.fontList.index(fontName))
            self.fontListBox.handler_unblock(self.fontHandId)
        if self.typed:
            if beginWord == None or endWord == None:
                beginWord = self.textBuffer.get_iter_at_mark(self.curOldPos)
                endWord = self.textBuffer.get_iter_at_mark(self.curOldPos)
                if beginWord.starts_word():
                    endWord.forward_word_end()
                elif endWord.ends_word():
                    beginWord.backward_word_start()
                elif beginWord.inside_word():
                    beginWord.backward_word_start()
                    endWord.forward_word_end()
                tmpIter1 = beginWord.copy()
                tmpIter1.backward_chars(2)
                tmpStr = self.textBuffer.get_text(tmpIter1, beginWord)
                if re.match(r'[a-zA-Z]', tmpStr[0]) and tmpStr[1] == "'":
                    beginWord.backward_word_start()
                else:
                    tmpIter1 = endWord.copy()
                    tmpIter1.forward_chars(2)
                    tmpStr = self.textBuffer.get_text(endWord, tmpIter1)
                    try: tmpStr[1]
                    except IndexError: pass
                    else:
                        if tmpStr[0] == "'" and re.match(r'[a-zA-Z]', tmpStr[1]):
                            endWord.forward_word_end()
            word = self.textBuffer.get_text(beginWord, endWord)
            try: word[0]
            except IndexError: pass
            else:
                try: int(word)
                except ValueError:
                    if not self.dict.check(word) and not beginWord.has_tag(self.ignoreTag):
                        self.textBuffer.apply_tag_by_name('error', beginWord, endWord)
                    else:
                        self.textBuffer.remove_tag_by_name('error', beginWord, endWord)
            self.typed = False


    def spellSuggest(self, widget, menu):
        x, y = self.textView.get_pointer()
        x, y = self.textView.window_to_buffer_coords(gtk.TEXT_WINDOW_WIDGET, x, y)
        curIter = self.textView.get_iter_at_location(x, y)
        beginWord = self.textView.get_iter_at_location(x, y)
        endWord = self.textView.get_iter_at_location(x, y)
        if beginWord.starts_word():
            endWord.forward_word_end()
        elif endWord.ends_word():
            beginWord.backward_word_start()
        elif beginWord.inside_word():
            endWord.forward_word_end()
            beginWord.backward_word_start()
        word = self.textBuffer.get_text(beginWord, endWord)
        if curIter.has_tag(self.errTag):
            beginWord = self.textView.get_iter_at_location(x, y)
            endWord = self.textView.get_iter_at_location(x, y)
            if beginWord.starts_word():
                endWord.forward_word_end()
            elif endWord.ends_word():
                beginWord.backward_word_start()
            elif beginWord.inside_word():
                endWord.forward_word_end()
                beginWord.backward_word_start()
            tmpIter1 = beginWord.copy()
            tmpIter1.backward_chars(2)
            tmpStr = self.textBuffer.get_text(tmpIter1, beginWord)
            if not tmpStr[0] == " " and tmpStr[1] == "'":
                beginWord.backward_word_start()
            else:
                tmpIter1 = endWord.copy()
                tmpIter1.forward_chars(2)
                tmpStr = self.textBuffer.get_text(endWord, tmpIter1)
                if tmpStr[0] == "'" and not tmpStr[1] == " ":
                    endWord.forward_word_end()
            suggestions = self.dict.suggest(word)
            suggestItem = gtk.MenuItem(label='Spelling Suggestions')
            suggestMenu = gtk.Menu()
            for newWord in suggestions:
                item = gtk.MenuItem(label=newWord)
                item.connect('activate', self.replaceWord, newWord, beginWord, endWord)
                suggestMenu.add(item)
            sep1 = gtk.SeparatorMenuItem()
            suggestMenu.add(sep1)
            ignoreItem = gtk.MenuItem(label='Add to ignore list')
            ignoreItem.connect('activate', self.ignoreWord, beginWord, endWord)
            ignoreItem.set_tooltip_text('Ignores this instance')
            suggestMenu.add(ignoreItem)
            docDictItem = gtk.MenuItem(label='Add to document dictionary')
            docDictItem.connect('activate', self.docDict, 'add', word, beginWord, endWord)
            suggestMenu.add(docDictItem)
            dictItem = gtk.MenuItem(label='Add to global dictionary')
            dictItem.connect('activate', self.globalDict, 'add', word, beginWord, endWord)
            suggestMenu.add(dictItem)
            suggestItem.set_submenu(suggestMenu)
            suggestItem.show_all()
            menu.insert(suggestItem, 0)
        if curIter.has_tag(self.ignoreTag):
            item = gtk.MenuItem(label='Remove from ignore list')
            item.connect('activate', self.unIgnoreWord, beginWord, endWord)
            item.show()
            menu.insert(item, 0)
        elif word in self.docSettings['docDict']:
            item = gtk.MenuItem(label='Remove from document dictionary')
            item.connect('activate', self.docDict, 'remove', word, beginWord, endWord)
            item.show()
            menu.insert(item, 0)
        elif self.globalDict(command='search', word=word):
            item = gtk.MenuItem(label='Remove from global dictionary')
            item.connect('activate', self.globalDict, 'remove', word, beginWord, endWord)
            item.show()
            menu.insert(item, 0)


    def replaceWord(self, item, word, beginWord, endWord):
        self.textBuffer.remove_tag_by_name('error', beginWord, endWord)
        wordPos = self.textBuffer.create_mark(None, beginWord, True)
        wordTags = beginWord.get_tags()
        self.textBuffer.delete(beginWord, endWord)
        self.textBuffer.insert(self.textBuffer.get_iter_at_mark(wordPos), word)
        beginWord = self.textBuffer.get_iter_at_mark(wordPos)
        endWord = self.textBuffer.get_iter_at_mark(wordPos)
        endWord.forward_word_end()
        for tag in wordTags:
            self.textBuffer.apply_tag(tag, beginWord, endWord)
        self.textBuffer.delete_mark(wordPos)


    def ignoreWord(self, item, beginWord, endWord):
        self.textBuffer.remove_tag_by_name('error', beginWord, endWord)
        self.textBuffer.apply_tag_by_name('ignore', beginWord, endWord)


    def unIgnoreWord(self, item, beginWord, endWord):
        self.textBuffer.remove_tag_by_name('ignore', beginWord, endWord)
        self.typed = True
        self.dectForm(beginWord=beginWord, endWord=endWord)


    def docDict(self, item, command, word=None, beginWord=None, endWord=None):
        if command == 'add':
            if beginWord != None and endWord != None:
                self.textBuffer.remove_tag_by_name('error', beginWord, endWord)
                origEnd = endWord.get_offset()
                curStart = self.textBuffer.get_iter_at_offset(beginWord.get_offset())
                if curStart.backward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY) != None:
                    curStart, curEnd = curStart.backward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY)
                    keepGoing = True
                else:
                    keepGoing = False
                while keepGoing:
                    if curStart.has_tag(self.errTag):
                        self.textBuffer.remove_tag_by_name('error', curStart, curEnd)
                    if curStart.backward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY) != None:
                        curStart, curEnd = curStart.backward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY)
                        keepGoing = True
                    else:
                        keepGoing = False
                curEnd = self.textBuffer.get_iter_at_offset(origEnd)
                if curEnd.forward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY) != None:
                    curStart, curEnd = curEnd.forward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY)
                    keepGoing = True
                else:
                    keepGoing = False
                while keepGoing:
                    if curStart.has_tag(self.errTag):
                        self.textBuffer.remove_tag_by_name('error', curStart, curEnd)
                    if curEnd.forward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY) != None:
                        curStart, curEnd = curEnd.forward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY)
                        keepGoing = True
                    else:
                        keepGoing = False
            self.dict.add(word)
            self.docSettings['docDict'].append(word)
        elif command == 'remove':
            if beginWord != None and endWord != None:
                self.textBuffer.apply_tag_by_name('error', beginWord, endWord)
                origEnd = endWord.get_offset()
                curStart = self.textBuffer.get_iter_at_offset(beginWord.get_offset())
                if curStart.backward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY) != None:
                    curStart, curEnd = curStart.backward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY)
                    keepGoing = True
                else:
                    keepGoing = False
                while keepGoing:
                    if curStart.has_tag(self.errTag):
                        self.textBuffer.apply_tag_by_name('error', curStart, curEnd)
                    if curStart.backward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY) != None:
                        curStart, curEnd = curStart.backward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY)
                        keepGoing = True
                    else:
                        keepGoing = False
                curEnd = self.textBuffer.get_iter_at_offset(origEnd)
                if curEnd.forward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY) != None:
                    curStart, curEnd = curEnd.forward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY)
                    keepGoing = True
                else:
                    keepGoing = False
                while keepGoing:
                    if curStart.has_tag(self.errTag):
                        self.textBuffer.apply_tag_by_name('error', curStart, curEnd)
                    if curEnd.forward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY) != None:
                        curStart, curEnd = curEnd.forward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY)
                        keepGoing = True
                    else:
                        keepGoing = False
            self.docSettings['docDict'].remove(word)
            self.dict.remove(word)


    def globalDict(self, event=None, command=None, word=None, beginWord=None, endWord=None):
        if command == 'init':
            self.dictFile = os.path.join(os.path.expanduser('~'), '.config', 'smartte', 'dict')
            if not os.path.exists(self.dictFile):
                f = open(self.dictFile, 'w')
                f.write('SmartTE')
                f.close()
                self.dict.add('SmartTE')
            else:
                f = open(self.dictFile, 'r')
                for line in f:
                    self.dict.add(line)
                f.close()
        elif command == 'add':
            if beginWord != None and endWord != None:
                self.textBuffer.remove_tag_by_name('error', beginWord, endWord)
                origEnd = endWord.get_offset()
                curStart = self.textBuffer.get_iter_at_offset(beginWord.get_offset())
                if curStart.backward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY) != None:
                    curStart, curEnd = curStart.backward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY)
                    keepGoing = True
                else:
                    keepGoing = False
                while keepGoing:
                    if curStart.has_tag(self.errTag):
                        self.textBuffer.remove_tag_by_name('error', curStart, curEnd)
                    if curStart.backward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY) != None:
                        curStart, curEnd = curStart.backward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY)
                        keepGoing = True
                    else:
                        keepGoing = False
                curEnd = self.textBuffer.get_iter_at_offset(origEnd)
                if curEnd.forward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY) != None:
                    curStart, curEnd = curEnd.forward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY)
                    keepGoing = True
                else:
                    keepGoing = False
                while keepGoing:
                    if curStart.has_tag(self.errTag):
                        self.textBuffer.remove_tag_by_name('error', curStart, curEnd)
                    if curEnd.forward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY) != None:
                        curStart, curEnd = curEnd.forward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY)
                        keepGoing = True
                    else:
                        keepGoing = False
            f = open(self.dictFile, 'a')
            f.write('\n' + word)
            f.close()
            self.dict.add(word)
        elif command == 'search':
            f = open(self.dictFile, 'r')
            tmpText = f.read()
            f.close()
            tmpList = tmpText.split('\n')
            if word in tmpList:
                return True
            else:
                return False
        elif command == 'remove':
            if beginWord != None and endWord != None:
                self.textBuffer.apply_tag_by_name('error', beginWord, endWord)
                origEnd = endWord.get_offset()
                curStart = self.textBuffer.get_iter_at_offset(beginWord.get_offset())
                if curStart.backward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY) != None:
                    curStart, curEnd = curStart.backward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY)
                    keepGoing = True
                else:
                    keepGoing = False
                while keepGoing:
                    if not curStart.has_tag(self.errTag):
                        self.textBuffer.apply_tag_by_name('error', curStart, curEnd)
                    if curStart.backward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY) != None:
                        curStart, curEnd = curStart.backward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY)
                        keepGoing = True
                    else:
                        keepGoing = False
                curEnd = self.textBuffer.get_iter_at_offset(origEnd)
                if curEnd.forward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY) != None:
                    curStart, curEnd = curEnd.forward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY)
                    keepGoing = True
                else:
                    keepGoing = False
                while keepGoing:
                    if not curStart.has_tag(self.errTag):
                        self.textBuffer.apply_tag_by_name('error', curStart, curEnd)
                    if curEnd.forward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY) != None:
                        curStart, curEnd = curEnd.forward_search(word, gtk.TEXT_SEARCH_VISIBLE_ONLY)
                        keepGoing = True
                    else:
                        keepGoing = False
            f = open(self.dictFile, 'r')
            tmpText = f.read()
            f.close()
            tmpList = tmpText.split('\n')
            tmpList.remove(word)
            tmpText = tmpList[0]
            for word in tmpList[1:]:
                tmpText = tmpText + '\n' + word
            f = open(self.dictFile, 'w')
            f.write(tmpText)
            f.close()


    def changeSizeEntry(self, combobox):
        model = self.textSizeEntry.get_model()
        model.clear()
        self.textSizeEntry.set_model(model)
        if combobox.get_active_text() == 'px':
            sizes = self.defPixelSizes
        else:
            sizes = self.defScaleSizes
        for size in sizes:
            self.textSizeEntry.append_text(str(size))
        self.textSizeEntry.set_active(0)


    def changeSize(self, combobox):
        if self.sizeTypeBox.get_active_text() == 'px':
            if self.textBuffer.get_selection_bounds() != ():
                start, end = self.textBuffer.get_selection_bounds()
                self.textBuffer.apply_tag(self.genSizeTag(combobox.get_text()+'px'), start, end)
            else:
                self.sizeStart = self.textBuffer.create_mark(None, self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()), True)
                self.sizeEnd = self.textBuffer.create_mark(None, self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()), False)
        else:
            if self.textBuffer.get_selection_bounds() != ():
                start, end = self.textBuffer.get_selection_bounds()
                self.textBuffer.apply_tag(self.genSizeTag(combobox.get_text()), start, end)
            else:
                self.sizeStart = self.textBuffer.create_mark(None, self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()), True)
                self.sizeEnd = self.textBuffer.create_mark(None, self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()), False)


    def changeFont(self, combobox):
        if self.textBuffer.get_selection_bounds() != ():
            start, end = self.textBuffer.get_selection_bounds()
            self.textBuffer.apply_tag(self.genFontTag(combobox.get_active_text()), start, end)
        else:
            self.fontStart = self.textBuffer.create_mark(None, self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()), True)
            self.fontEnd = self.textBuffer.create_mark(None, self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()), False)


    def tabFocus(self, notebook, page, page_num):
        self.textView.grab_focus()


    def __init__(self):
        self.window = gtk.Window()
        self.window.set_border_width(0)
        self.window.set_resizable(True)
        self.window.set_default_size(675, 300)
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
        self.textView.connect('populate-popup', self.spellSuggest)
        self.insertId = self.textBuffer.connect_after('insert-text', self.persistAttr)
        self.textView.connect_after('backspace', self.backspaceEvent)

        self.curPos = self.textBuffer.create_mark(None, self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()))
        self.curOldPos = self.textBuffer.create_mark(None, self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()))
        self.dict = enchant.Dict()
        self.globalDict(command='init')
        self.typed = False
        self.docSettings = {'justStyle':'left', 'saveIgnore':True, 'docDict':[]}
        self.sizes = {}
        self.defPixelSizes = [9,10,12,14,16,20,24,32,40,48,60,72]
        self.defScaleSizes = [1,2,3,4,5,6,7]
        self.fonts = {}
        self.fontList = []
        for font in self.textView.get_pango_context().list_families():
            self.fontList.append(font.get_name())
        self.fontList = sorted(self.fontList)

        self.boldTag = gtk.TextTag('bold')
        self.boldTag.set_property('weight', pango.WEIGHT_BOLD)
        self.textTags.add(self.boldTag)
        self.italTag = gtk.TextTag('italic')
        self.italTag.set_property('style', pango.STYLE_ITALIC)
        self.textTags.add(self.italTag)
        self.undlTag = gtk.TextTag('underline')
        self.undlTag.set_property('underline', pango.UNDERLINE_SINGLE)
        self.textTags.add(self.undlTag)
        self.errTag = gtk.TextTag('error')
        self.errTag.set_property('underline', pango.UNDERLINE_ERROR)
        self.textTags.add(self.errTag)
        self.ignoreTag = gtk.TextTag('ignore')
        self.textTags.add(self.ignoreTag)

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
        copyButton = gtk.ToolButton(gtk.STOCK_COPY)
        copyButton.connect('clicked', self.textCopyTo)
        copyButton.set_tooltip_text('Copy to BBCode')
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
        filebar.insert(newButton, -1)
        filebar.insert(openButton, -1)
        filebar.insert(saveButton, -1)
        filebar.insert(saveAsButton, -1)
        filebar.insert(copyButton, -1)
        filebar.insert(undoButton, -1)
        filebar.insert(redoButton, -1)
        filebar.insert(quitButton, -1)
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
        self.fontListBox = gtk.combo_box_new_text()
        #self.fontListBox.set_size_request(60, -1)
        self.defFont = self.textView.get_pango_context().get_font_description().get_family()
        for font in self.fontList:
            self.fontListBox.append_text(font)
        self.fontListBox.set_active(self.fontList.index(self.defFont))
        self.fontHandId = self.fontListBox.connect('changed', self.changeFont)
        self.fontListAlign = gtk.Alignment()
        self.fontListAlign.set_padding(5, 5, 0, 0)
        self.fontListAlign.add(self.fontListBox)
        self.fontListItem = gtk.ToolItem()
        self.fontListItem.add(self.fontListAlign)
        sep2 = gtk.SeparatorToolItem()
        self.textSizeEntry = gtk.combo_box_entry_new_text()
        self.textSizeEntry.set_size_request(60, -1)
        self.defSize = self.textView.get_pango_context().get_font_description().get_size()/pango.SCALE
        try: self.defPixelSizes.index(self.defSize)
        except ValueError:
            self.defPixelSizes.append(self.defSize)
            self.defPixelSizes = sorted(self.defPixelSizes)
            index = self.defPixelSizes.index(self.defSize)
        else:
            index = self.defPixelSizes.index(self.defSize)
        for size in self.defPixelSizes:
            self.textSizeEntry.append_text(str(size))
        self.textSizeEntry.set_active(index)
        self.textHandId = self.textSizeEntry.child.connect('changed', self.changeSize)
        self.textSizeAlign = gtk.Alignment()
        self.textSizeAlign.set_padding(5, 5, 0, 0)
        self.textSizeAlign.add(self.textSizeEntry)
        self.textSizeItem = gtk.ToolItem()
        self.textSizeItem.add(self.textSizeAlign)
        self.sizeTypeBox = gtk.combo_box_new_text()
        self.sizeTypeBox.set_size_request(50, -1)
        self.sizeTypeBox.append_text('px')
        self.sizeTypeBox.append_text('pt')
        self.sizeTypeBox.set_active(0)
        self.sizeTypeBox.connect('changed', self.changeSizeEntry)
        self.sizeTypeAlign = gtk.Alignment()
        self.sizeTypeAlign.set_padding(5, 5, 0, 0)
        self.sizeTypeAlign.add(self.sizeTypeBox)
        self.sizeTypeItem = gtk.ToolItem()
        self.sizeTypeItem.add(self.sizeTypeAlign)
        sep3 = gtk.SeparatorToolItem()
        self.justLeftButton = gtk.RadioToolButton(None, gtk.STOCK_JUSTIFY_LEFT)
        self.leftId = self.justLeftButton.connect('toggled', self.changeJust)
        self.justLeftButton.set_tooltip_text('Justify text to the left')
        self.justCenterButton = gtk.RadioToolButton(self.justLeftButton, gtk.STOCK_JUSTIFY_CENTER)
        self.centerId = self.justCenterButton.connect('toggled', self.changeJust)
        self.justCenterButton.set_tooltip_text('Justify text to the center')
        self.justRightButton = gtk.RadioToolButton(self.justLeftButton, gtk.STOCK_JUSTIFY_RIGHT)
        self.rightId = self.justRightButton.connect('toggled', self.changeJust)
        self.justRightButton.set_tooltip_text('Justify text to the right')
        self.justFillButton = gtk.RadioToolButton(self.justLeftButton, gtk.STOCK_JUSTIFY_FILL)
        self.fillId = self.justFillButton.connect('toggled', self.changeJust)
        self.justFillButton.set_tooltip_text('Justify text so it fills window')
        formbar = gtk.Toolbar()
        formbar.set_style(gtk.TOOLBAR_ICONS)
        formbar.insert(self.boldButton, -1)
        formbar.insert(self.italButton, -1)
        formbar.insert(self.undlButton, -1)
        formbar.insert(sep1, -1)
        formbar.insert(self.fontListItem, -1)
        formbar.insert(sep2, -1)
        formbar.insert(self.textSizeItem, -1)
        formbar.insert(self.sizeTypeItem, -1)
        formbar.insert(sep3, -1)
        formbar.insert(self.justLeftButton, -1)
        formbar.insert(self.justCenterButton, -1)
        formbar.insert(self.justRightButton, -1)
        formbar.insert(self.justFillButton, -1)
        formLabel = gtk.Label('Format')

        notebook = gtk.Notebook()
        notebook.set_tab_pos(gtk.POS_TOP)
        notebook.append_page(filebar, fileLabel)
        notebook.append_page(formbar, formLabel)
        notebook.connect_after('switch-page', self.tabFocus)

        statusbar = gtk.Statusbar()
        statusbar.set_has_resize_grip(False)
        statusHBox = gtk.HBox(False, 0)
        statusHBox.pack_start(statusbar, True)

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
