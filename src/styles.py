"""CSS styles for fetch-gtk UI"""

CSS = """
/* Define theme colors and fallbacks */
@define-color semantic_green #30d158;
@define-color semantic_yellow #ffd60a;
@define-color semantic_red #ff3b30;
@define-color warning_red #e01b24;
@define-color sidebar_bg_color mix(@window_bg_color, @window_fg_color, 0.02);

/* ─── Window & Background ─────────────────────────────────── */
window.fetch-gtk-win {
    background-color: @window_bg_color;
}

/* ─── Header bar premium aesthetics ───────────────────────── */
.main-header {
    background-color: transparent;
    box-shadow: none;
    border-bottom: none;
}

.sidebar-header {
    background-color: transparent;
    box-shadow: none;
    border-bottom: none;
}

/* ─── Fetch Overview Panel (Terminal Style) ────────────────── */
.fetch-container {
    background-color: alpha(@window_fg_color, 0.02);
    border: 1px solid alpha(@window_fg_color, 0.06);
    border-radius: 18px;
    padding: 24px;
    margin-bottom: 16px;
    box-shadow: 0 4px 12px alpha(black, 0.05);
}

.fetch-logo-box {
    margin-right: 24px;
    padding: 8px;
    border-radius: 14px;
    background: radial-gradient(circle at center, alpha(#8bfe98, 0.12) 0%, transparent 80%);
}

.fetch-logo-image {
    -gtk-icon-shadow: 0 8px 24px alpha(#8bfe98, 0.3);
}

.fetch-title {
    font-size: 20px;
    font-weight: 900;
    color: @accent_bg_color;
    letter-spacing: -0.5px;
}

.fetch-separator {
    background-color: alpha(@window_fg_color, 0.15);
    margin: 8px 0 12px 0;
}

.fetch-key {
    font-size: 15px;
    font-weight: 800;
    color: @accent_bg_color;
    margin-right: 12px;
    padding: 2px 0;
}

.fetch-val {
    font-size: 15px;
    color: @window_fg_color;
    padding: 2px 0;
}

/* Color blocks (like terminal colors) */
.color-pill {
    min-width: 24px;
    min-height: 24px;
    border-radius: 50%;
    margin-right: 8px;
    margin-top: 16px;
    border: 1px solid alpha(black, 0.1);
    box-shadow: 0 2px 4px alpha(black, 0.1);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.color-pill:hover {
    transform: scale(1.2);
    box-shadow: 0 4px 8px alpha(black, 0.2);
}

.color-black { background-color: #1e1e2e; }
.color-red { background-color: #f38ba8; }
.color-green { background-color: #a6e3a1; }
.color-yellow { background-color: #f9e2af; }
.color-blue { background-color: #89b4fa; }
.color-magenta { background-color: #f5c2e7; }
.color-cyan { background-color: #89dceb; }
.color-white { background-color: #cdd6f4; }

/* ─── Dashboard Hero Banner ───────────────────────────────── */
.hero-box {
    padding: 24px;
    margin-bottom: 16px;
    background: radial-gradient(circle at top center, alpha(@accent_bg_color, 0.18) 0%, alpha(@accent_bg_color, 0.05) 40%, transparent 100%);
    border-radius: 24px;
    border: 1px solid alpha(@accent_bg_color, 0.15);
}

.hero-icon {
    color: @accent_bg_color;
    -gtk-icon-shadow: 0 0 20px alpha(@accent_bg_color, 0.5);
}

.hero-title {
    font-size: 30px;
    font-weight: 1000;
    letter-spacing: -1.2px;
    color: @window_fg_color;
    text-shadow: 0 2px 4px alpha(black, 0.15);
}

.hero-subtitle {
    font-size: 13px;
    font-weight: 700;
    color: alpha(@window_fg_color, 0.45);
}

.hero-cpu-badge {
    background-color: alpha(@accent_bg_color, 0.1);
    color: @accent_bg_color;
    border: 1px solid alpha(@accent_bg_color, 0.25);
    border-radius: 8px;
    padding: 2px 10px;
    font-weight: 900;
    font-size: 11px;
    margin-left: 8px;
}

.live-status-pill {
    background-color: alpha(@semantic_green, 0.2);
    color: @semantic_green;
    border: 1px solid alpha(@semantic_green, 0.4);
    border-radius: 14px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    animation: status-pulse 2s infinite ease-in-out;
}

@keyframes status-pulse {
    0% {
        background-color: alpha(@semantic_green, 0.2);
        border-color: alpha(@semantic_green, 0.4);
    }
    50% {
        background-color: alpha(@semantic_green, 0.4);
        border-color: alpha(@semantic_green, 0.8);
    }
    100% {
        background-color: alpha(@semantic_green, 0.2);
        border-color: alpha(@semantic_green, 0.4);
    }
}

/* ─── Category Section Headers ────────────────────────────── */
.section-title-box {
    margin-top: 24px;
    margin-bottom: 12px;
    padding: 0 4px;
}

.section-title-label {
    font-size: 15px;
    font-weight: bold;
    color: @window_fg_color;
}

.category-icon {
    color: @accent_bg_color;
    margin-right: 8px;
    -gtk-icon-size: 18px;
}

/* ─── Premium Cards (Glassmorphism) ───────────────────────── */
.monitor-card {
    background-color: alpha(@window_fg_color, 0.03);
    background-image: linear-gradient(145deg, alpha(@window_fg_color, 0.02), transparent);
    border: 1px solid alpha(@window_fg_color, 0.08);
    border-radius: 20px;
    padding: 16px;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    box-shadow: 0 2px 4px alpha(black, 0.03);
}

.monitor-card:hover {
    background-color: alpha(@window_fg_color, 0.06);
    border-color: alpha(@accent_bg_color, 0.35);
    transform: translateY(-4px);
    box-shadow: 0 8px 16px alpha(black, 0.08);
}

.monitor-name-label {
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: alpha(@window_fg_color, 0.45);
}

.monitor-tag-badge {
    font-size: 9.5px;
    font-weight: bold;
    border-radius: 8px;
    padding: 2px 6px;
}

/* Dynamic Badge Colors using theme-defined variables mapping to cpu/gpu badge variables */
.monitor-tag-badge.system {
    color: @cpu_badge_fg;
    background-color: @cpu_badge_bg;
    border: 1px solid alpha(@cpu_badge_fg, 0.4);
}

.monitor-tag-badge.live {
    color: @gpu_badge_fg;
    background-color: @gpu_badge_bg;
    border: 1px solid alpha(@gpu_badge_fg, 0.4);
}

.monitor-tag-badge.energy {
    color: @gpu_badge_fg;
    background-color: @gpu_badge_bg;
    border: 1px solid alpha(@gpu_badge_fg, 0.4);
}

.monitor-tag-badge.perf {
    color: @cpu_badge_fg;
    background-color: @cpu_badge_bg;
    border: 1px solid alpha(@cpu_badge_fg, 0.4);
}

.monitor-value-label {
    font-size: 24px;
    font-weight: 900;
    color: @accent_bg_color;
    font-variant-numeric: tabular-nums;
}

.monitor-unit-label {
    font-size: 12px;
    font-weight: bold;
    color: alpha(@window_fg_color, 0.4);
    margin-bottom: 3px;
}

.monitor-icon {
    color: alpha(@window_fg_color, 0.4);
    margin-right: 6px;
    -gtk-icon-size: 16px;
}

/* ─── Usage Level Bars ────────────────────────────────────── */
progressbar.usage-bar {
    min-height: 8px;
    margin-top: 8px;
    margin-bottom: 4px;
}

progressbar.usage-bar trough {
    border-radius: 4px;
    background-color: alpha(@window_fg_color, 0.06);
    min-height: 8px;
    border: none;
}

progressbar.usage-bar progress {
    border-radius: 4px;
    min-height: 8px;
    border: none;
    transition: background-color 0.4s ease;
}

progressbar.usage-bar.low progress {
    background-color: @semantic_green;
    box-shadow: 0 0 12px alpha(@semantic_green, 0.3);
}

progressbar.usage-bar.medium progress {
    background-color: @semantic_yellow;
    box-shadow: 0 0 12px alpha(@semantic_yellow, 0.3);
}

progressbar.usage-bar.high progress {
    background-color: @semantic_red;
    box-shadow: 0 0 12px alpha(@semantic_red, 0.3);
}

/* ─── Navigation & Sidebar (Ptyxis Style) ────────────────── */
.sidebar-pane {
    background-color: @sidebar_bg_color;
    border-right: 1px solid alpha(@window_fg_color, 0.05);
}

.navigation-sidebar row {
    border-radius: 10px;
    margin: 2px 8px;
    padding: 8px 12px;
    transition: all 0.2s ease;
}

.navigation-sidebar row image {
    -gtk-icon-size: 20px;
    margin-right: 10px;
    color: inherit;
    opacity: 0.7;
    transition: all 0.2s ease;
}

.navigation-sidebar row label {
    font-size: 14px;
    font-weight: 700;
    transition: all 0.2s ease;
}

.navigation-sidebar row:hover {
    background-color: alpha(@window_fg_color, 0.05);
}

.navigation-sidebar row:selected {
    background-color: alpha(@accent_bg_color, 0.12);
    color: @accent_bg_color;
}

.navigation-sidebar row:selected image {
    color: @accent_bg_color;
    opacity: 1.0;
}

/* ─── Preset buttons (Floating Action Feel) ───────────────── */
.preset-row {
    padding: 16px 24px;
    background-color: transparent;
    border: none;
}

.preset-btn {
    border-radius: 28px;
    padding: 10px 28px;
    font-weight: 900;
    font-size: 15px;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    min-height: 48px;
    border: 1px solid transparent;
}

.preset-btn:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px alpha(black, 0.2);
}

.btn-power-saving {
    background-color: alpha(@semantic_green, 0.18);
    color: @semantic_green;
    border-color: alpha(@semantic_green, 0.4);
}

.preset-btn.btn-power-saving:hover {
    background-color: alpha(@semantic_green, 0.3);
    border-color: @semantic_green;
}

.btn-balance {
    background-color: alpha(@semantic_yellow, 0.18);
    color: @semantic_yellow;
    border-color: alpha(@semantic_yellow, 0.4);
}

.preset-btn.btn-balance:hover {
    background-color: alpha(@semantic_yellow, 0.3);
    border-color: @semantic_yellow;
}

.btn-max-performance {
    background-color: alpha(@semantic_red, 0.18);
    color: @semantic_red;
    border-color: alpha(@semantic_red, 0.4);
}

.preset-btn.btn-max-performance:hover {
    background-color: alpha(@semantic_red, 0.3);
    border-color: @semantic_red;
}
"""
