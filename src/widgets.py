"""UI elements, card structures, and components for fetch-gtk"""
import logging
from gi.repository import Gtk, Pango

log = logging.getLogger(__name__)

def _bar_class(fraction: float) -> str:
    """Determine progress bar coloring classes (from green to red)"""
    if fraction < 0.5:
        return "low"
    elif fraction < 0.8:
        return "medium"
    return "high"

def _build_section_header(title: str, icon_name: str) -> Gtk.Box:
    """Create a standard styled section header with an icon"""
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
    box.add_css_class("section-title-box")

    icon = Gtk.Image.new_from_icon_name(icon_name)
    icon.add_css_class("category-icon")
    box.append(icon)

    label = Gtk.Label(label=title)
    label.add_css_class("section-title-label")
    box.append(label)

    return box

def _build_monitor_card(label: str, unit: str, icon_name: str, initial_value: str = "—", tag_text: str = None, tag_class: str = None) -> Gtk.Box:
    """Build a general statistics card for telemetry details"""
    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    card.add_css_class("monitor-card")
    card.set_hexpand(True)

    top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    top_row.set_hexpand(True)

    icon = Gtk.Image.new_from_icon_name(icon_name)
    icon.add_css_class("monitor-icon")
    top_row.append(icon)

    name_lbl = Gtk.Label(label=label)
    name_lbl.add_css_class("monitor-name-label")
    name_lbl.set_halign(Gtk.Align.START)
    name_lbl.set_hexpand(True)
    top_row.append(name_lbl)
    
    if tag_text and tag_class:
        tag_lbl = Gtk.Label(label=tag_text)
        tag_lbl.add_css_class("monitor-tag-badge")
        tag_lbl.add_css_class(tag_class)
        tag_lbl.set_halign(Gtk.Align.END)
        top_row.append(tag_lbl)
        
    card.append(top_row)

    val_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    val_row.set_halign(Gtk.Align.START)
    val_row.set_margin_top(8)

    val_lbl = Gtk.Label(label=initial_value)
    val_lbl.add_css_class("monitor-value-label")
    val_row.append(val_lbl)

    if unit:
        unit_lbl = Gtk.Label(label=unit)
        unit_lbl.add_css_class("monitor-unit-label")
        unit_lbl.set_valign(Gtk.Align.END)
        unit_lbl.set_margin_bottom(6)
        val_row.append(unit_lbl)
    card.append(val_row)

    card._val_lbl = val_lbl
    return card

def _build_monitor_card_with_bar(label: str, unit: str, icon_name: str, max_limit: float = 100.0, tag_text: str = None, tag_class: str = None) -> Gtk.Box:
    """Build a stats card that includes a progress bar for utilization metrics"""
    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    card.add_css_class("monitor-card")
    card.set_hexpand(True)

    top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    top_row.set_hexpand(True)

    icon = Gtk.Image.new_from_icon_name(icon_name)
    icon.add_css_class("monitor-icon")
    top_row.append(icon)

    name_lbl = Gtk.Label(label=label)
    name_lbl.add_css_class("monitor-name-label")
    name_lbl.set_halign(Gtk.Align.START)
    name_lbl.set_hexpand(True)
    top_row.append(name_lbl)

    if tag_text and tag_class:
        tag_lbl = Gtk.Label(label=tag_text)
        tag_lbl.add_css_class("monitor-tag-badge")
        tag_lbl.add_css_class(tag_class)
        tag_lbl.set_halign(Gtk.Align.END)
        top_row.append(tag_lbl)

    card.append(top_row)

    val_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    val_row.set_halign(Gtk.Align.START)
    val_row.set_margin_top(8)

    val_lbl = Gtk.Label(label="—")
    val_lbl.add_css_class("monitor-value-label")
    val_row.append(val_lbl)

    if unit:
        unit_lbl = Gtk.Label(label=unit)
        unit_lbl.add_css_class("monitor-unit-label")
        unit_lbl.set_valign(Gtk.Align.END)
        unit_lbl.set_margin_bottom(6)
        val_row.append(unit_lbl)
    card.append(val_row)

    bar = Gtk.ProgressBar()
    bar.add_css_class("usage-bar")
    bar.set_fraction(0.0)
    card.append(bar)

    card._val_lbl = val_lbl
    card._bar = bar
    card._max_limit = max_limit

    def update_val(new_val: float | None):
        if new_val is not None:
            card._val_lbl.set_text(f"{new_val:.1f}")
            frac = min(1.0, max(0.0, new_val / card._max_limit))
            card._bar.set_fraction(frac)
            card._bar.remove_css_class("low")
            card._bar.remove_css_class("medium")
            card._bar.remove_css_class("high")
            card._bar.add_css_class(_bar_class(frac))
        else:
            card._val_lbl.set_text("—")
            card._bar.set_fraction(0.0)

    card.update_val = update_val
    return card

def _build_fetch_row(key_text: str, val_text: str) -> Gtk.Box:
    """Build a terminal-like key-value detail row for the fetch overview"""
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    box.set_margin_bottom(6)
    box.set_hexpand(True)
    
    key_lbl = Gtk.Label(label=f"{key_text}:")
    key_lbl.add_css_class("fetch-key")
    key_lbl.set_halign(Gtk.Align.START)
    key_lbl.set_xalign(0.0)
    
    val_lbl = Gtk.Label(label=val_text)
    val_lbl.add_css_class("fetch-val")
    val_lbl.set_halign(Gtk.Align.START)
    val_lbl.set_xalign(0.0)
    val_lbl.set_hexpand(True)
    val_lbl.set_selectable(True)
    val_lbl.set_wrap(True)
    val_lbl.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
    val_lbl.set_max_width_chars(60)
    
    box.append(key_lbl)
    box.append(val_lbl)
    box._val_lbl = val_lbl
    return box

def _build_color_palette_row() -> Gtk.Box:
    """Build the circular color blocks typical of CLI fetches"""
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    box.set_halign(Gtk.Align.START)
    
    colors = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]
    for c in colors:
        pill = Gtk.Box()
        pill.add_css_class("color-pill")
        pill.add_css_class(f"color-{c}")
        pill.set_tooltip_text(f"Color: {c.capitalize()}")
        box.append(pill)
        
    return box
