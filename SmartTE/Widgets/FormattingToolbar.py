from gi.repository import Pango, Gtk, GLib
from SmartTE.Widgets.Toolbar import Toolbar
from SmartTE.Signals import ToolbarSignals, FormatSignals, FormatTags
from SmartTE.Widgets.ToolButtons import SignalToggledToolButton

class FormattingToolbar(Toolbar):
    def __init__(self):
        super().__init__('Format')
        self.appendToggle(Gtk.STOCK_BOLD,
                          'Bold',
                          FormatTags.BOLD,
                          FormatSignals.BOLD_ACTIVATE,
                          FormatSignals.BOLD_DEACTIVATE,
                          ToolbarSignals.FORMATTING_ACTIVE,
                          ToolbarSignals.FORMATTING_INACTIVE,
                          'Enable or disable bold on the selection')
        self.appendToggle(Gtk.STOCK_ITALIC,
                          'Italic',
                          FormatTags.ITALIC,
                          FormatSignals.ITALIC_ACTIVATE,
                          FormatSignals.ITALIC_DEACTIVATE,
                          ToolbarSignals.FORMATTING_ACTIVE,
                          ToolbarSignals.FORMATTING_INACTIVE,
                          'Enable or disable italicize on the selection')
        self.appendToggle(Gtk.STOCK_UNDERLINE,
                          'Underline',
                          FormatTags.UNDERLINE,
                          FormatSignals.UNDERLINE_ACTIVATE,
                          FormatSignals.UNDERLINE_DEACTIVATE,
                          ToolbarSignals.FORMATTING_ACTIVE,
                          ToolbarSignals.FORMATTING_INACTIVE,
                          'Enable or disable underline on the selection')
        self.appendWidget(Gtk.SeparatorToolItem())
        self.appendFontCombo(ToolbarSignals.FAMILY_CHANGE,
                             FormatSignals.FONT_CHANGE,
                             'Change the font family of the selection')
        self.appendSizeCombo(ToolbarSignals.SIZE_CHANGE,
                             FormatSignals.SIZE_CHANGE,
                             'Change the size of the selection')

    def appendToggle(self, stock, label, tag_name, activateSignal, deactivateSignal, activeSignal, inactiveSignal, tooltip):
        button = SignalToggledToolButton(tag_name, activateSignal, deactivateSignal, activeSignal, inactiveSignal)
        button.set_stock_id(stock)
        button.set_label(label)
        button.set_tooltip_text(tooltip)
        self.appendWidget(button)

    def appendSizeCombo(self, callbackSignal, changeSignal, tooltip):
        sizes = [8, 9, 10, 12, 14, 16, 20, 24, 32, 36, 48, 60, 72]
        #defaultSize = Gtk.TextView().get_pango_context().get_font_description().get_size() / Pango.SCALE
        #if not defaultSize in sizes:
        #    sizes.append(defaultSize)
        #    sizes.sort()
        liststore = Gtk.ListStore(str)
        for i in sizes:
            #liststore.append(['<span font="{name}">{name}</span>'.format(name=i)])
            liststore.append([str(i)])
        combo = Gtk.ComboBox.new_with_model_and_entry(liststore)
        combo.set_entry_text_column(0)
        combo.get_child().set_width_chars(3)
        combo.connect('changed', self.sizeCallback, callbackSignal)
        combo.get_child().connect('activate', self.sizeEntryCallback, callbackSignal)
        #combo.set_active(sizes.index(defaultSize))
        self.appendCombo(combo, tooltip)

    def appendFontCombo(self, callbackSignal, changeSignal, tooltip):
        fontlist = self.get_pango_context().list_families()
        sortedfontlist = sorted(fontlist, key=lambda font: font.get_name())
        liststore = Gtk.ListStore(str)
        #defaultFont = Gtk.TextView().get_pango_context().get_font_description().get_family()
        for font in sortedfontlist:
            if not '.pcf' in font.get_name():
                fontname = GLib.markup_escape_text(font.get_name())
                liststore.append(['<span font_family="{name}">{name}</span>'.format(name=fontname)])
        combo = Gtk.ComboBox.new_with_model(liststore)
        renderer_markup = Gtk.CellRendererText()
        combo.pack_start(renderer_markup, True)
        combo.add_attribute(renderer_markup, "markup", 0)
        combo.connect('changed', self.fontCallback, callbackSignal)
        #combo.set_active(sortedfontlist.index(defaultFont))
        self.appendCombo(combo, tooltip)
        
    def appendCombo(self, combo, tooltip):
        combo.set_tooltip_text(tooltip)
        align = Gtk.Alignment()
        align.set_padding(5, 5, 0, 0)
        align.add(combo)
        toolitem = Gtk.ToolItem()
        toolitem.add(align)
        self.appendWidget(toolitem)

    def fontCallback(self, widget, signal):
        active = widget.get_active()
        active_text = widget.get_model()[active][0]
        font_name = Pango.parse_markup(active_text, -1, '\u0000')[2]
        self.widgetCallback(widget, signal, font_name=font_name)

    def sizeCallback(self, widget, signal):
        if widget.get_active() != -1:
            self.widgetCallback(widget, signal, size=widget.get_child().get_text())

    def sizeEntryCallback(self, widget, signal):
        self.widgetCallback(widget, signal, size=widget.get_text())
