"""Main application window layout for fetch-gtk"""
from gi.repository import Gtk, Adw, Gio, GObject
from pages import (
    _build_overview_page,
    _build_dashboard_page,
    _build_settings_page
)

def build_main_window(app) -> Adw.ApplicationWindow:
    """Build the main window and bind the view stack page items"""
    win = Adw.ApplicationWindow(application=app)
    win.set_default_size(1050, 750)
    win.set_title("fetch-gtk")
    win.add_css_class("fetch-gtk-win")

    # Refresh Button
    app.btn_refresh = Gtk.Button(icon_name="view-refresh-symbolic")
    app.btn_refresh.set_tooltip_text("Refresh stats (F5)")
    app.btn_refresh.connect("clicked", app.on_refresh_clicked)

    # Menu Button
    app.menu_btn = Gtk.MenuButton(icon_name="open-menu-symbolic")
    app.menu_btn.set_tooltip_text("Main Menu")

    # View stack
    view_stack = Adw.ViewStack()
    view_stack.set_vexpand(True)
    app.view_stack = view_stack

    # Dashboard page (Live usage grids)
    dashboard_page = _build_dashboard_page(app)
    view_stack.add_titled_with_icon(
        dashboard_page, "dashboard", "Dashboard",
        "utilities-system-monitor-symbolic"
    )

    # Overview page (Logo + key-value stats)
    overview_page = _build_overview_page(app)
    view_stack.add_titled_with_icon(
        overview_page, "overview", "Overview",
        "computer-symbolic"
    )

    # Settings page (options, color accent etc.)
    settings_page = _build_settings_page(app)
    view_stack.add_titled_with_icon(
        settings_page, "settings", "Settings",
        "preferences-system-symbolic"
    )

    # Sidebar Split View
    split_view = Adw.OverlaySplitView()
    split_view.set_sidebar_position(Gtk.PackType.START)
    split_view.set_min_sidebar_width(180)
    split_view.set_max_sidebar_width(240)
    split_view.set_sidebar_width_fraction(0.20)
    split_view.set_show_sidebar(True)

    # Sidebar Box
    sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    sidebar_box.add_css_class("sidebar-pane")
    
    sidebar_header = Adw.HeaderBar()
    sidebar_header.add_css_class("sidebar-header")
    sidebar_header.set_show_end_title_buttons(False)

    sidebar_title = Gtk.Label(label="fetch-gtk")
    sidebar_title.add_css_class("title")
    sidebar_title.add_css_class("bold")
    sidebar_header.set_title_widget(sidebar_title)
    sidebar_header.pack_end(app.menu_btn)
    sidebar_box.append(sidebar_header)

    sidebar_navigation = Adw.ViewSwitcherSidebar()
    sidebar_navigation.add_css_class("navigation-sidebar")
    sidebar_navigation.set_stack(view_stack)

    sidebar_scrolled = Gtk.ScrolledWindow()
    sidebar_scrolled.set_vexpand(True)
    sidebar_scrolled.set_child(sidebar_navigation)
    sidebar_box.append(sidebar_scrolled)

    split_view.set_sidebar(sidebar_box)

    # Main Content Area
    content_toolbar_view = Adw.ToolbarView()
    content_header = Adw.HeaderBar()
    content_header.add_css_class("main-header")

    # Toggle sidebar button
    app.btn_sidebar = Gtk.ToggleButton(icon_name="sidebar-show-symbolic")
    app.btn_sidebar.set_active(True)
    app.btn_sidebar.set_tooltip_text("Toggle Sidebar")
    app.btn_sidebar.connect("toggled", lambda b: split_view.set_show_sidebar(b.get_active()))
    content_header.pack_start(app.btn_sidebar)

    split_view.bind_property("show-sidebar", app.btn_sidebar, "active", GObject.BindingFlags.BIDIRECTIONAL)

    # Title widget
    app.window_title = Adw.WindowTitle()
    app.window_title.set_title("System Dashboard")
    app.window_title.set_subtitle(f"{app.current_stats.get('username', 'user')}@{app.current_stats.get('hostname', 'host')}")
    content_header.set_title_widget(app.window_title)

    def update_header_title(stack, _paramspec):
        child = stack.get_visible_child()
        if child:
            name = child.get_name()
            title = ""
            if hasattr(child, "get_title"):
                title = child.get_title()
            if title == "Dashboard" or name == "dashboard":
                title = "System Dashboard"
            elif title == "Overview" or name == "overview":
                title = "System Information"
            app.window_title.set_title(title)

            # Show copy and screenshot only on overview page
            is_overview = (name == "overview")
            if hasattr(app, "btn_copy") and app.btn_copy:
                app.btn_copy.set_visible(is_overview)
            if hasattr(app, "btn_screenshot") and app.btn_screenshot:
                app.btn_screenshot.set_visible(is_overview)
            
    view_stack.connect("notify::visible-child", update_header_title)

    content_header.pack_end(app.btn_refresh)
    content_toolbar_view.add_top_bar(content_header)
    content_toolbar_view.set_content(view_stack)

    # Bottom Action Bar
    action_bar = Gtk.ActionBar()
    action_bar.add_css_class("preset-row")

    btn_copy = Gtk.Button(label="📋 Copy Fetch Text")
    btn_copy.add_css_class("preset-btn")
    btn_copy.add_css_class("btn-power-saving")
    btn_copy.set_tooltip_text("Copy terminal fastfetch text layout to clipboard")
    btn_copy.connect("clicked", app.on_copy_fetch_clicked)

    btn_screenshot = Gtk.Button(label="📸 Screenshot Overview")
    btn_screenshot.add_css_class("preset-btn")
    btn_screenshot.add_css_class("btn-balance")
    btn_screenshot.set_tooltip_text("Save the system overview card as a PNG image")
    btn_screenshot.connect("clicked", app.on_screenshot_clicked)

    btn_reload = Gtk.Button(label="🔄 Refresh Readings")
    btn_reload.add_css_class("preset-btn")
    btn_reload.add_css_class("btn-max-performance")
    btn_reload.set_tooltip_text("Scan all hardware stats now")
    btn_reload.connect("clicked", app.on_refresh_clicked)
    
    app.btn_copy = btn_copy
    app.btn_screenshot = btn_screenshot
    app.btn_reload = btn_reload

    action_bar.pack_start(btn_copy)
    action_bar.pack_start(btn_screenshot)
    action_bar.pack_end(btn_reload)

    content_toolbar_view.add_bottom_bar(action_bar)
    split_view.set_content(content_toolbar_view)

    # Initial call to apply button visibility rules
    update_header_title(view_stack, None)

    toast_overlay = Adw.ToastOverlay()
    toast_overlay.set_child(split_view)
    win.set_content(toast_overlay)
    app.toast_overlay = toast_overlay

    # Main Application Menu options
    gmenu = Gio.Menu.new()
    
    theme_menu = Gio.Menu.new()
    theme_menu.append("Adwaita Default", "app.theme-color::default")
    theme_menu.append("Ryzen Red", "app.theme-color::ryzen")
    theme_menu.append("DLSS Green", "app.theme-color::geforce")
    theme_menu.append("14nm+++ Blue", "app.theme-color::intel")
    theme_menu.append("Archbtw Blue", "app.theme-color::arch")
    theme_menu.append("Saints Purple", "app.theme-color::saints")
    theme_menu.append("Noctua Brown", "app.theme-color::noctua")

    section_theme = Gio.Menu.new()
    section_theme.append_submenu("Accent Color", theme_menu)
    gmenu.append_section(None, section_theme)

    section1 = Gio.Menu.new()
    section1.append("Refresh Stats", "app.reload")
    gmenu.append_section(None, section1)

    section2 = Gio.Menu.new()
    section2.append("About fetch-gtk", "app.about")
    gmenu.append_section(None, section2)

    app.menu_btn.set_menu_model(gmenu)

    return win
