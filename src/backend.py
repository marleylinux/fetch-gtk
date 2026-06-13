"""System information and telemetry retrieval for fetch-gtk"""
import os
import re
import socket
import platform
import subprocess
import logging

log = logging.getLogger(__name__)

def get_os_info() -> dict:
    """Read distro name and details from /etc/os-release"""
    info = {
        "name": "Linux",
        "version": "",
        "pretty_name": "Linux",
        "logo": "linux",
        "id": "linux"
    }
    if os.path.exists("/etc/os-release"):
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if "=" in line:
                        k, v = line.strip().split("=", 1)
                        v = v.strip('"\'')
                        if k == "NAME":
                            info["name"] = v
                        elif k == "VERSION":
                            info["version"] = v
                        elif k == "PRETTY_NAME":
                            info["pretty_name"] = v
                        elif k == "LOGO":
                            info["logo"] = v
                        elif k == "ID":
                            info["id"] = v
        except Exception as e:
            log.debug("Failed to parse /etc/os-release: %s", e)
    return info

def get_host_info() -> str:
    """Get the machine model name from sysfs DMI data"""
    # 1. Try DMI product name + version
    product = None
    version = None
    try:
        if os.path.exists("/sys/devices/virtual/dmi/id/product_name"):
            with open("/sys/devices/virtual/dmi/id/product_name", "r") as f:
                product = f.read().strip()
        if os.path.exists("/sys/devices/virtual/dmi/id/product_version"):
            with open("/sys/devices/virtual/dmi/id/product_version", "r") as f:
                version = f.read().strip()
    except Exception:
        pass

    if product and product not in ("System Product Name", "To Be Filled By O.E.M."):
        if version and version not in ("System Version", "To Be Filled By O.E.M.", "None"):
            return f"{product} ({version})"
        return product

    # 2. Try Device Tree model (useful for Raspberry Pi, etc.)
    try:
        dt_path = "/sys/firmware/devicetree/base/model"
        if os.path.exists(dt_path):
            with open(dt_path, "r") as f:
                return f.read().strip().replace("\x00", "")
    except Exception:
        pass

    # 3. Fallback
    return platform.node() or "Generic Hardware"

def get_uptime_raw() -> float:
    """Get system uptime in seconds"""
    try:
        with open("/proc/uptime", "r") as f:
            return float(f.readline().split()[0])
    except Exception:
        return 0.0

def get_uptime_str() -> str:
    """Get system uptime formatted as a human readable string"""
    seconds = get_uptime_raw()
    if seconds <= 0.0:
        return "Unknown"
    
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)

def get_shell() -> str:
    """Get current user shell and version"""
    shell_path = os.environ.get("SHELL")
    if not shell_path:
        try:
            import pwd
            shell_path = pwd.getpwuid(os.getuid()).pw_shell
        except Exception:
            shell_path = "/bin/sh"
            
    shell_name = os.path.basename(shell_path)
    
    # Try getting the version
    version = ""
    try:
        res = subprocess.run([shell_path, "--version"], capture_output=True, text=True, timeout=0.1)
        output = res.stdout.strip() or res.stderr.strip()
        # Find first number sequence like 5.2.15 or 5.9
        match = re.search(r"\d+\.\d+(\.\d+)?", output)
        if match:
            version = match.group(0)
    except Exception:
        pass
        
    if version:
        return f"{shell_name} {version}"
    return shell_name

def get_de_wm() -> tuple[str, str]:
    """Detect Desktop Environment and Window Manager"""
    de = os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("DESKTOP_SESSION") or ""
    # Clean up DE names (e.g. GNOME, KDE, MATE)
    de = de.upper()
    if "GNOME" in de:
        de = "GNOME"
    elif "KDE" in de or "PLASMA" in de:
        de = "KDE Plasma"
    elif "XFCE" in de:
        de = "XFCE"
    elif "MATE" in de:
        de = "MATE"
    elif "CINNAMON" in de:
        de = "Cinnamon"
    elif not de:
        de = "Unknown DE"

    # Identify Window Manager
    wm = "Unknown WM"
    # Look through running processes for known WMs
    try:
        processes = []
        for pid_str in os.listdir("/proc"):
            if pid_str.isdigit():
                try:
                    with open(f"/proc/{pid_str}/comm", "r") as f:
                        processes.append(f.read().strip().lower())
                except Exception:
                    pass
        
        known_wms = {
            "mutter": "Mutter",
            "kwin_wayland": "KWin (Wayland)",
            "kwin_x11": "KWin (X11)",
            "kwin": "KWin",
            "sway": "Sway",
            "hyprland": "Hyprland",
            "i3": "i3wm",
            "bspwm": "bspwm",
            "awesome": "AwesomeWM",
            "openbox": "Openbox",
            "xfwm4": "Xfwm4",
            "compiz": "Compiz",
            "fluxbox": "Fluxbox",
            "dwm": "dwm",
            "weston": "Weston"
        }
        for proc in processes:
            if proc in known_wms:
                wm = known_wms[proc]
                break
    except Exception:
        pass

    # Simple session type detection
    session_type = os.environ.get("XDG_SESSION_TYPE")
    if session_type:
        session_type = session_type.capitalize()
        if wm != "Unknown WM" and session_type not in wm:
            wm = f"{wm} ({session_type})"
            
    return de, wm

def count_packages() -> str:
    """Count installed packages for common package managers"""
    counts = []
    
    # 1. Pacman (Arch)
    if os.path.exists("/var/lib/pacman/local"):
        try:
            # Each folder is an installed package
            dirs = [d for d in os.listdir("/var/lib/pacman/local") if not d.startswith(".")]
            counts.append(f"{len(dirs)} (pacman)")
        except Exception:
            pass
            
    # 2. Dpkg/Apt (Debian/Ubuntu)
    if os.path.exists("/var/lib/dpkg/status"):
        try:
            count = 0
            with open("/var/lib/dpkg/status", "r") as f:
                for line in f:
                    if line.startswith("Package: "):
                        count += 1
            if count > 0:
                counts.append(f"{count} (dpkg)")
        except Exception:
            pass

    # 3. RPM (Fedora/RHEL)
    if os.path.exists("/var/lib/rpm"):
        try:
            # We can count files in /var/lib/rpm or run rpm -qa (latter is slower but accurate, let's try direct counting or check if rpm binary is there)
            res = subprocess.run(["rpm", "-qa"], capture_output=True, text=True, timeout=0.2)
            if res.returncode == 0:
                count = len(res.stdout.strip().splitlines())
                if count > 0:
                    counts.append(f"{count} (rpm)")
        except Exception:
            pass

    # 4. Flatpak
    flatpak_count = 0
    sys_flatpak = "/var/lib/flatpak/app"
    user_flatpak = os.path.expanduser("~/.local/share/flatpak/app")
    if os.path.exists(sys_flatpak):
        try:
            flatpak_count += len(os.listdir(sys_flatpak))
        except Exception:
            pass
    if os.path.exists(user_flatpak):
        try:
            flatpak_count += len(os.listdir(user_flatpak))
        except Exception:
            pass
    if flatpak_count > 0:
        counts.append(f"{flatpak_count} (flatpak)")

    # 5. Snap
    snap_dir = "/var/lib/snapd/snaps"
    if os.path.exists(snap_dir):
        try:
            # count files ending in .snap
            snaps = [f for f in os.listdir(snap_dir) if f.endswith(".snap")]
            if snaps:
                counts.append(f"{len(snaps)} (snap)")
        except Exception:
            pass

    if not counts:
        return "Unknown"
    return ", ".join(counts)

def get_terminal() -> str:
    """Find the name of the parent terminal emulator process"""
    try:
        ppid = os.getppid()
        # Traversal up to 10 parent levels to find the terminal
        visited = set()
        for _ in range(10):
            if ppid in visited or ppid <= 1:
                break
            visited.add(ppid)
            
            comm_path = f"/proc/{ppid}/comm"
            if not os.path.exists(comm_path):
                break
                
            with open(comm_path, "r") as f:
                comm = f.read().strip()
                
            # If the process is a shell, python runner or sudo, we traverse up
            if comm in ("bash", "zsh", "fish", "sh", "python3", "python", "sudo", "app.py"):
                # Read parent pid
                status_path = f"/proc/{ppid}/status"
                if os.path.exists(status_path):
                    with open(status_path, "r") as f:
                        for line in f:
                            if line.startswith("PPid:"):
                                ppid = int(line.split()[1])
                                break
                else:
                    break
            else:
                # Format common names nicely
                nicenames = {
                    "ptyxis": "Ptyxis",
                    "gnome-terminal-": "GNOME Terminal",
                    "gnome-terminal": "GNOME Terminal",
                    "kitty": "Kitty",
                    "alacritty": "Alacritty",
                    "konsole": "Konsole",
                    "wezterm-gui": "WezTerm",
                    "wezterm": "WezTerm",
                    "foot": "Foot",
                    "xfce4-terminal": "XFCE Terminal",
                    "xterm": "Xterm",
                    "termite": "Termite",
                    "tilix": "Tilix",
                    "deepin-terminal": "Deepin Terminal"
                }
                comm_lower = comm.lower()
                for k, v in nicenames.items():
                    if k in comm_lower:
                        return v
                return comm.capitalize()
    except Exception:
        pass
    return os.environ.get("TERM", "Unknown Terminal")

def get_cpu_info() -> dict:
    """Get detailed CPU name and core layout info"""
    cpu = {
        "model": "Unknown CPU",
        "cores_logical": os.cpu_count() or 1,
        "cores_physical": 1
    }
    
    # Try reading /proc/cpuinfo
    if os.path.exists("/proc/cpuinfo"):
        try:
            core_ids = set()
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line and cpu["model"] == "Unknown CPU":
                        name = line.split(":", 1)[1].strip()
                        # Clean up common fluff
                        name = name.replace("(R)", "").replace("(TM)", "")
                        name = name.replace("Processor", "").replace("CPU", "")
                        name = re.sub(r"\s+", " ", name)
                        cpu["model"] = name.strip()
                    elif "core id" in line:
                        core_ids.add(line.split(":", 1)[1].strip())
            if core_ids:
                cpu["cores_physical"] = len(core_ids)
            else:
                cpu["cores_physical"] = cpu["cores_logical"]
        except Exception:
            pass
            
    if cpu["model"] == "Unknown CPU":
        cpu["model"] = platform.processor() or "Generic Processor"
        
    return cpu

def get_gpus() -> list[str]:
    """Get active graphics cards"""
    gpus = []
    
    # 1. Try lspci (standard and robust)
    try:
        res = subprocess.run(["lspci"], capture_output=True, text=True, timeout=0.2)
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                if "VGA compatible controller" in line or "3D controller" in line or "Display controller" in line:
                    parts = line.split(":", 2)
                    if len(parts) >= 3:
                        gpu_name = parts[2].strip()
                        # Clean up vendors
                        gpu_name = re.sub(r"\[AMD/ATI\]", "", gpu_name)
                        gpu_name = re.sub(r"Corporation", "", gpu_name)
                        gpu_name = re.sub(r"Technologies Inc", "", gpu_name)
                        gpu_name = gpu_name.replace("Advanced Micro Devices, Inc. ", "")
                        gpu_name = gpu_name.replace("Intel ", "").replace("NVIDIA ", "")
                        # Remove revision ID at end (rev 0c)
                        gpu_name = re.sub(r"\(rev \w+\)", "", gpu_name)
                        gpu_name = re.sub(r"\s+", " ", gpu_name).strip()
                        if gpu_name:
                            gpus.append(gpu_name)
    except Exception:
        pass
        
    # 2. Fallback to /sys/class/drm/
    if not gpus and os.path.exists("/sys/class/drm"):
        try:
            for card in sorted(os.listdir("/sys/class/drm")):
                if card.startswith("card") and "-" not in card:
                    # Check uevent or name
                    uevent_path = f"/sys/class/drm/{card}/device/uevent"
                    if os.path.exists(uevent_path):
                        with open(uevent_path, "r") as f:
                            content = f.read()
                        match = re.search(r"PCI_SLOT_NAME=(.+)", content)
                        if match:
                            gpus.append(f"GPU (PCI {match.group(1)})")
        except Exception:
            pass
            
    if not gpus:
        gpus.append("Software Rasterizer / Unknown GPU")
        
    # Deduplicate while preserving order
    seen = set()
    return [x for x in gpus if not (x in seen or seen.add(x))]

def get_memory_info() -> tuple[float, float, float]:
    """Get RAM details: (used_gb, total_gb, percent)"""
    total = 0.0
    available = 0.0
    if os.path.exists("/proc/meminfo"):
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        total = float(line.split()[1]) * 1024 # KiB to Bytes
                    elif line.startswith("MemAvailable:"):
                        available = float(line.split()[1]) * 1024 # KiB to Bytes
        except Exception:
            pass
            
    if total <= 0.0:
        return 0.0, 0.0, 0.0
        
    used = total - available
    percent = (used / total) * 100.0
    
    # Convert to GiB
    gib = 1024 ** 3
    return used / gib, total / gib, percent

def get_disk_info() -> tuple[float, float, float]:
    """Get Root disk space: (used_gb, total_gb, percent)"""
    try:
        stat = os.statvfs("/")
        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bfree * stat.f_frsize
        avail = stat.f_bavail * stat.f_frsize
        used = total - free
        
        total_gb = total / (1024 ** 3)
        used_gb = used / (1024 ** 3)
        percent = (used / (used + avail)) * 100.0 if (used + avail) > 0 else 0.0
        return used_gb, total_gb, percent
    except Exception:
        return 0.0, 0.0, 0.0

def get_battery_info() -> tuple[int | None, str]:
    """Get battery capacity percentage and status"""
    power_path = "/sys/class/power_supply"
    if os.path.exists(power_path):
        try:
            for supply in os.listdir(power_path):
                if supply.startswith("BAT"):
                    cap_path = f"{power_path}/{supply}/capacity"
                    stat_path = f"{power_path}/{supply}/status"
                    if os.path.exists(cap_path):
                        with open(cap_path, "r") as f:
                            cap = int(f.read().strip())
                        status = "Unknown"
                        if os.path.exists(stat_path):
                            with open(stat_path, "r") as f:
                                status = f.read().strip()
                        return cap, status
        except Exception:
            pass
    return None, "No Battery"

def get_local_ip() -> str:
    """Find local IP address using socket routing lookup"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # doesn't connect, just registers routing path
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def get_live_cpu_utilization() -> tuple[float, float]:
    """Read raw CPU tick counters from /proc/stat as (idle, total).

    Returns raw idle and total tick counts. Caller must diff between two
    successive readings to derive a utilization percentage.
    """
    try:
        with open("/proc/stat", "r") as f:
            line = f.readline()
        if line.startswith("cpu "):
            parts = [float(x) for x in line.split()[1:]]
            idle = parts[3] + parts[4]
            total = sum(parts)
            return idle, total
    except Exception:
        pass
    return 0.0, 0.0

def get_cpu_temp() -> float | None:
    """Read CPU temperature from hwmon"""
    try:
        hwmon = "/sys/class/hwmon"
        if os.path.exists(hwmon):
            for hdir in sorted(os.listdir(hwmon)):
                base = f"{hwmon}/{hdir}"
                name_path = f"{base}/name"
                if os.path.exists(name_path):
                    with open(name_path, "r") as f:
                        name = f.read().strip()
                    # coretemp (Intel), k10temp (AMD), zenpower (AMD)
                    if name in ("coretemp", "k10temp", "zenpower", "acpitz"):
                        # search for temp*_input
                        for file in os.listdir(base):
                            if file.endswith("_input") and file.startswith("temp"):
                                with open(f"{base}/{file}", "r") as f:
                                    temp_raw = float(f.read().strip())
                                return temp_raw / 1000.0
    except Exception:
        pass
    return None

def get_live_cpu_clocks() -> list[float]:
    """Read frequencies of all CPU cores in MHz"""
    freqs = []
    try:
        base_dir = "/sys/devices/system/cpu"
        if os.path.exists(base_dir):
            cpu_dirs = sorted(
                [d for d in os.listdir(base_dir) if re.match(r"^cpu\d+$", d)],
                key=lambda x: int(x[3:])
            )
            for cpu in cpu_dirs:
                path = f"{base_dir}/{cpu}/cpufreq/scaling_cur_freq"
                if os.path.exists(path):
                    try:
                        with open(path, "r") as f:
                            khz = float(f.read().strip())
                            freqs.append(khz / 1000.0)
                    except Exception:
                        pass
    except Exception:
        pass
        
    if not freqs:
        # Fallback to /proc/cpuinfo
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if line.strip().startswith("cpu MHz"):
                        try:
                            mhz = float(line.split(":", 1)[1].strip())
                            freqs.append(mhz)
                        except ValueError:
                            pass
        except Exception:
            pass
    return freqs

def get_swap_info() -> tuple[float, float, float]:
    """Get swap usage: (used_gb, total_gb, percent)"""
    total = 0.0
    free = 0.0
    if os.path.exists("/proc/meminfo"):
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("SwapTotal:"):
                        total = float(line.split()[1]) * 1024 # KiB to Bytes
                    elif line.startswith("SwapFree:"):
                        free = float(line.split()[1]) * 1024 # KiB to Bytes
        except Exception:
            pass
    if total <= 0.0:
        return 0.0, 0.0, 0.0
    used = total - free
    percent = (used / total) * 100.0
    gib = 1024 ** 3
    return used / gib, total / gib, percent

def get_cpu_governor_driver() -> tuple[str, str]:
    """Read CPU governor and driver name"""
    gov = "Unknown"
    driver = "Unknown"
    try:
        gov_path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
        driver_path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver"
        if os.path.exists(gov_path):
            with open(gov_path, "r") as f:
                gov = f.read().strip()
        if os.path.exists(driver_path):
            with open(driver_path, "r") as f:
                driver = f.read().strip()
    except Exception:
        pass
    return gov, driver

def get_disk_models() -> list[str]:
    """Find active disk models and partition types"""
    models = []
    try:
        block_dir = "/sys/block"
        if os.path.exists(block_dir):
            for dev in os.listdir(block_dir):
                if dev.startswith("sd") or dev.startswith("nvme"):
                    model_path = f"{block_dir}/{dev}/device/model"
                    size_path = f"{block_dir}/{dev}/size"
                    rotational_path = f"{block_dir}/{dev}/queue/rotational"
                    
                    model_name = ""
                    if os.path.exists(model_path):
                        with open(model_path, "r") as f:
                            model_name = f.read().strip()
                            # Clean up common fluff to prevent text overflow
                            model_name = model_name.replace("SSD", "").replace("Solid State Drive", "")
                            model_name = re.sub(r"\s+", " ", model_name).strip()
                            if len(model_name) > 25:
                                model_name = model_name[:22] + ".."
                    else:
                        model_name = dev.upper()
                        
                    is_ssd = "SSD"
                    if os.path.exists(rotational_path):
                        with open(rotational_path, "r") as f:
                            is_ssd = "HDD" if f.read().strip() == "1" else "SSD"
                            
                    size_gb = 0.0
                    if os.path.exists(size_path):
                        try:
                            with open(size_path, "r") as f:
                                size_gb = (float(f.read().strip()) * 512) / (1024 ** 3)
                        except Exception:
                            pass
                            
                    if size_gb > 0.1:
                        models.append(f"{model_name} ({size_gb:.0f}GB {is_ssd})")
    except Exception:
        pass
    return models if models else ["Generic Drive"]

def get_network_io() -> tuple[str, float, float]:
    """Find active network interface, downloaded & uploaded bytes in MB since boot"""
    active_iface = "None"
    rx_mb = 0.0
    tx_mb = 0.0
    try:
        if os.path.exists("/proc/net/dev"):
            with open("/proc/net/dev", "r") as f:
                lines = f.readlines()
            
            max_bytes = 0
            for line in lines[2:]:
                if ":" not in line:
                    continue
                iface, data = line.split(":", 1)
                iface = iface.strip()
                if iface == "lo":
                    continue
                parts = data.split()
                if len(parts) >= 9:
                    try:
                        rx = int(parts[0])
                        tx = int(parts[8])
                        total = rx + tx
                        if total > max_bytes:
                            max_bytes = total
                            active_iface = iface
                            rx_mb = rx / (1024 ** 2)
                            tx_mb = tx / (1024 ** 2)
                    except ValueError:
                        pass
    except Exception:
        pass
    return active_iface, rx_mb, tx_mb

def get_process_count() -> int:
    """Count running user processes"""
    count = 0
    try:
        for pid in os.listdir("/proc"):
            if pid.isdigit():
                count += 1
    except Exception:
        pass
    return count

def get_load_average() -> str:
    """Read load averages"""
    try:
        with open("/proc/loadavg", "r") as f:
            return ", ".join(f.read().split()[:3])
    except Exception:
        return "Unknown"

def get_all_system_stats() -> dict:
    """Collect all basic fetch metrics at once"""
    os_info = get_os_info()
    de, wm = get_de_wm()
    cpu = get_cpu_info()
    gpus = get_gpus()
    used_mem, total_mem, mem_pct = get_memory_info()
    used_disk, total_disk, disk_pct = get_disk_info()
    bat_pct, bat_status = get_battery_info()
    
    # Extra Telemetry
    swap_used, swap_total, swap_pct = get_swap_info()
    gov, driver = get_cpu_governor_driver()
    disks = get_disk_models()
    net_iface, net_rx, net_tx = get_network_io()
    proc_count = get_process_count()
    load_avg = get_load_average()
    
    return {
        "username": os.environ.get("USER") or os.environ.get("LOGNAME") or "user",
        "hostname": socket.gethostname() or "localhost",
        "os_pretty": os_info["pretty_name"],
        "os_id": os_info["id"],
        "os_logo": os_info["logo"],
        "host": get_host_info(),
        "kernel": platform.release(),
        "arch": platform.machine(),
        "uptime": get_uptime_str(),
        "packages": count_packages(),
        "shell": get_shell(),
        "de": de,
        "wm": wm,
        "terminal": get_terminal(),
        "cpu_model": cpu["model"],
        "cpu_cores_logical": cpu["cores_logical"],
        "cpu_cores_physical": cpu["cores_physical"],
        "gpus": gpus,
        "mem_used": used_mem,
        "mem_total": total_mem,
        "mem_pct": mem_pct,
        "disk_used": used_disk,
        "disk_total": total_disk,
        "disk_pct": disk_pct,
        "battery_pct": bat_pct,
        "battery_status": bat_status,
        "local_ip": get_local_ip(),
        
        # New Telemetry data fields
        "swap_used": swap_used,
        "swap_total": swap_total,
        "swap_pct": swap_pct,
        "cpu_governor": gov,
        "cpu_driver": driver,
        "disks": disks,
        "net_interface": net_iface,
        "net_rx": net_rx,
        "net_tx": net_tx,
        "process_count": proc_count,
        "load_avg": load_avg
    }
