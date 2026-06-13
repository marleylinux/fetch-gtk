"""UI page builders for fetch-gtk"""
import os
import logging
from gi.repository import Gtk, Adw, Gdk
from widgets import (
    _build_section_header,
    _build_monitor_card,
    _build_monitor_card_with_bar,
    _build_fetch_row,
    _build_color_palette_row
)
try:
    from main import APP_VER
except ImportError:
    APP_VER = "1.0.0"


log = logging.getLogger(__name__)

def _make_page_scaffold(name: str, title: str) -> tuple[Gtk.ScrolledWindow, Gtk.Box]:
    """Create a scrolled window and centered clamped box for consistent styling"""
    scrolled = Gtk.ScrolledWindow()
    scrolled.set_vexpand(True)
    scrolled.set_name(name)
    scrolled.get_title = lambda: title
    
    clamp = Adw.Clamp()
    clamp.set_maximum_size(1000)
    clamp.set_margin_top(24)
    clamp.set_margin_bottom(32)
    clamp.set_margin_start(16)
    clamp.set_margin_end(16)
    scrolled.set_child(clamp)
    
    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    clamp.set_child(main_box)
    return scrolled, main_box

def _build_overview_page(app) -> Gtk.ScrolledWindow:
    """Build the classic fastfetch-style overview page"""
    scrolled, main_box = _make_page_scaffold("overview", "Overview")
    
    # Large container box for the fetch panel
    fetch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
    fetch_box.add_css_class("fetch-container")
    fetch_box.set_vexpand(True)
    app.fetch_box = fetch_box
    
    # 1. Left Side: OS / App Logo
    logo_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    logo_container.set_valign(Gtk.Align.CENTER)
    logo_container.add_css_class("fetch-logo-box")
    app.logo_container = logo_container
    logo_container.set_visible(app.ui_settings.get("show_logo", True))
    
    # Determine logo icon
    os_id = app.current_stats.get("os_id", "linux")
    icon_names = [
        f"distributor-logo-{os_id}",
        os_id,
        "distributor-logo",
        "linux-logo",
        "com.marley.fetch-gtk",
        "computer-symbolic"
    ]
    
    logo_image = Gtk.Image()
    logo_image.add_css_class("fetch-logo-image")
    logo_image.set_pixel_size(160)
    
    # Look up in icon theme
    theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
    logo_set = False
    for icon_name in icon_names:
        if theme.has_icon(icon_name):
            logo_image.set_from_icon_name(icon_name)
            logo_set = True
            break
            
    if not logo_set:
        # Check if local assets have the icon
        asset_logo = "/usr/share/fetch-gtk/assets/com.marley.fetch-gtk.png"
        if not os.path.exists(asset_logo):
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            asset_logo = os.path.join(curr_dir, "assets", "com.marley.fetch-gtk.png")
            
        if os.path.exists(asset_logo):
            logo_image.set_from_file(asset_logo)
        else:
            logo_image.set_from_icon_name("computer-symbolic")
            
    logo_container.append(logo_image)
    fetch_box.append(logo_container)
    
    # 2. Right Side: Telemetry details
    details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    details_box.set_valign(Gtk.Align.CENTER)
    details_box.set_hexpand(True)
    
    # Header: user@hostname
    usr = app.ui_settings.get("custom_username") or app.current_stats.get("username", "user")
    host = app.ui_settings.get("custom_hostname") or app.current_stats.get("hostname", "host")
    app.fetch_title = Gtk.Label(label=f"{usr}@{host}")
    app.fetch_title.add_css_class("fetch-title")
    app.fetch_title.set_halign(Gtk.Align.START)
    app.fetch_title.set_xalign(0.0)
    app.fetch_title.set_hexpand(True)
    details_box.append(app.fetch_title)
    
    # Dash separator
    separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    separator.add_css_class("fetch-separator")
    details_box.append(separator)
    
    # Detail rows
    app.fetch_rows = {}
    rows_def = [
        ("OS", "os_pretty"),
        ("Host", "host"),
        ("Kernel", "kernel"),
        ("Uptime", "uptime"),
        ("Packages", "packages"),
        ("Shell", "shell"),
        ("DE", "de"),
        ("WM", "wm"),
        ("Terminal", "terminal"),
        ("CPU", "cpu_model"),
        ("Cores", "cpu_cores"),
        ("CPU Governor", "cpu_governor"),
        ("CPU Driver", "cpu_driver"),
        ("GPU", "gpus"),
        ("Memory", "mem_str"),
        ("Swap", "swap_str"),
        ("Disk", "disk_str"),
        ("Battery", "battery_str"),
        ("Process Count", "process_count"),
        ("Load Average", "load_avg"),
        ("Local IP", "local_ip")
    ]
    
    for label, stat_key in rows_def:
        val = app.get_formatted_stat(stat_key)
        row = _build_fetch_row(label, val)
        is_visible = app.ui_settings.get("show_items", {}).get(stat_key, True)
        row.set_visible(is_visible)
        details_box.append(row)
        app.fetch_rows[stat_key] = row
        
    # Color palette blocks
    palette = _build_color_palette_row()
    details_box.append(palette)
    app.palette_row = palette
    palette.set_visible(app.ui_settings.get("show_palette", True))
    
    fetch_box.append(details_box)
    main_box.append(fetch_box)
    
    return scrolled

def _layout_grid_cards(grid: Gtk.Grid, cards: list):
    """Arrange monitor cards inside a grid layout following standard rules (2 columns max)"""
    count = len(cards)
    for i, card in enumerate(cards):
        if count % 2 == 0 or count > 4:
            col = i % 2
            row = i // 2
            grid.attach(card, col, row, 1, 1)
        elif count == 3:
            if i < 2:
                grid.attach(card, i, 0, 1, 1)
            else:
                grid.attach(card, 0, 1, 2, 1)
        else:
            grid.attach(card, 0, i, 2, 1)

def _build_dashboard_page(app) -> Gtk.ScrolledWindow:
    """Build the real-time resource tracking dashboard"""
    scrolled, main_box = _make_page_scaffold("dashboard", "Dashboard")
    
    # Hero Box at the top
    hero_center = Gtk.CenterBox()
    hero_center.add_css_class("hero-box")
    
    hero_start = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    hero_start.set_valign(Gtk.Align.CENTER)
    
    live_badge = Gtk.Label(label="● Live")
    live_badge.add_css_class("live-status-pill")
    hero_start.append(live_badge)
    hero_center.set_start_widget(hero_start)
    
    hero_center_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
    hero_center_box.set_halign(Gtk.Align.CENTER)
    hero_center_box.set_valign(Gtk.Align.CENTER)
    
    hero_icon = Gtk.Image.new_from_icon_name("computer-symbolic")
    hero_icon.set_pixel_size(48)
    hero_icon.add_css_class("hero-icon")
    hero_center_box.append(hero_icon)
    
    text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    text_box.set_valign(Gtk.Align.CENTER)
    
    app.hero_title = Gtk.Label(label="System Dashboard")
    app.hero_title.add_css_class("hero-title")
    app.hero_title.set_halign(Gtk.Align.START)
    text_box.append(app.hero_title)
    
    subtitle_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    subtitle_lbl = Gtk.Label(label="Active monitoring for")
    subtitle_lbl.add_css_class("hero-subtitle")
    subtitle_box.append(subtitle_lbl)
    
    app.hero_subtitle = Gtk.Label(label=app.current_stats.get("cpu_model", "CPU"))
    app.hero_subtitle.add_css_class("hero-cpu-badge")
    subtitle_box.append(app.hero_subtitle)
    text_box.append(subtitle_box)
    
    hero_center_box.append(text_box)
    hero_center.set_center_widget(hero_center_box)
    
    main_box.append(hero_center)
    
    # Section 1: Processor Telemetry
    main_box.append(_build_section_header("Processor Telemetry", "cpu-symbolic"))
    
    grid_cpu = Gtk.Grid()
    grid_cpu.set_column_spacing(16)
    grid_cpu.set_row_spacing(16)
    grid_cpu.set_hexpand(True)
    
    app.card_cpu_clock = _build_monitor_card("CPU Speed", "GHz", "cpu-symbolic", tag_text="Clock", tag_class="perf")
    app.card_cpu_temp = _build_monitor_card("CPU Temp", "°C", "sensors-temperature-symbolic", tag_text="Thermal", tag_class="system")
    app.card_cpu_load = _build_monitor_card_with_bar("CPU Load", "%", "cpu-symbolic", max_limit=100.0, tag_text="Usage", tag_class="live")
    
    gov = app.current_stats.get("cpu_governor", "Unknown")
    driver = app.current_stats.get("cpu_driver", "Unknown")
    app.card_cpu_gov = _build_monitor_card("CPU Driver / Gov", "", "system-run-symbolic", initial_value=f"{driver} ({gov})", tag_text="Profile", tag_class="system")
    
    _layout_grid_cards(grid_cpu, [app.card_cpu_clock, app.card_cpu_temp, app.card_cpu_load, app.card_cpu_gov])
    main_box.append(grid_cpu)
    
    # Section 2: Memory & Storage
    main_box.append(_build_section_header("Memory & Storage", "ram-symbolic"))
    
    grid_mem = Gtk.Grid()
    grid_mem.set_column_spacing(16)
    grid_mem.set_row_spacing(16)
    grid_mem.set_hexpand(True)
    
    app.card_ram = _build_monitor_card_with_bar("Memory Usage", "GiB", "ram-symbolic", max_limit=app.current_stats.get("mem_total", 16.0), tag_text="RAM", tag_class="live")
    app.card_swap = _build_monitor_card_with_bar("Swap Space", "GiB", "ram-symbolic", max_limit=app.current_stats.get("swap_total", 4.0), tag_text="Swap", tag_class="energy")
    app.card_disk = _build_monitor_card_with_bar("Disk Space (/)", "GiB", "drive-harddisk-symbolic", max_limit=app.current_stats.get("disk_total", 256.0), tag_text="Disk", tag_class="system")
    
    disks = app.current_stats.get("disks", [])
    disk_model = disks[0] if disks else "Unknown Storage"
    app.card_disk_models = _build_monitor_card("Storage Device", "", "drive-harddisk-symbolic", initial_value=disk_model, tag_text="Hardware", tag_class="system")
    
    _layout_grid_cards(grid_mem, [app.card_ram, app.card_swap, app.card_disk, app.card_disk_models])
    main_box.append(grid_mem)
    
    # Section 3: Connectivity & Power
    main_box.append(_build_section_header("Connectivity & Power", "network-wireless-symbolic"))
    
    grid_net = Gtk.Grid()
    grid_net.set_column_spacing(16)
    grid_net.set_row_spacing(16)
    grid_net.set_hexpand(True)
    
    iface = app.current_stats.get("net_interface", "None")
    app.card_net_io = _build_monitor_card("Network IO", "", "network-transmit-receive-symbolic", initial_value=f"{iface} (Live)", tag_text="Traffic", tag_class="live")
    app.card_battery = _build_monitor_card_with_bar("Battery Charge", "%", "battery-symbolic", max_limit=100.0, tag_text="Power", tag_class="energy")
    
    _layout_grid_cards(grid_net, [app.card_net_io, app.card_battery])
    main_box.append(grid_net)
    
    # Section 4: System Activity
    main_box.append(_build_section_header("System Load & Tasks", "utilities-system-monitor-symbolic"))
    
    grid_sys = Gtk.Grid()
    grid_sys.set_column_spacing(16)
    grid_sys.set_row_spacing(16)
    grid_sys.set_hexpand(True)
    
    app.card_processes = _build_monitor_card("Active Processes", "tasks", "utilities-system-monitor-symbolic", initial_value="—", tag_text="Tasks", tag_class="system")
    app.card_load_avg = _build_monitor_card("Load Averages", "", "utilities-system-monitor-symbolic", initial_value="—", tag_text="Load", tag_class="perf")
    
    _layout_grid_cards(grid_sys, [app.card_processes, app.card_load_avg])
    main_box.append(grid_sys)
    
    return scrolled


def _build_settings_page(app) -> Gtk.ScrolledWindow:
    """Build the options, accents and application info page"""
    scrolled, main_box = _make_page_scaffold("settings", "Settings")
    
    main_box.append(_build_section_header("Options", "preferences-system-symbolic"))
    
    group_options = Adw.PreferencesGroup()
    group_options.set_title("Telemetry Options")
    
    # Refresh Interval selector
    row_interval = Adw.ActionRow()
    row_interval.set_title("Telemetry Refresh Rate")
    row_interval.set_subtitle("Select how often live system metrics are queried")
    
    dropdown = Gtk.ComboBoxText()
    dropdown.append("1000", "1 Second")
    dropdown.append("2000", "2 Seconds")
    dropdown.append("5000", "5 Seconds")
    dropdown.append("0", "Manual Only")
    
    # Set active based on current setting
    current_interval = str(app.ui_settings.get("refresh_interval", 2000))
    dropdown.set_active_id(current_interval)
    dropdown.connect("changed", app.on_refresh_interval_changed)
    dropdown.set_valign(Gtk.Align.CENTER)
    app.setting_dropdown = dropdown
    
    row_interval.add_suffix(dropdown)
    
    # Individual Reset
    btn_reset_interval = Gtk.Button(icon_name="edit-clear-symbolic")
    btn_reset_interval.add_css_class("flat")
    btn_reset_interval.set_tooltip_text("Reset to default (2 seconds)")
    btn_reset_interval.set_valign(Gtk.Align.CENTER)
    btn_reset_interval.connect("clicked", lambda _b: dropdown.set_active_id("2000"))
    row_interval.add_suffix(btn_reset_interval)
    
    group_options.add(row_interval)
    
    # Custom Username override
    row_custom_user = Adw.ActionRow()
    row_custom_user.set_title("Custom Username")
    row_custom_user.set_subtitle("Override username displayed in overview")
    entry_user = Gtk.Entry()
    entry_user.set_valign(Gtk.Align.CENTER)
    entry_user.set_text(app.ui_settings.get("custom_username", ""))
    app.setting_entry_user = entry_user
    row_custom_user.add_suffix(entry_user)
    def on_user_entry_changed(entry):
        app.ui_settings["custom_username"] = entry.get_text().strip()
        app._save_ui_settings()
        app._update_ui_values()
    entry_user.connect("changed", on_user_entry_changed)
    
    # Individual Reset
    btn_reset_user = Gtk.Button(icon_name="edit-clear-symbolic")
    btn_reset_user.add_css_class("flat")
    btn_reset_user.set_tooltip_text("Clear custom username override")
    btn_reset_user.set_valign(Gtk.Align.CENTER)
    btn_reset_user.connect("clicked", lambda _b: entry_user.set_text(""))
    row_custom_user.add_suffix(btn_reset_user)
    
    group_options.add(row_custom_user)
    
    # Custom Hostname override
    row_custom_host = Adw.ActionRow()
    row_custom_host.set_title("Custom Hostname")
    row_custom_host.set_subtitle("Override hostname displayed in overview")
    entry_host = Gtk.Entry()
    entry_host.set_valign(Gtk.Align.CENTER)
    entry_host.set_text(app.ui_settings.get("custom_hostname", ""))
    app.setting_entry_host = entry_host
    row_custom_host.add_suffix(entry_host)
    def on_host_entry_changed(entry):
        app.ui_settings["custom_hostname"] = entry.get_text().strip()
        app._save_ui_settings()
        app._update_ui_values()
    entry_host.connect("changed", on_host_entry_changed)
    
    # Individual Reset
    btn_reset_host = Gtk.Button(icon_name="edit-clear-symbolic")
    btn_reset_host.add_css_class("flat")
    btn_reset_host.set_tooltip_text("Clear custom hostname override")
    btn_reset_host.set_valign(Gtk.Align.CENTER)
    btn_reset_host.connect("clicked", lambda _b: entry_host.set_text(""))
    row_custom_host.add_suffix(btn_reset_host)
    
    group_options.add(row_custom_host)
    
    main_box.append(group_options)

    # Overview Layout Options
    main_box.append(_build_section_header("Overview Layout Options", "preferences-desktop-theme-symbolic"))
    
    group_layout = Adw.PreferencesGroup()
    group_layout.set_title("Layout Options")
    
    # Logo switch
    switch_logo = Adw.SwitchRow()
    switch_logo.set_title("Show App Logo")
    switch_logo.set_subtitle("Show or hide the OS / App logo in the overview page")
    switch_logo.set_active(app.ui_settings.get("show_logo", True))
    app.setting_switch_logo = switch_logo
    def on_logo_toggled(switch_row, _spec):
        active = switch_row.get_active()
        app.ui_settings["show_logo"] = active
        app._save_ui_settings()
        if hasattr(app, "logo_container") and app.logo_container:
            app.logo_container.set_visible(active)
    switch_logo.connect("notify::active", on_logo_toggled)
    
    # Individual Reset
    btn_reset_logo = Gtk.Button(icon_name="edit-clear-symbolic")
    btn_reset_logo.add_css_class("flat")
    btn_reset_logo.set_tooltip_text("Reset to show logo")
    btn_reset_logo.set_valign(Gtk.Align.CENTER)
    btn_reset_logo.connect("clicked", lambda _b: switch_logo.set_active(True))
    switch_logo.add_suffix(btn_reset_logo)
    
    group_layout.add(switch_logo)
    
    # Palette switch
    switch_palette = Adw.SwitchRow()
    switch_palette.set_title("Show Color Palette")
    switch_palette.set_subtitle("Show the terminal color circles at the bottom of the overview")
    switch_palette.set_active(app.ui_settings.get("show_palette", True))
    app.setting_switch_palette = switch_palette
    def on_palette_toggled(switch_row, _spec):
        active = switch_row.get_active()
        app.ui_settings["show_palette"] = active
        app._save_ui_settings()
        if hasattr(app, "palette_row") and app.palette_row:
            app.palette_row.set_visible(active)
    switch_palette.connect("notify::active", on_palette_toggled)
    
    # Individual Reset
    btn_reset_palette = Gtk.Button(icon_name="edit-clear-symbolic")
    btn_reset_palette.add_css_class("flat")
    btn_reset_palette.set_tooltip_text("Reset to show color palette")
    btn_reset_palette.set_valign(Gtk.Align.CENTER)
    btn_reset_palette.connect("clicked", lambda _b: switch_palette.set_active(True))
    switch_palette.add_suffix(btn_reset_palette)
    
    group_layout.add(switch_palette)
    
    main_box.append(group_layout)
    
    # Overview Fields
    main_box.append(_build_section_header("Overview Fields", "dialog-information-symbolic"))
    
    group_fields = Adw.PreferencesGroup()
    group_fields.set_title("Visible Telemetry Fields")
    group_fields.set_description("Select which system parameters to show in the overview panel")
    
    toggle_items = [
        ("OS Information", "os_pretty"),
        ("Hardware Host", "host"),
        ("Kernel Version", "kernel"),
        ("System Uptime", "uptime"),
        ("Installed Packages", "packages"),
        ("Shell Information", "shell"),
        ("Desktop Environment", "de"),
        ("Window Manager", "wm"),
        ("Active Terminal", "terminal"),
        ("Processor Model", "cpu_model"),
        ("CPU Cores Info", "cpu_cores"),
        ("CPU Governor", "cpu_governor"),
        ("CPU Driver", "cpu_driver"),
        ("Graphics Card (GPU)", "gpus"),
        ("RAM Utilization", "mem_str"),
        ("Swap Memory", "swap_str"),
        ("Disk Space Utilization", "disk_str"),
        ("Battery Status", "battery_str"),
        ("Process Count", "process_count"),
        ("Load Average", "load_avg"),
        ("Local IP Address", "local_ip")
    ]
    
    defaults = {
        "os_pretty": True, "host": True, "kernel": True, "uptime": True, "packages": True,
        "shell": True, "de": True, "wm": True, "terminal": True, "cpu_model": True,
        "cpu_cores": True, "cpu_governor": False, "cpu_driver": False, "gpus": True,
        "mem_str": True, "swap_str": False, "disk_str": True, "battery_str": True,
        "process_count": False, "load_avg": False, "local_ip": True
    }
    
    app.setting_switches = {}
    for label_name, stat_key in toggle_items:
        switch_row = Adw.SwitchRow()
        switch_row.set_title(label_name)
        is_active = app.ui_settings.get("show_items", {}).get(stat_key, True)
        switch_row.set_active(is_active)
        app.setting_switches[stat_key] = switch_row
        
        def on_toggle_changed(switch_row, _spec, key=stat_key):
            active = switch_row.get_active()
            app.ui_settings.setdefault("show_items", {})[key] = active
            app._save_ui_settings()
            if hasattr(app, "fetch_rows") and key in app.fetch_rows:
                app.fetch_rows[key].set_visible(active)
                
        switch_row.connect("notify::active", on_toggle_changed)
        
        # Individual Reset
        btn_reset_field = Gtk.Button(icon_name="edit-clear-symbolic")
        btn_reset_field.add_css_class("flat")
        btn_reset_field.set_tooltip_text("Reset to default visibility")
        btn_reset_field.set_valign(Gtk.Align.CENTER)
        default_val = defaults.get(stat_key, True)
        btn_reset_field.connect("clicked", lambda _b, s=switch_row, val=default_val: s.set_active(val))
        switch_row.add_suffix(btn_reset_field)
        
        group_fields.add(switch_row)
        
    main_box.append(group_fields)

    # About Section
    main_box.append(_build_section_header("About", "help-about-symbolic"))
    
    group_about = Adw.PreferencesGroup()
    group_about.set_title("Application Details")
    
    row_version = Adw.ActionRow()
    row_version.set_title("Version")
    row_version.set_subtitle(APP_VER)
    group_about.add(row_version)
    
    row_author = Adw.ActionRow()
    row_author.set_title("Developer")
    row_author.set_subtitle("Marley (marleylinux)")
    group_about.add(row_author)
    
    row_repo = Adw.ActionRow()
    row_repo.set_title("Repository")
    row_repo.set_subtitle("https://github.com/marleylinux/fetch-gtk")
    
    btn_link = Gtk.Button(icon_name="document-open-symbolic")
    btn_link.set_tooltip_text("Open GitHub Repo")
    btn_link.set_valign(Gtk.Align.CENTER)
    btn_link.connect("clicked", lambda b: Gtk.show_uri(app.win, "https://github.com/marleylinux/fetch-gtk", Gdk.CURRENT_TIME))
    row_repo.add_suffix(btn_link)
    group_about.add(row_repo)
    
    main_box.append(group_about)
    
    # Factory Reset
    btn_reset = Gtk.Button()
    btn_reset.set_tooltip_text("Wipe all settings, delete configurations, and reset to defaults")
    btn_reset.add_css_class("destructive-action")
    btn_reset.add_css_class("pill")
    btn_reset.set_margin_top(24)
    btn_reset.set_margin_bottom(16)
    btn_reset.set_halign(Gtk.Align.CENTER)
    
    btn_reset_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    btn_reset_icon = Gtk.Image.new_from_icon_name("edit-clear-all-symbolic")
    btn_reset_label = Gtk.Label(label="Factory Reset")
    btn_reset_content.append(btn_reset_icon)
    btn_reset_content.append(btn_reset_label)
    btn_reset.set_child(btn_reset_content)
    
    btn_reset.connect("clicked", app.on_factory_reset_clicked)
    main_box.append(btn_reset)
    
    return scrolled
