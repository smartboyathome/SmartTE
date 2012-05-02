from gi.repository import Gtk
from SmartTE.Widgets import EditorWindow, FileToolbar, FormattingToolbar, UndoableTextBuffer

window = EditorWindow.EditorWindow()
filebar = FileToolbar.FileToolbar()
formbar = FormattingToolbar.FormattingToolbar()
notebook = Gtk.Notebook()
vbox = Gtk.VBox()

notebook.set_tab_pos(Gtk.PositionType.TOP)
notebook.append_page(filebar, filebar.label)
notebook.append_page(formbar, formbar.label)

scroll = Gtk.ScrolledWindow(None, None)
textview = Gtk.TextView()
textview.set_buffer(UndoableTextBuffer.TextBuffer())
scroll.add(textview)
scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

vbox.pack_start(notebook, False, True, 0)
vbox.pack_start(scroll, True, True, 0)

window.add(vbox)
window.show_all()
Gtk.main()
