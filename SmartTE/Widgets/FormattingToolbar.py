from gi.repository import Gtk, GLib
from SmartTE.Widgets.Toolbar import Toolbar
from SmartTE.Signals import ToolbarSignals, FormatSignals
from SmartTE.Widgets.ToolButtons import SignalToggledToolButton

class FormattingToolbar(Toolbar):
    def __init__(self):
        super().__init__('Format')
        self.appendToggle(Gtk.STOCK_BOLD,
                          'Bold',
                          FormatSignals.BOLD_ACTIVATE,
                          FormatSignals.BOLD_DEACTIVATE,
                          ToolbarSignals.BOLD_ACTIVE,
                          ToolbarSignals.BOLD_INACTIVE,
                          'Enable or disable bold on the selection')
        self.appendToggle(Gtk.STOCK_ITALIC,
                          'Italic',
                          FormatSignals.ITALIC_ACTIVATE,
                          FormatSignals.ITALIC_DEACTIVATE,
                          ToolbarSignals.ITALIC_ACTIVE,
                          ToolbarSignals.ITALIC_INACTIVE,
                          'Enable or disable italicize on the selection')
        self.appendToggle(Gtk.STOCK_UNDERLINE,
                          'Underline',
                          FormatSignals.UNDERLINE_ACTIVATE,
                          FormatSignals.UNDERLINE_DEACTIVATE,
                          ToolbarSignals.UNDERLINE_ACTIVE,
                          ToolbarSignals.UNDERLINE_INACTIVE,
                          'Enable or disable underline on the selection')
        self.appendWidget(Gtk.SeparatorToolItem())
        self.appendFontCombo(ToolbarSignals.FAMILY_CHANGE,
                             'Change the font family of the selection')
        self.appendSizeCombo(ToolbarSignals.SIZE_CHANGE,
                             'Change the size of the selection')

    def appendToggle(self, stock, label, activateSignal, deactivateSignal, activeSignal, inactiveSignal, tooltip):
        button = SignalToggledToolButton(activateSignal, deactivateSignal, activeSignal, inactiveSignal)
        button.set_stock_id(stock)
        button.set_label(label)
        button.set_tooltip_text(tooltip)
        self.appendWidget(button)

    def appendSizeCombo(self, callbackSignal, tooltip):
        sizes = [8, 9, 10, 12, 14, 16, 20, 24, 32, 36, 48, 60, 72]
        #defaultSize = Gtk.TextView().get_pango_context().get_font_description().get_size() / Pango.SCALE
        #if not defaultSize in sizes:
        #    sizes.append(defaultSize)
        #    sizes.sort()
        liststore = Gtk.ListStore(str)
        for i in sizes:
            liststore.append(['<span font="%i">%i</span>' % (i, i)])
        combo = Gtk.ComboBox.new_with_model_and_entry(liststore)
        #combo.set_active(sizes.index(defaultSize))
        combo.set_size_request(60, -1)
        self.appendCombo(combo, callbackSignal, tooltip)

    def appendFontCombo(self, callbackSignal, tooltip):
        fontlist = self.get_pango_context().list_families()
        sortedfontlist = sorted(fontlist, key=lambda font: font.get_name())
        liststore = Gtk.ListStore(str)
        #defaultFont = Gtk.TextView().get_pango_context().get_font_description().get_family()
        for font in sortedfontlist:
            if not '.pcf' in font.get_name():
                fontname = GLib.markup_escape_text(font.get_name())
                liststore.append(['<span font_family="%s">%s</span>' % (fontname, fontname)])
        combo = Gtk.ComboBox.new_with_model_and_entry(liststore)
        #combo.set_active(sortedfontlist.index(defaultFont))
        self.appendCombo(combo, callbackSignal, tooltip)
        
    def appendCombo(self, combo, callbackSignal, tooltip):
        renderer_markup = Gtk.CellRendererText()
        combo.pack_start(renderer_markup, True)
        combo.add_attribute(renderer_markup, "markup", 0)
        combo.connect('changed', self.widgetCallback, callbackSignal)
        combo.set_tooltip_text(tooltip)
        align = Gtk.Alignment()
        align.set_padding(5, 5, 0, 0)
        align.add(combo)
        toolitem = Gtk.ToolItem()
        toolitem.add(align)
        self.appendWidget(toolitem)
