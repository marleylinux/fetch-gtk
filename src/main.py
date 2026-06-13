"""Main coordinator and state manager for fetch-gtk"""
import os
import json
import logging
import threading
import socket
from gi.repository import Gtk, Adw, Gdk, Gio, GLib, Graphene, GObject

import backend
import styles
import ui as ui_module

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

APP_ID = "com.marley.fetch-gtk"
APP_NAME = "fetch-gtk"
APP_VER = "1.0.1"

class FetchGtkApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self.win = None
        self.css_provider = Gtk.CssProvider()
        self.theme_css_provider = Gtk.CssProvider()
        
        # In-memory stats
        self.current_stats = {}
        self._refreshing = False
        self._timer_id = None
        
        # Idle/Total CPU ticks for live utilization
        self.prev_idle = 0.0
        self.prev_total = 0.0
        
        # User settings
        self.ui_settings = {
            "theme": "default",
            "refresh_interval": 2000,  # ms
            "custom_username": "",
            "custom_hostname": "",
            "show_logo": True,
            "show_palette": True,
            "show_items": {
                "os_pretty": True,
                "host": True,
                "kernel": True,
                "uptime": True,
                "packages": True,
                "shell": True,
                "de": True,
                "wm": True,
                "terminal": True,
                "cpu_model": True,
                "cpu_cores": True,
                "cpu_governor": False,
                "cpu_driver": False,
                "gpus": True,
                "mem_str": True,
                "swap_str": False,
                "disk_str": True,
                "battery_str": True,
                "process_count": False,
                "load_avg": False,
                "local_ip": True
            }
        }
        self._load_ui_settings()

    def _load_ui_settings(self):
        self.ui_config_path = os.path.expanduser("~/.config/fetch-gtk/ui.json")
        if os.path.exists(self.ui_config_path):
            try:
                with open(self.ui_config_path, "r") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        for k, v in loaded.items():
                            if k == "show_items" and isinstance(v, dict):
                                self.ui_settings["show_items"].update(v)
                            else:
                                self.ui_settings[k] = v
            except Exception as e:
                log.warning("Failed to load UI settings: %s", e)

    def _save_ui_settings(self):
        try:
            os.makedirs(os.path.dirname(self.ui_config_path), exist_ok=True)
            with open(self.ui_config_path, "w") as f:
                json.dump(self.ui_settings, f)
        except Exception as e:
            log.error("Failed to save UI settings: %s", e)

    # ── Application lifecycle ──────────────────────────────────────────────────

    def do_activate(self) -> None:
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.PREFER_DARK)

        # Load styles.CSS
        self.css_provider.load_from_data(styles.CSS.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        # Load dynamic theme provider
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self.theme_css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER,
        )

        # Load initial stats synchronously or default them so UI compiles
        self._load_default_stats()

        # Register actions
        self._register_actions()

        # Build main window
        self.win = ui_module.build_main_window(self)
        self.win.set_icon_name(APP_ID)

        GLib.set_prgname(APP_ID)
        GLib.set_application_name(APP_NAME)

        self.win.present()

        # Load actual stats asynchronously in background to prevent UI lag on startup
        self._do_initial_load_async()

    def _load_default_stats(self):
        """Temporary stats to show during startup compilation"""
        self.current_stats = {
            "username": os.environ.get("USER", "user"),
            "hostname": socket.gethostname(),
            "os_pretty": "Linux",
            "os_id": "linux",
            "os_logo": "linux",
            "host": "Generic PC",
            "kernel": "Loading...",
            "arch": "x86_64",
            "uptime": "Loading...",
            "packages": "Loading...",
            "shell": "Loading...",
            "de": "Loading...",
            "wm": "Loading...",
            "terminal": "Loading...",
            "cpu_model": "Loading CPU...",
            "cpu_cores_logical": 4,
            "cpu_cores_physical": 2,
            "gpus": ["Loading GPU..."],
            "mem_used": 0.0,
            "mem_total": 16.0,
            "mem_pct": 0.0,
            "disk_used": 0.0,
            "disk_total": 256.0,
            "disk_pct": 0.0,
            "battery_pct": 100,
            "battery_status": "Unknown",
            "local_ip": "127.0.0.1",
            
            # Dashboard values
            "swap_used": 0.0,
            "swap_total": 4.0,
            "swap_pct": 0.0,
            "cpu_governor": "Unknown",
            "cpu_driver": "Unknown",
            "disks": ["Generic SSD"],
            "net_interface": "None",
            "net_rx": 0.0,
            "net_tx": 0.0,
            "process_count": 0,
            "load_avg": "0.0 0.0 0.0"
        }

    def _do_initial_load_async(self):
        if self._refreshing:
            return
        self._refreshing = True
        
        def fetch():
            try:
                stats = backend.get_all_system_stats()
                GLib.idle_add(self._on_initial_load_done, stats)
            except Exception as e:
                log.error("Failed to load telemetry stats: %s", e)
                self._refreshing = False
                
        threading.Thread(target=fetch, daemon=True).start()

    def _on_initial_load_done(self, stats: dict):
        self.current_stats.update(stats)
        self._refreshing = False
        
        # Populate UI details
        self._update_ui_values()
        
        # Initialize CPU utilization ticks
        idle, total = backend.get_live_cpu_utilization()
        self.prev_idle = idle
        self.prev_total = total
        
        # Start telemetry loop
        self._start_telemetry_loop()

    def get_formatted_stat(self, key: str) -> str:
        """Helper to format stats neatly for the fetch lists"""
        if key == "mem_str":
            used = self.current_stats.get("mem_used", 0.0)
            total = self.current_stats.get("mem_total", 0.0)
            pct = self.current_stats.get("mem_pct", 0.0)
            return f"{used:.1f} GiB / {total:.1f} GiB ({int(pct)}%)"
        elif key == "disk_str":
            used = self.current_stats.get("disk_used", 0.0)
            total = self.current_stats.get("disk_total", 0.0)
            pct = self.current_stats.get("disk_pct", 0.0)
            return f"{used:.1f} GiB / {total:.1f} GiB ({int(pct)}%)"
        elif key == "battery_str":
            pct = self.current_stats.get("battery_pct")
            status = self.current_stats.get("battery_status", "No Battery")
            if pct is not None:
                return f"{pct}% ({status})"
            return status
        elif key == "gpus":
            gpus = self.current_stats.get("gpus", [])
            return ", ".join(gpus) if gpus else "Unknown GPU"
        elif key == "cpu_cores":
            phys = self.current_stats.get("cpu_cores_physical", 1)
            logi = self.current_stats.get("cpu_cores_logical", 1)
            return f"{phys} Cores / {logi} Threads"
        elif key == "swap_str":
            used = self.current_stats.get("swap_used", 0.0)
            total = self.current_stats.get("swap_total", 0.0)
            pct = self.current_stats.get("swap_pct", 0.0)
            return f"{used:.1f} GiB / {total:.1f} GiB ({int(pct)}%)"
        
        return str(self.current_stats.get(key, "Unknown"))

    def _update_ui_values(self):
        """Redraw all overview fetch labels and appearance rows"""
        usr = self.ui_settings.get("custom_username") or self.current_stats.get("username", "user")
        host = self.ui_settings.get("custom_hostname") or self.current_stats.get("hostname", "host")
        if hasattr(self, "fetch_title") and self.fetch_title:
            self.fetch_title.set_label(f"{usr}@{host}")
            
        if hasattr(self, "window_title") and self.window_title:
            # Update subtitle in header
            self.window_title.set_subtitle(f"{usr}@{host}")

        # Update fetch lists
        rows_def = [
            ("os_pretty", "os_pretty"),
            ("host", "host"),
            ("kernel", "kernel"),
            ("uptime", "uptime"),
            ("packages", "packages"),
            ("shell", "shell"),
            ("de", "de"),
            ("wm", "wm"),
            ("terminal", "terminal"),
            ("cpu_model", "cpu_model"),
            ("cpu_cores", "cpu_cores"),
            ("cpu_governor", "cpu_governor"),
            ("cpu_driver", "cpu_driver"),
            ("gpus", "gpus"),
            ("mem_str", "mem_str"),
            ("swap_str", "swap_str"),
            ("disk_str", "disk_str"),
            ("battery_str", "battery_str"),
            ("process_count", "process_count"),
            ("load_avg", "load_avg"),
            ("local_ip", "local_ip")
        ]
        
        if hasattr(self, "fetch_rows"):
            for row_key, stat_key in rows_def:
                row_widget = self.fetch_rows.get(stat_key)
                if row_widget:
                    val = self.get_formatted_stat(stat_key)
                    row_widget._val_lbl.set_label(val)

        # Update Telemetry Limits & Hero Labels
        if hasattr(self, "hero_subtitle") and self.hero_subtitle:
            self.hero_subtitle.set_text(self.current_stats.get("cpu_model", "CPU"))
            
        if hasattr(self, "card_ram") and self.card_ram:
            self.card_ram._max_limit = self.current_stats.get("mem_total", 16.0)
            self.card_disk._max_limit = self.current_stats.get("disk_total", 256.0)
            
        if hasattr(self, "card_swap") and self.card_swap:
            self.card_swap._max_limit = self.current_stats.get("swap_total", 4.0)

        if hasattr(self, "card_disk_models") and self.card_disk_models:
            disks = self.current_stats.get("disks", [])
            disk_model = disks[0] if disks else "Unknown Storage"
            self.card_disk_models._val_lbl.set_text(disk_model)

        if hasattr(self, "card_cpu_gov") and self.card_cpu_gov:
            gov = self.current_stats.get("cpu_governor", "Unknown")
            driver = self.current_stats.get("cpu_driver", "Unknown")
            self.card_cpu_gov._val_lbl.set_text(f"{driver} ({gov})")

    # ── Telemetry Refresh Loop ─────────────────────────────────────────────────

    def _start_telemetry_loop(self):
        if self._timer_id is not None:
            GLib.source_remove(self._timer_id)
            self._timer_id = None
            
        interval = self.ui_settings.get("refresh_interval", 2000)
        if interval > 0:
            self._timer_id = GLib.timeout_add(interval, self._on_telemetry_tick)

    def _on_telemetry_tick(self) -> bool:
        """Fires at periodic intervals to read live hardware state from sysfs/proc."""
        try:
            # 1. CPU frequency
            clocks = backend.get_live_cpu_clocks()
            avg_clock = sum(clocks) / len(clocks) / 1000.0 if clocks else None # Convert MHz to GHz
            
            # 2. CPU load percentage
            idle, total = backend.get_live_cpu_utilization()
            cpu_util = 0.0
            diff_total = total - self.prev_total
            if diff_total > 0.0:
                diff_idle = idle - self.prev_idle
                cpu_util = (1.0 - (diff_idle / diff_total)) * 100.0
            self.prev_idle = idle
            self.prev_total = total
            
            # 3. CPU Temp
            temp = backend.get_cpu_temp()
            
            # 4. RAM Usage
            used_mem, total_mem, mem_pct = backend.get_memory_info()
            
            # 5. Disk Usage
            used_disk, total_disk, disk_pct = backend.get_disk_info()
            
            # 6. Battery Status
            bat_pct, bat_status = backend.get_battery_info()
            
            # 7. Uptime
            uptime_str = backend.get_uptime_str()
            
            # 8. Extra Dashboard stats
            swap_used, swap_total, swap_pct = backend.get_swap_info()
            net_iface, net_rx, net_tx = backend.get_network_io()
            load_avg = backend.get_load_average()
            proc_count = backend.get_process_count()
            gov, driver = backend.get_cpu_governor_driver()
            
            # Save into current stats
            self.current_stats.update({
                "mem_used": used_mem,
                "mem_total": total_mem,
                "mem_pct": mem_pct,
                "disk_used": used_disk,
                "disk_total": total_disk,
                "disk_pct": disk_pct,
                "battery_pct": bat_pct,
                "battery_status": bat_status,
                "uptime": uptime_str,
                
                "swap_used": swap_used,
                "swap_total": swap_total,
                "swap_pct": swap_pct,
                "net_interface": net_iface,
                "net_rx": net_rx,
                "net_tx": net_tx,
                "load_avg": load_avg,
                "process_count": proc_count,
                "cpu_governor": gov,
                "cpu_driver": driver
            })

            # Update fetch row uptime
            if hasattr(self, "fetch_rows"):
                upt_row = self.fetch_rows.get("uptime")
                if upt_row:
                    upt_row._val_lbl.set_label(uptime_str)
                bat_row = self.fetch_rows.get("battery_str")
                if bat_row:
                    bat_row._val_lbl.set_label(self.get_formatted_stat("battery_str"))

            # Update Telemetry cards
            if hasattr(self, "card_cpu_clock") and self.card_cpu_clock:
                self.card_cpu_clock._val_lbl.set_text(f"{avg_clock:.2f}" if avg_clock else "—")
                
            if hasattr(self, "card_cpu_temp") and self.card_cpu_temp:
                self.card_cpu_temp._val_lbl.set_text(f"{temp:.1f}" if temp is not None else "—")
                
            if hasattr(self, "card_cpu_load") and self.card_cpu_load:
                self.card_cpu_load.update_val(cpu_util)
                
            if hasattr(self, "card_cpu_gov") and self.card_cpu_gov:
                self.card_cpu_gov._val_lbl.set_text(f"{driver} ({gov})")
                
            if hasattr(self, "card_ram") and self.card_ram:
                self.card_ram._max_limit = total_mem
                self.card_ram.update_val(used_mem)
                
            if hasattr(self, "card_swap") and self.card_swap:
                self.card_swap._max_limit = swap_total
                self.card_swap.update_val(swap_used)
                
            if hasattr(self, "card_disk") and self.card_disk:
                self.card_disk.update_val(used_disk)
                
            if hasattr(self, "card_net_io") and self.card_net_io:
                self.card_net_io._val_lbl.set_text(f"{net_rx:.1f}M Rx / {net_tx:.1f}M Tx")
                self.card_net_io.set_tooltip_text(f"Interface: {net_iface}")
                
            if hasattr(self, "card_processes") and self.card_processes:
                self.card_processes._val_lbl.set_text(str(proc_count))
                
            if hasattr(self, "card_load_avg") and self.card_load_avg:
                self.card_load_avg._val_lbl.set_text(load_avg)
                
            if hasattr(self, "card_battery") and self.card_battery:
                if bat_pct is not None:
                    self.card_battery.update_val(float(bat_pct))
                    self.card_battery._val_lbl.set_text(f"{bat_pct} ({bat_status})")
                else:
                    self.card_battery.update_val(None)
                    self.card_battery._val_lbl.set_text("No Battery")
                    
        except Exception as e:
            log.warning("Telemetry tick update failed: %s", e)
            
        return True # Keep timeout running

    def _register_actions(self) -> None:
        action_reload = Gio.SimpleAction.new("reload", None)
        action_reload.connect("activate", lambda a, p: self.on_refresh_clicked(None))
        self.add_action(action_reload)
        self.set_accels_for_action("app.reload", ["F5"])

        action_about = Gio.SimpleAction.new("about", None)
        action_about.connect("activate", self.on_about_activated)
        self.add_action(action_about)

        # Stateful Theme Color choice action
        initial_theme = self.ui_settings.get("theme", "default")
        action_theme = Gio.SimpleAction.new_stateful(
            "theme-color",
            GLib.VariantType.new("s"),
            GLib.Variant.new_string(initial_theme)
        )
        action_theme.connect("change-state", self.on_theme_color_changed)
        self.add_action(action_theme)

        # Set initial color theme
        self.on_theme_color_changed(action_theme, GLib.Variant.new_string(initial_theme))

    def on_theme_color_changed(self, action, state) -> None:
        action.set_state(state)
        color = state.get_string()

        self.ui_settings["theme"] = color
        self._save_ui_settings()


        theme_palettes = {
            "default": {
                "accent": "@accent_bg_color",
                "cpu_fg": "#4cc9f0", "cpu_bg": "rgba(76, 201, 240, 0.12)",
                "gpu_fg": "#f72585", "gpu_bg": "rgba(247, 37, 133, 0.12)",
            },
            "ryzen": {
                "accent": "#ff3b30",
                "cpu_fg": "#ffd60a", "cpu_bg": "rgba(255, 214, 10, 0.12)",
                "gpu_fg": "#30d158", "gpu_bg": "rgba(48, 209, 88, 0.12)",
            },
            "geforce": {
                "accent": "#76ff03",
                "cpu_fg": "#00e5ff", "cpu_bg": "rgba(0, 229, 255, 0.12)",
                "gpu_fg": "#ff4081", "gpu_bg": "rgba(255, 64, 129, 0.12)",
            },
            "intel": {
                "accent": "#0071e3",
                "cpu_fg": "#ffea00", "cpu_bg": "rgba(255, 234, 0, 0.12)",
                "gpu_fg": "#00ff41", "gpu_bg": "rgba(0, 255, 65, 0.12)",
            },
            "arch": {
                "accent": "#1793d1",
                "cpu_fg": "#bf5af2", "cpu_bg": "rgba(191, 90, 242, 0.12)",
                "gpu_fg": "#ff9f0a", "gpu_bg": "rgba(255, 159, 10, 0.12)",
            },
            "saints": {
                "accent": "#af52de",
                "cpu_fg": "#ff3700", "cpu_bg": "rgba(255, 55, 0, 0.12)",
                "gpu_fg": "#5eebff", "gpu_bg": "rgba(94, 235, 255, 0.12)",
            },
            "noctua": {
                "accent": "#9c6644",
                "cpu_fg": "#e63946", "cpu_bg": "rgba(230, 57, 70, 0.12)",
                "gpu_fg": "#a8dadc", "gpu_bg": "rgba(168, 218, 220, 0.12)",
            }
        }

        palette = theme_palettes.get(color, theme_palettes["default"])
        accent = palette["accent"]

        css_lines = []
        if color != "default":
            css_lines.append(f"@define-color accent_color {accent};")
            css_lines.append(f"@define-color accent_bg_color {accent};")
            css_lines.append("@define-color accent_fg_color #ffffff;")
            css_lines.append(f"@define-color suggested_bg_color {accent};")
            css_lines.append("@define-color suggested_fg_color #ffffff;")
            css_lines.append(f"@define-color selection_bg_color {accent};")
            css_lines.append("@define-color selection_fg_color #ffffff;")

            css_lines.append(".suggested-action { background-color: @accent_bg_color; color: @accent_fg_color; }")
            css_lines.append(".preset-btn { border-color: alpha(@accent_bg_color, 0.3); }")
            css_lines.append(".preset-btn:hover { background-color: alpha(@accent_bg_color, 0.1); border-color: @accent_bg_color; }")

        # Set dynamic color definitions
        css_lines.append(f"@define-color cpu_badge_fg {palette['cpu_fg']};")
        css_lines.append(f"@define-color cpu_badge_bg {palette['cpu_bg']};")
        css_lines.append(f"@define-color gpu_badge_fg {palette['gpu_fg']};")
        css_lines.append(f"@define-color gpu_badge_bg {palette['gpu_bg']};")

        full_css = "\n".join(css_lines)
        self.theme_css_provider.load_from_data(full_css.encode())

    # ── User Interaction Handlers ──────────────────────────────────────────────

    def on_refresh_clicked(self, _button) -> None:
        """Triggered manually by user (F5 or refresh buttons)"""
        self._show_toast("Refreshing system statistics...")
        self._do_initial_load_async()

    def on_refresh_interval_changed(self, combobox) -> None:
        active_id = combobox.get_active_id()
        if active_id:
            val = int(active_id)
            self.ui_settings["refresh_interval"] = val
            self._save_ui_settings()
            self._start_telemetry_loop()
            if val > 0:
                self._show_toast(f"Refresh rate set to {val/1000.0:.1f}s")
            else:
                self._show_toast("Live telemetry paused")

    def _show_toast(self, message: str):
        if hasattr(self, "toast_overlay") and self.toast_overlay:
            toast = Adw.Toast.new(message)
            toast.set_timeout(2)
            self.toast_overlay.add_toast(toast)

    def on_about_activated(self, _action, _param) -> None:
        about = Adw.AboutDialog()
        about.set_application_name(APP_NAME)
        about.set_application_icon(APP_ID)
        about.set_version(APP_VER)
        about.set_developer_name("Marley")
        about.set_website("https://github.com/marleylinux/fetch-gtk")
        about.set_issue_url("https://github.com/marleylinux/fetch-gtk/issues")
        about.set_license_type(Gtk.License.GPL_3_0)
        about.set_comments(
            "A modern, polished GTK4/Libadwaita system fetch display (similar to fastfetch)."
        )
        about.set_developers(["Marley <warburtonmarley@proton.me>"])
        about.present(self.win)

    def on_factory_reset_clicked(self, _btn) -> None:
        dialog = Adw.MessageDialog(
            transient_for=self.win,
            heading="Factory Reset & Wipe?",
            body="This will:\n • Delete all saved settings\n • Restore all default views and telemetries\n\nAre you sure you want to proceed?",
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("reset", "Reset Everything")
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.set_response_appearance("reset", Adw.ResponseAppearance.DESTRUCTIVE)

        def on_response(d, response):
            if response == "reset":
                self._execute_factory_reset()

        dialog.connect("response", on_response)
        dialog.present()

    def _execute_factory_reset(self) -> None:
        try:
            # Delete config file
            if os.path.exists(self.ui_config_path):
                os.remove(self.ui_config_path)
            
            # Reset in-memory settings
            self.ui_settings = {
                "theme": "default",
                "refresh_interval": 2000,
                "custom_username": "",
                "custom_hostname": "",
                "show_logo": True,
                "show_palette": True,
                "show_items": {
                    "os_pretty": True,
                    "host": True,
                    "kernel": True,
                    "uptime": True,
                    "packages": True,
                    "shell": True,
                    "de": True,
                    "wm": True,
                    "terminal": True,
                    "cpu_model": True,
                    "cpu_cores": True,
                    "cpu_governor": False,
                    "cpu_driver": False,
                    "gpus": True,
                    "mem_str": True,
                    "swap_str": False,
                    "disk_str": True,
                    "battery_str": True,
                    "process_count": False,
                    "load_avg": False,
                    "local_ip": True
                }
            }
            
            # Reset settings widgets if they exist
            if hasattr(self, "setting_dropdown") and self.setting_dropdown:
                self.setting_dropdown.set_active_id("2000")
            if hasattr(self, "setting_entry_user") and self.setting_entry_user:
                self.setting_entry_user.set_text("")
            if hasattr(self, "setting_entry_host") and self.setting_entry_host:
                self.setting_entry_host.set_text("")
            if hasattr(self, "setting_switch_logo") and self.setting_switch_logo:
                self.setting_switch_logo.set_active(True)
            if hasattr(self, "setting_switch_palette") and self.setting_switch_palette:
                self.setting_switch_palette.set_active(True)
                
            if hasattr(self, "setting_switches") and self.setting_switches:
                defaults = self.ui_settings["show_items"]
                for key, switch in self.setting_switches.items():
                    switch.set_active(defaults.get(key, True))
                    
            # Refresh overview visibility
            if hasattr(self, "logo_container") and self.logo_container:
                self.logo_container.set_visible(True)
            if hasattr(self, "palette_row") and self.palette_row:
                self.palette_row.set_visible(True)
            if hasattr(self, "fetch_rows") and self.fetch_rows:
                defaults = self.ui_settings["show_items"]
                for key, row in self.fetch_rows.items():
                    row.set_visible(defaults.get(key, True))
            
            # Re-apply theme default
            action_theme = self.lookup_action("theme-color")
            if action_theme:
                self.on_theme_color_changed(action_theme, GLib.Variant.new_string("default"))
            
            # Save settings and refresh
            self._save_ui_settings()
            self._update_ui_values()
            
            self._show_toast("Factory reset completed successfully!")
        except Exception as e:
            log.error("Factory reset failed: %s", e)
            self._show_toast(f"Failed to reset: {e}")

    def on_copy_fetch_clicked(self, _button) -> None:
        """Format the fetch system parameters as terminal fetch text and copy to clipboard"""
        os_id = self.current_stats.get("os_id", "linux")
        
        # Dynamic ASCII mapping based on OS
        ascii_arts = {
            "arch": [
                "    /\\        ",
                "   /  \\       ",
                "  /\\   \\      ",
                " /      \\     ",
                "/   ,,   \\    ",
                "/   |  |   \\   ",
                "/___.'  '.___\\ "
            ],
            "debian": [
                "  _____     ",
                " /  __ \\    ",
                "|  /    |   ",
                "|  \\___/    ",
                " \\          ",
                "  \\____/    ",
                "            "
            ],
            "fedora": [
                "      ______   ",
                "     /  __  \\  ",
                "    /  /  \\  \\ ",
                " ==/  /_  /_ / ",
                "  /  ___/      ",
                " /  /          ",
                "/__/           "
            ],
            "ubuntu": [
                "       _       ",
                "   _  ( )  _   ",
                "  (_\\  |  /_)  ",
                "    \\  |  /    ",
                "  _--`---`---_ ",
                " (_          _)",
                "   --_---_--   "
            ],
            "linux": [
                "   .--.    ",
                "  |o_o |   ",
                "  |:_/ |   ",
                " //   \\ \\  ",
                "(|     | ) ",
                "/'\\_   _/`\\",
                "\\___)=(___)"
            ]
        }
        
        art = ascii_arts.get(os_id, ascii_arts["linux"])
        
        # Telemetry metrics list
        usr = self.ui_settings.get("custom_username") or self.current_stats.get("username", "user")
        host = self.ui_settings.get("custom_hostname") or self.current_stats.get("hostname", "host")
        title_line = f"{usr}@{host}"
        sep_line = "-" * len(title_line)
        
        details = [title_line, sep_line]
        
        text_labels = [
            ("os_pretty", "OS"),
            ("host", "Host"),
            ("kernel", "Kernel"),
            ("uptime", "Uptime"),
            ("packages", "Packages"),
            ("shell", "Shell"),
            ("de", "DE"),
            ("wm", "WM"),
            ("terminal", "Terminal"),
            ("cpu_model", "CPU"),
            ("cpu_cores", "Cores"),
            ("cpu_governor", "CPU Governor"),
            ("cpu_driver", "CPU Driver"),
            ("gpus", "GPU"),
            ("mem_str", "Memory"),
            ("swap_str", "Swap"),
            ("disk_str", "Disk"),
            ("battery_str", "Battery"),
            ("process_count", "Processes"),
            ("load_avg", "Load Average"),
            ("local_ip", "Local IP")
        ]
        
        for key, label in text_labels:
            if self.ui_settings.get("show_items", {}).get(key, True):
                details.append(f"{label}: {self.get_formatted_stat(key)}")
        
        # Stitch them together line-by-line
        merged_lines = []
        max_art_lines = len(art)
        max_details_lines = len(details)
        
        for i in range(max(max_art_lines, max_details_lines)):
            art_part = art[i] if i < max_art_lines else " " * len(art[0])
            detail_part = details[i] if i < max_details_lines else ""
            merged_lines.append(f"{art_part}  {detail_part}")
            
        fetch_txt = "\n".join(merged_lines)
        
        # Copy to default Gdk Clipboard
        display = Gdk.Display.get_default()
        clipboard = display.get_clipboard()
        clipboard.set(GObject.Value(str, fetch_txt))
        
        self._show_toast("Fetch text copied to clipboard!")

    def on_screenshot_clicked(self, _btn) -> None:
        if hasattr(Gtk, "FileDialog"):
            dialog = Gtk.FileDialog()
            dialog.set_title("Save Overview Screenshot")
            dialog.set_initial_name("fetch-gtk-overview.png")
            
            filter_png = Gtk.FileFilter()
            filter_png.set_name("PNG Images")
            filter_png.add_mime_type("image/png")
            filters = Gio.ListStore.new(Gtk.FileFilter)
            filters.append(filter_png)
            dialog.set_filters(filters)
            
            dialog.save(self.win, None, self.on_screenshot_save_done)
        else:
            # Fallback for older GTK versions: Save directly to ~/Pictures or ~/Downloads and notify
            home = os.path.expanduser("~")
            pictures = os.path.join(home, "Pictures")
            downloads = os.path.join(home, "Downloads")
            
            target_dir = pictures if os.path.exists(pictures) else (downloads if os.path.exists(downloads) else home)
            path = os.path.join(target_dir, "fetch-gtk-overview.png")
            
            base, ext = os.path.splitext(path)
            counter = 1
            while os.path.exists(path):
                path = f"{base}_{counter}{ext}"
                counter += 1
                
            self.take_overview_screenshot(path)

    def on_screenshot_save_done(self, dialog, result) -> None:
        try:
            file = dialog.save_finish(result)
            if file:
                path = file.get_path()
                if not path.lower().endswith(".png"):
                    path += ".png"
                self.take_overview_screenshot(path)
        except Exception as e:
            log.debug("Screenshot file selection cancelled: %s", e)

    def take_overview_screenshot(self, path: str) -> None:
        try:
            if not hasattr(self, "fetch_box") or not self.fetch_box:
                self._show_toast("Error: Overview widget not found.")
                return
                
            widget = self.fetch_box
            
            native = widget.get_native()
            if not native:
                self._show_toast("Please select the Overview tab first.")
                return
                
            width = widget.get_width()
            height = widget.get_height()
            if width <= 0 or height <= 0:
                self._show_toast("Please select the Overview tab first to render it.")
                return
                
            # Graphene bounds Rect
            bounds = Graphene.Rect.alloc()
            bounds.init(0, 0, width, height)

            # Create snapshot and render widget
            snapshot = Gtk.Snapshot()

            # Draw a solid background color first (matching system dark/light theme)
            bg_color = Gdk.RGBA()
            success, parsed_color = widget.get_style_context().lookup_color("window_bg_color")
            if success:
                bg_color = parsed_color
                # Force opaque background in case system theme has window transparency/blur enabled
                bg_color.alpha = 1.0
            else:
                is_dark = Adw.StyleManager.get_default().get_dark()
                bg_color.parse("#242424" if is_dark else "#f6f6f6")
            snapshot.append_color(bg_color, bounds)

            Gtk.Widget.do_snapshot(widget, snapshot)
            node = snapshot.to_node()
            if not node:
                self._show_toast("Error: Failed to capture snapshot.")
                return
                
            renderer = native.get_renderer()
            if not renderer:
                self._show_toast("Error: Failed to get renderer.")
                return
            
            texture = renderer.render_texture(node, bounds)
            if not texture:
                self._show_toast("Error: Failed to render texture.")
                return
            texture.save_to_png(path)
            
            self._show_toast(f"Screenshot saved to: {os.path.basename(path)}")
        except Exception as e:
            log.error("Failed to save screenshot: %s", e)
            self._show_toast(f"Screenshot failed: {e}")

