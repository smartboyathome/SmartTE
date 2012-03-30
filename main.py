from gi.repository import Gtk
from SmartTE import EditorWindow, FileToolbar, FormattingToolbar

window = EditorWindow.EditorWindow()
filebar = FileToolbar.FileToolbar()
formbar = FormattingToolbar.FormattingToolbar()
notebook = Gtk.Notebook()
vbox = Gtk.VBox()

notebook.set_tab_pos(Gtk.PositionType.TOP)
notebook.append_page(filebar, filebar.label)
notebook.append_page(formbar, formbar.label)

scroll = Gtk.ScrolledWindow(None, None)
scroll.add(Gtk.TextView())
scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

vbox.pack_start(notebook, False, True, 0)
vbox.pack_start(scroll, True, True, 0)

window.add(vbox)
window.show_all()
Gtk.main()
