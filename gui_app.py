"""
Module A: UI & User Interface Engine (Premium Obsidian Edition)
Constructs a stunning, high-fidelity native Tkinter desktop interface tailored for accessibility.
Enforces Obsidian Black (#09090b) backdrop, Sleek Velvet Zinc (#18181b) cards,
Vibrant Emerald Mint (#10b981) success indicators, and Radiant Purple (#8b5cf6) accents.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import logging
from typing import Dict, Any, Callable, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GUIApp")

class GradientCanvas(tk.Canvas):
    """
    Custom vertical gradient canvas widget that supports shadow text for accessibility.
    """
    def __init__(self, parent, color1: str, color2: str, text: str = "", font: tuple = ("Segoe UI", 20, "bold"), fg: str = "#8b5cf6", **kwargs):
        super().__init__(parent, highlightthickness=0, bd=0, **kwargs)
        self.color1 = color1
        self.color2 = color2
        self.text_content = text
        self.font = font
        self.fg = fg
        self.text_id = None
        self.shadow_id = None
        self.bind("<Configure>", self._on_configure)

    def _on_configure(self, event=None):
        self.draw_gradient()
        self.draw_text()

    def draw_gradient(self):
        self.delete("gradient")
        width = self.winfo_width()
        height = self.winfo_height()
        if width <= 1 or height <= 1:
            return
            
        r1, g1, b1 = self.hex_to_rgb(self.color1)
        r2, g2, b2 = self.hex_to_rgb(self.color2)
        
        for y in range(height):
            ratio = y / max(height - 1, 1)
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            color = f"#{r:02x}{g:02x}{b:02x}"
            self.create_line(0, y, width, y, tags="gradient", fill=color)
        self.tag_lower("gradient")

    def draw_text(self):
        self.delete("text", "shadow")
        width = self.winfo_width()
        height = self.winfo_height()
        
        # 3D shadow offset
        shadow_offset = 2
        self.create_text(width // 2 + shadow_offset, height // 2 + shadow_offset, text=self.text_content, font=self.font, fill="#050507", tags="shadow")
        self.text_id = self.create_text(width // 2, height // 2, text=self.text_content, font=self.font, fill=self.fg, tags="text")

    @staticmethod
    def hex_to_rgb(hex_str):
        hex_str = hex_str.lstrip('#')
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))


class MedicineAssistantGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("👁️ AI Medicine Assistant - Premium Accessibility Suite")
        self.root.geometry("1240x800")
        
        # High-Fidelity Premium Obsidian Color Palette System
        self.bg_color = "#09090b"          # Obsidian dark backdrop
        self.card_color = "#18181b"        # Velvet Zinc card body
        self.border_color = "#27272a"      # Sleek highlight outline
        self.accent_color = "#8b5cf6"      # Radiant Violet/Purple
        self.hover_color = "#a78bfa"       # Lighter lavender hover
        
        # State Colors
        self.success_color = "#10b981"     # Emerald Green
        self.alert_color = "#f43f5e"       # Vibrant Rose Red
        self.warning_color = "#f59e0b"     # Warm Amber Orange
        
        self.text_color = "#fafafa"        # Clean bright white
        self.muted_color = "#a1a1aa"       # Cool zinc gray
        
        # Legacy compatibility color hooks
        self.green_btn = self.success_color
        self.red_btn = self.alert_color
        self.orange_btn = self.warning_color
        self.border_accent = self.accent_color

        self.root.configure(bg=self.bg_color)

        # Callbacks bound by Orchestrator
        self.capture_callback = None
        self.reset_callback = None
        self.quit_callback = None
        self.ip_connect_callback = None
        self.proceed_callback = None
        self.verify_camera_callback = None
        self.online_search_callback = None
        self.scan_wifi_callback = None
        self.camera_type_change_callback = None

        # Two-Stage Layout Containers
        self.diag_frame = None
        self.main_frame = None

        # Configuration variables
        self.camera_type_var = tk.StringVar(value="local") # "local" or "ip"
        self.usb_index_var = tk.StringVar(value="0")
        self.ip_url_var = tk.StringVar(value="http://192.168.100.67:8080/video")

        # Hardware connection states cache
        self.hardware_states = {
            "mouse": ("CONNECTED", True),
            "speakers": ("CONNECTED", True),
            "camera": ("DISCONNECTED", False)
        }

        self._build_stages()
        self._bind_hotkeys()
        
        # Start status bar pulsing loop
        self.root.after(500, self.pulse_status_bar)
        
        logger.info("Accessibility UI Engine successfully initialized under Velvet-Purple Theme.")

    def _build_stages(self):
        """
        Initializes primary Tkinter layouts.
        """
        # --- Stage 1: Diagnostics Frame ---
        self.diag_frame = tk.Frame(self.root, bg=self.bg_color)
        self.diag_frame.pack(fill=tk.BOTH, expand=True)

        # --- Stage 2: Workspace Frame (Hidden initially) ---
        self.main_frame = tk.Frame(self.root, bg=self.bg_color)

    def _create_premium_button(self, parent, text, bg, fg, command, hover_bg=None, font=("Segoe UI", 11, "bold"), height=2) -> tk.Button:
        """
        Utility to spawn fully padded flat buttons with hover animations and outline glow.
        """
        btn = tk.Button(parent, text=text, font=font, bg=bg, fg=fg, relief=tk.FLAT, bd=0, padx=22, pady=10,
                        activebackground=hover_bg or bg, activeforeground=fg, command=command, cursor="hand2",
                        highlightthickness=1, highlightbackground=bg, highlightcolor=hover_bg or bg)
        
        btn.default_bg = bg
        btn.hover_bg = hover_bg or bg
        
        def on_btn_enter(e):
            if btn.cget("state") == tk.DISABLED:
                return
            btn.configure(bg=btn.hover_bg)
            if btn.hover_bg:
                btn.configure(highlightbackground=btn.hover_bg, highlightcolor=btn.hover_bg)
        def on_btn_leave(e):
            if btn.cget("state") == tk.DISABLED:
                return
            btn.configure(bg=btn.default_bg)
            btn.configure(highlightbackground=btn.default_bg, highlightcolor=btn.default_bg)
            
        btn.bind("<Enter>", on_btn_enter)
        btn.bind("<Leave>", on_btn_leave)
        return btn

    def _bind_hover_glow(self, widget, normal_bg=None, hover_bg=None, normal_border=None, hover_border=None):
        """
        Binds enter/leave events to apply beautiful neon glowing highlights to container frames
        and blends child widgets' background colors recursively for visual excellence.
        """
        def change_bg(w, bg_color):
            if isinstance(w, (tk.Frame, tk.Label, tk.LabelFrame, tk.Radiobutton)):
                try:
                    w.configure(bg=bg_color)
                except Exception:
                    pass
            for child in w.winfo_children():
                change_bg(child, bg_color)

        def on_enter(e):
            if hover_bg:
                change_bg(widget, hover_bg)
            if hover_border:
                try:
                    widget.configure(highlightbackground=hover_border, highlightcolor=hover_border)
                except Exception:
                    pass
        def on_leave(e):
            if normal_bg:
                change_bg(widget, normal_bg)
            if normal_border:
                try:
                    widget.configure(highlightbackground=normal_border, highlightcolor=normal_border)
                except Exception:
                    pass
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        
        def bind_children(w):
            for child in w.winfo_children():
                if not isinstance(child, (tk.Text, tk.Entry, tk.Button)):
                    child.bind("<Enter>", on_enter)
                    child.bind("<Leave>", on_leave)
                    bind_children(child)
        bind_children(widget)

    def pulse_status_bar(self):
        """
        Pulsates the status bar color when in warning, alert or loading states.
        """
        try:
            if hasattr(self, 'status_bar') and self.status_bar.winfo_exists():
                current_text = self.status_bar.cget("text").upper()
                current_bg = self.status_bar.cget("bg")
                
                is_alert = any(kw in current_text for kw in ["ALERT", "FAILED", "REQUIRED", "RESCAN", "ERROR", "WARNING", "OFFLINE"])
                is_loading = any(kw in current_text for kw in ["ANALYZING", "EXTRACTING", "SCANNING", "QUERYING"])
                
                if is_alert:
                    color1 = self.alert_color
                    color2 = "#881337" # Dark crimson
                    new_bg = color2 if current_bg == color1 else color1
                    self.status_bar.configure(bg=new_bg, fg=self.text_color)
                elif is_loading:
                    color1 = self.warning_color
                    color2 = "#78350f" # Dark brown/amber
                    new_bg = color2 if current_bg == color1 else color1
                    self.status_bar.configure(bg=new_bg, fg=self.text_color)
                else:
                    if "LIVE" in current_text or "ACTIVE" in current_text:
                        color1 = self.accent_color
                        color2 = "#4c1d95"
                        new_bg = color2 if current_bg == color1 else color1
                        self.status_bar.configure(bg=new_bg, fg=self.text_color)
                    elif "SUCCESS" in current_text:
                        color1 = self.success_color
                        color2 = "#064e3b" # Dark emerald
                        new_bg = color2 if current_bg == color1 else color1
                        self.status_bar.configure(bg=new_bg, fg="#fafafa" if new_bg == color2 else "#09090b")
        except Exception as e:
            logger.debug(f"Pulsing exception: {e}")
        finally:
            self.root.after(500, self.pulse_status_bar)

    def _draw_status_pills(self, parent_frame):
        """
        Draws a modern horizontal ribbon of custom connectivity pills.
        """
        ribbon = tk.Frame(parent_frame, bg=self.bg_color)
        ribbon.pack(fill=tk.X, pady=(10, 10))

        def create_pill(label, text, is_ok):
            glow = self.success_color if is_ok else self.alert_color
            pill = tk.Frame(ribbon, bg=self.card_color, highlightthickness=1, highlightbackground=self.border_color, highlightcolor=self.border_color, bd=0)
            pill.pack(side=tk.LEFT, padx=10, fill=tk.Y)
            self._bind_hover_glow(pill, normal_border=self.border_color, hover_border=self.accent_color)

            # Icon/Name indicator
            tk.Label(pill, text=label, font=("Segoe UI", 9, "bold"), fg=self.muted_color, bg=self.card_color, padx=10, pady=5).pack(side=tk.LEFT)
            
            # Glowing badge
            badge = tk.Label(pill, text=text.upper(), font=("Segoe UI", 9, "bold"), fg="#09090b", bg=glow, padx=12, pady=5)
            badge.pack(side=tk.RIGHT)

        m_text, m_ok = self.hardware_states["mouse"]
        create_pill("⌨️ INPUT", m_text, m_ok)
        
        s_text, s_ok = self.hardware_states["speakers"]
        create_pill("🔊 AUDIO", s_text, s_ok)

        c_text, c_ok = self.hardware_states["camera"]
        create_pill("📷 CAMERA", c_text, c_ok)

    def render_diagnostics(self, mouse_kb_status: str, audio_status: str, audio_ok: bool, camera_status: str, camera_ok: bool):
        """
        Constructs Stage 1 checklist and Camera selection wizard widgets.
        """
        self.hardware_states["mouse"] = (mouse_kb_status, True)
        self.hardware_states["speakers"] = (audio_status, audio_ok)
        self.hardware_states["camera"] = (camera_status, camera_ok)

        for child in self.diag_frame.winfo_children():
            child.destroy()

        # Banner Ribbon Title
        header = GradientCanvas(self.diag_frame, color1="#1e1b4b", color2="#311042", text="🛡️ AI MEDICINE ASSISTANT SETUP WIZARD", font=("Segoe UI", 20, "bold"), fg="#c084fc", height=60)
        header.pack(fill=tk.X, pady=(15, 10), padx=20)

        # Render status pills ribbon
        self._draw_status_pills(self.diag_frame)
        btn_state = tk.NORMAL if camera_ok else tk.DISABLED
        btn_bg = self.success_color if camera_ok else self.border_color
        btn_fg = "#09090b" if camera_ok else self.muted_color
        hover_color = "#059669" if camera_ok else self.accent_color
        
        self.proceed_btn = self._create_premium_button(self.diag_frame, "🚀 Launch Main Accessibility Dashboard", btn_bg, btn_fg, 
                                                       self._trigger_proceed, hover_bg=hover_color)
        self.proceed_btn.configure(state=btn_state)
        self.proceed_btn.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(5, 20))

        # Main diagnostics card container (split columns)
        card = tk.Frame(self.diag_frame, bg=self.card_color, highlightthickness=1, highlightbackground=self.border_color, highlightcolor=self.border_color, bd=0)
        card.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=20, pady=10)
        self._bind_hover_glow(card, normal_border=self.border_color, hover_border=self.accent_color)

        # Two-column structure: Left for options, Right for camera live verification
        left_col = tk.Frame(card, bg=self.card_color)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)

        right_col = tk.Frame(card, bg=self.card_color)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, padx=20, pady=20)

        # --- LEFT COLUMN CONTENT ---
        # 1. System diagnostics checks
        diag_box = tk.LabelFrame(left_col, text=" SYSTEM DIAGNOSTICS CHECKS ", font=("Segoe UI", 10, "bold"),
                                   bg=self.card_color, fg=self.accent_color, highlightthickness=1, highlightbackground=self.border_color, highlightcolor=self.border_color, bd=0, padx=15, pady=10)
        diag_box.pack(fill=tk.X, pady=(0, 15))
        self._bind_hover_glow(diag_box, normal_bg=self.card_color, hover_bg="#202024", normal_border=self.border_color, hover_border=self.accent_color)

        def add_row(parent, icon, label, status_text, is_ok):
            row = tk.Frame(parent, bg=self.card_color)
            row.pack(fill=tk.X, pady=6)
            
            lbl = tk.Label(row, text=f"{icon}  {label}", font=("Segoe UI", 10, "bold"), fg=self.text_color, bg=self.card_color)
            lbl.pack(side=tk.LEFT)
            
            glow_color = self.success_color if is_ok else self.alert_color
            status_lbl = tk.Label(row, text=status_text.upper(), font=("Segoe UI", 9, "bold"), fg=glow_color, bg=self.card_color)
            status_lbl.pack(side=tk.RIGHT)

        add_row(diag_box, "⌨️", "Tactile Peripherals", mouse_kb_status, True)
        add_row(diag_box, "🔊", "SAPI5 Audio System", audio_status, audio_ok)

        # 2. Camera Configuration options card (Ask about camera source)
        camera_box = tk.LabelFrame(left_col, text=" CAMERA CONNECTION INTEGRATION ", font=("Segoe UI", 10, "bold"),
                                     bg=self.card_color, fg=self.accent_color, highlightthickness=1, highlightbackground=self.border_color, highlightcolor=self.border_color, bd=0, padx=15, pady=15)
        camera_box.pack(fill=tk.X, pady=5)
        self._bind_hover_glow(camera_box, normal_bg=self.card_color, hover_bg="#202024", normal_border=self.border_color, hover_border=self.accent_color)

        tk.Label(camera_box, text="How would you like to connect your camera device?", font=("Segoe UI", 11), fg=self.muted_color, bg=self.card_color).pack(anchor=tk.W, pady=(0, 10))

        # Radio buttons to choose camera type
        radio_frame = tk.Frame(camera_box, bg=self.card_color)
        radio_frame.pack(fill=tk.X, pady=5)

        # Container slots for toggleable controls
        toggle_frame = tk.Frame(camera_box, bg=self.card_color)
        toggle_frame.pack(fill=tk.X, pady=10)

        # Local Webcam UI Box
        local_widget_frame = tk.Frame(toggle_frame, bg=self.card_color)
        tk.Label(local_widget_frame, text="🔌 Local Webcam: ", font=("Segoe UI", 11, "bold"), fg=self.text_color, bg=self.card_color).pack(side=tk.LEFT)
        self.local_status_lbl = tk.Label(local_widget_frame, text="Auto-detecting...", font=("Segoe UI", 11, "italic"), fg=self.warning_color, bg=self.card_color)
        self.local_status_lbl.pack(side=tk.LEFT, padx=10)

        # IP Webcam UI Box
        ip_widget_frame = tk.Frame(toggle_frame, bg=self.card_color)
        tk.Label(ip_widget_frame, text="IP Camera Stream URL: ", font=("Segoe UI", 11, "bold"), fg=self.text_color, bg=self.card_color).pack(side=tk.LEFT)
        ip_entry = tk.Entry(ip_widget_frame, textvariable=self.ip_url_var, font=("Segoe UI", 11),
                            bg="#242433", fg=self.text_color, bd=0, insertbackground="white",
                            highlightbackground=self.border_color, highlightcolor=self.accent_color, highlightthickness=1)
        ip_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, ipady=4)

        self.scan_wifi_btn = self._create_premium_button(ip_widget_frame, "🔍 Auto-Scan Wi-Fi", self.accent_color, self.text_color,
                                                         self._trigger_scan_wifi, hover_bg=self.hover_color, font=("Segoe UI", 9, "bold"), height=1)
        self.scan_wifi_btn.configure(padx=10, pady=4)
        self.scan_wifi_btn.pack(side=tk.RIGHT, padx=5)

        self.local_widget_frame = local_widget_frame
        self.ip_widget_frame = ip_widget_frame

        usb_radio = tk.Radiobutton(radio_frame, text="🔌 Local USB Webcam", variable=self.camera_type_var, value="local",
                                    font=("Segoe UI", 11), bg=self.card_color, fg=self.text_color, selectcolor=self.card_color,
                                    activebackground=self.card_color, activeforeground=self.accent_color, command=self.switch_camera_inputs)
        usb_radio.pack(side=tk.LEFT, padx=(0, 20))

        ip_radio = tk.Radiobutton(radio_frame, text="🌐 Wireless IP Camera", variable=self.camera_type_var, value="ip",
                                    font=("Segoe UI", 11), bg=self.card_color, fg=self.text_color, selectcolor=self.card_color,
                                    activebackground=self.card_color, activeforeground=self.accent_color, command=self.switch_camera_inputs)
        ip_radio.pack(side=tk.LEFT, padx=10)

        # Trigger initial packing layout
        self.switch_camera_inputs()

        # Connect button
        self.verify_btn = self._create_premium_button(camera_box, "⚡ Verify Camera Connection", self.accent_color, self.text_color,
                                                      self._trigger_verify_camera, hover_bg=self.hover_color)
        self.verify_btn.pack(fill=tk.X, pady=(15, 0))

        # --- RIGHT COLUMN CONTENT ---
        # Live Preview Bounding Box
        preview_box = tk.LabelFrame(right_col, text=" HARDWARE LIVE PREVIEW FEED ", font=("Segoe UI", 10, "bold"),
                                    bg=self.card_color, fg=self.accent_color, highlightthickness=1, highlightbackground=self.border_color, highlightcolor=self.accent_color, bd=0, padx=15, pady=15)
        preview_box.pack(fill=tk.BOTH, expand=True)
        self._bind_hover_glow(preview_box, normal_bg=self.card_color, hover_bg="#202024", normal_border=self.border_color, hover_border=self.accent_color)

        self.preview_canvas = tk.Label(preview_box, text="[ PREVIEW STANDBY ]\n\nChoose camera source on left\nand click 'Verify Camera Connection'.",
                                       font=("Segoe UI", 10), bg="#050507", fg=self.muted_color, relief=tk.SOLID, bd=1, width=42, height=16)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)

        if camera_ok:
            self.unlock_proceed()

    def unlock_proceed(self):
        """
        Enables user launch transitions.
        """
        self.proceed_btn.default_bg = self.success_color
        self.proceed_btn.hover_bg = "#059669"
        self.proceed_btn.configure(state=tk.NORMAL, bg=self.success_color, fg="#09090b",
                                   highlightbackground=self.success_color, highlightcolor=self.success_color)
        logger.info("Diagnostics clear. Stage 2 launch interface unlocked.")

    def update_preview_frame(self, pil_image: Image.Image):
        """
        Updates the small preview canvas in the diagnostic setup stage.
        """
        try:
            if not self.preview_canvas.winfo_exists():
                return
            width = self.preview_canvas.winfo_width()
            height = self.preview_canvas.winfo_height()
            if width <= 10: width = 360
            if height <= 10: height = 270
            
            resized_img = pil_image.resize((width, height), Image.Resampling.BILINEAR)
            tk_img = ImageTk.PhotoImage(resized_img)
            
            self.preview_canvas.configure(image=tk_img, text="")
            self.preview_canvas.image = tk_img
        except Exception as e:
            logger.debug(f"Preview frame render mismatch: {e}")

    def _trigger_verify_camera(self):
        mode = self.camera_type_var.get()
        source = self.usb_index_var.get().strip() if mode == "local" else self.ip_url_var.get().strip()
        if self.verify_camera_callback:
            self.verify_camera_callback(mode, source)

    def _trigger_proceed(self):
        if self.proceed_btn['state'] == tk.DISABLED:
            self.speak_feedback("Cannot launch workspace. Please verify your camera connection first by pressing V.")
            return
        self.diag_frame.pack_forget()
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self._build_stage2_workspace()
        if self.proceed_callback:
            self.proceed_callback()

    def _build_stage2_workspace(self):
        """
        Draws the gorgeous stage 2 layout.
        """
        for child in self.main_frame.winfo_children():
            child.destroy()

        # Ribbon Status Header
        header = GradientCanvas(self.main_frame, color1="#1e1b4b", color2="#311042", text="👁️ AI MEDICINE ASSISTANT SYSTEM", font=("Segoe UI", 20, "bold"), fg="#c084fc", height=60)
        header.pack(fill=tk.X, side=tk.TOP, padx=20, pady=(15, 5))

        # Workspace split frames
        split_workspace = tk.Frame(self.main_frame, bg=self.bg_color)
        split_workspace.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # ------------------- LEFT PANEL: VIDEO CHANNEL -------------------
        left_panel = tk.Frame(split_workspace, bg=self.bg_color)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        tk.Label(left_panel, text="📷 LIVE STREAM ACCESSIBILITY FEED", font=("Segoe UI", 12, "bold"), fg=self.accent_color, bg=self.bg_color).pack(anchor=tk.W, pady=(0, 6))

        # Geometric neon bounding wrapper
        self.video_wrapper = tk.Frame(left_panel, bg="#000000", width=640, height=480, highlightthickness=2, highlightbackground=self.accent_color, highlightcolor=self.accent_color, bd=0)
        self.video_wrapper.pack_propagate(False)
        self.video_wrapper.pack(fill=tk.BOTH, expand=True)
        self._bind_hover_glow(self.video_wrapper, normal_border=self.accent_color, hover_border=self.success_color)

        self.video_canvas = tk.Label(self.video_wrapper, bg="#000000")
        self.video_canvas.pack(fill=tk.BOTH, expand=True)

        # ------------------- RIGHT PANEL: METRICS DESK -------------------
        self.right_panel = tk.Frame(split_workspace, bg=self.bg_color, width=480)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        self.right_panel.pack_propagate(False)

        # Scrollbar container
        scroll_y = tk.Scrollbar(self.right_panel, orient=tk.VERTICAL)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        canvas = tk.Canvas(self.right_panel, bg=self.bg_color, bd=0, highlightthickness=0, yscrollcommand=scroll_y.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.config(command=canvas.yview)

        desk_card = tk.Frame(canvas, bg=self.bg_color)
        canvas_win = canvas.create_window((0, 0), window=desk_card, anchor="nw")

        def configure_scroll(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        desk_card.bind("<Configure>", configure_scroll)

        def configure_canvas_width(e):
            canvas.itemconfig(canvas_win, width=e.width)
        canvas.bind("<Configure>", configure_canvas_width)

        # Intelligent Card Container
        metrics_box = tk.LabelFrame(desk_card, text=" DETECTED PRODUCT SIGNATURE ", font=("Segoe UI", 12, "bold"),
                                    bg=self.card_color, fg=self.accent_color, highlightthickness=1, highlightbackground=self.border_color, highlightcolor=self.border_color, bd=0, padx=20, pady=20)
        metrics_box.pack(fill=tk.X, pady=(0, 15))
        self._bind_hover_glow(metrics_box, normal_bg=self.card_color, hover_bg="#202024", normal_border=self.border_color, hover_border=self.accent_color)

        # Premium Row Spawners
        def spawn_row(parent, title, text, text_color="#FFFFFF", font_size=11):
            row = tk.Frame(parent, bg=self.card_color)
            row.pack(fill=tk.X, pady=8)
            
            lbl_title = tk.Label(row, text=f"{title}:", font=("Segoe UI", 11, "bold"), fg=self.muted_color, bg=self.card_color)
            lbl_title.pack(side=tk.LEFT, anchor=tk.NW)
            
            lbl_val = tk.Label(row, text=text, font=("Segoe UI", font_size, "bold"), fg=text_color, bg=self.card_color, wraplength=240, justify=tk.LEFT)
            lbl_val.pack(side=tk.RIGHT, anchor=tk.NE)
            return lbl_val

        self.drug_name_lbl = spawn_row(metrics_box, "💊 Medicine Name", "Waiting...", font_size=15, text_color=self.success_color)
        self.strength_lbl = spawn_row(metrics_box, "⚡ Product Strength", "-")
        self.form_lbl = spawn_row(metrics_box, "📋 Dosage Form", "-")
        self.mfg_lbl = spawn_row(metrics_box, "🏭 Manufacturer", "-")
        self.price_lbl = spawn_row(metrics_box, "🔬 Therapeutic Class", "-")

        # Large Text Blocks
        tk.Label(metrics_box, text="Verified Medical Indications:", font=("Segoe UI", 10, "bold"), fg=self.accent_color, bg=self.card_color).pack(anchor=tk.W, pady=(15, 2))
        self.indication_txt = tk.Text(metrics_box, height=3, font=("Segoe UI", 10), bg=self.bg_color, fg=self.text_color, wrap=tk.WORD, relief=tk.FLAT, state=tk.DISABLED, highlightthickness=1, highlightbackground=self.border_color)
        self.indication_txt.pack(fill=tk.X, pady=(0, 10))

        tk.Label(metrics_box, text="Therapeutic Classification / Side Effects:", font=("Segoe UI", 10, "bold"), fg=self.warning_color, bg=self.card_color).pack(anchor=tk.W, pady=(5, 2))
        self.side_effects_txt = tk.Text(metrics_box, height=3, font=("Segoe UI", 10), bg=self.bg_color, fg=self.text_color, wrap=tk.WORD, relief=tk.FLAT, state=tk.DISABLED, highlightthickness=1, highlightbackground=self.border_color)
        self.side_effects_txt.pack(fill=tk.X, pady=(0, 10))

        # Dynamic Data Source Indicator
        self.data_source_lbl = tk.Label(metrics_box, text="Data Source: [ STANDBY ]", font=("Segoe UI", 10, "bold"), fg=self.muted_color, bg=self.card_color, pady=10)
        self.data_source_lbl.pack(fill=tk.X)

        # Status Banner
        self.status_bar = tk.Label(desk_card, text="STATUS: System Active", font=("Segoe UI", 12, "bold"),
                                   bg=self.hover_color, fg=self.text_color, height=2, relief=tk.SOLID, bd=1)
        self.status_bar.pack(fill=tk.X, pady=(0, 15))

        # Stylized Control switches
        controls = tk.Frame(desk_card, bg=self.bg_color)
        controls.pack(fill=tk.X)

        self.capture_btn = self._create_premium_button(controls, "📸 CAPTURE BOTTLE LABEL [SPACE / C]", self.success_color, "#09090b",
                                                       self._trigger_capture, hover_bg="#059669")
        self.capture_btn.pack(fill=tk.X, pady=4)

        self.reset_btn = self._create_premium_button(controls, "🔄 RETRY LIVE SCANNER FEED [R]", self.warning_color, "#09090b",
                                                     self._trigger_reset, hover_bg="#d97706")
        self.reset_btn.pack(fill=tk.X, pady=4)

        self.quit_btn = self._create_premium_button(controls, "🛑 SHUTDOWN SYSTEM WORKSPACE [Q]", self.alert_color, self.text_color,
                                                    self._trigger_quit, hover_bg="#e11d48")
        self.quit_btn.pack(fill=tk.X, pady=4)

        # Online Fallback Button
        self.online_btn = self._create_premium_button(controls, "🔮 INTERNET SEARCH VERIFICATION [I]", self.accent_color, self.text_color,
                                                      self._trigger_online_search, hover_bg=self.hover_color)

    def _bind_hotkeys(self):
        self.root.bind("<space>", lambda e: self._trigger_capture())
        self.root.bind("<c>", lambda e: self._trigger_capture())
        self.root.bind("<C>", lambda e: self._trigger_capture())
        self.root.bind("<r>", lambda e: self._trigger_reset())
        self.root.bind("<R>", lambda e: self._trigger_reset())
        self.root.bind("<q>", lambda e: self._trigger_quit())
        self.root.bind("<Q>", lambda e: self._trigger_quit())
        self.root.bind("<i>", lambda e: self._trigger_online_search())
        self.root.bind("<I>", lambda e: self._trigger_online_search())
        self.root.bind("<u>", lambda e: self._select_camera_type("local"))
        self.root.bind("<U>", lambda e: self._select_camera_type("local"))
        self.root.bind("<w>", lambda e: self._select_camera_type("ip"))
        self.root.bind("<W>", lambda e: self._select_camera_type("ip"))
        self.root.bind("<v>", lambda e: self._trigger_verify_camera())
        self.root.bind("<V>", lambda e: self._trigger_verify_camera())
        self.root.bind("<l>", lambda e: self._trigger_proceed())
        self.root.bind("<L>", lambda e: self._trigger_proceed())

    def _select_camera_type(self, mode: str):
        self.camera_type_var.set(mode)
        self.switch_camera_inputs()

    def switch_camera_inputs(self):
        if not hasattr(self, 'local_widget_frame') or not hasattr(self, 'ip_widget_frame'):
            return
        mode = self.camera_type_var.get()
        if mode == "local":
            self.ip_widget_frame.pack_forget()
            self.local_widget_frame.pack(fill=tk.X, pady=5)
            if hasattr(self, 'verify_btn'):
                self.verify_btn.configure(text="🔄 Rescan Local Hardware Cameras")
            self.speak_feedback("Auto-detecting local hardware camera.")
        else:
            self.local_widget_frame.pack_forget()
            self.ip_widget_frame.pack(fill=tk.X, pady=5)
            if hasattr(self, 'verify_btn'):
                self.verify_btn.configure(text="⚡ Connect & Verify IP Camera")
            self.speak_feedback("Selected Wireless IP Camera stream input.")

        if self.camera_type_change_callback:
            self.camera_type_change_callback(mode)

    def speak_feedback(self, text: str):
        if hasattr(self, 'speak_callback') and self.speak_callback:
            self.speak_callback(text, True)

    def _trigger_capture(self):
        if self.capture_callback:
            self.capture_callback()

    def _trigger_reset(self):
        if self.reset_callback:
            self.reset_callback()

    def _trigger_quit(self):
        if self.quit_callback:
            self.quit_callback()

    def _trigger_online_search(self):
        if hasattr(self, 'online_search_callback') and self.online_search_callback:
            self.online_search_callback()

    def _trigger_scan_wifi(self):
        if hasattr(self, 'scan_wifi_callback') and self.scan_wifi_callback:
            self.scan_wifi_callback()

    def update_video_frame(self, pil_image: Image.Image):
        """
        Updates Left Frame canvas.
        """
        try:
            if not self.video_canvas.winfo_exists():
                return
            # Constrain to the fixed wrapper size to prevent positive feedback loop and layout sliding
            width = self.video_wrapper.winfo_width()
            height = self.video_wrapper.winfo_height()
            if width <= 10: width = 640
            if height <= 10: height = 480
            
            resized_img = pil_image.resize((width, height), Image.Resampling.BILINEAR)
            tk_img = ImageTk.PhotoImage(resized_img)
            
            self.video_canvas.configure(image=tk_img)
            self.video_canvas.image = tk_img
        except Exception as e:
            logger.debug(f"Frame render mismatch: {e}")

    def update_status(self, text: str, color: str = None):
        """
        Updates bottom Status text and colors.
        """
        if not color:
            color = self.hover_color
        try:
            self.status_bar.configure(text=f"STATUS: {text.upper()}", bg=color)
        except Exception:
            pass

    def display_matched_results(self, med: Dict[str, Any], score: float, data_source: str = "LOCAL"):
        """
        Populates high-fidelity widgets.
        """
        name = med.get('name', med.get('drug_name', 'N/A'))
        self.drug_name_lbl.configure(text=name.upper())
        self.mfg_lbl.configure(text=med.get('manufacturer', 'N/A'))
        self.strength_lbl.configure(text=med.get('strength', 'N/A'))
        self.form_lbl.configure(text=med.get('dosage_form', med.get('form', 'N/A')))
        self.price_lbl.configure(text=med.get('category', 'N/A'))
        
        self.indication_txt.configure(state=tk.NORMAL)
        self.indication_txt.delete("1.0", tk.END)
        self.indication_txt.insert(tk.END, med.get('indication', 'N/A'))
        self.indication_txt.configure(state=tk.DISABLED)

        self.side_effects_txt.configure(state=tk.NORMAL)
        self.side_effects_txt.delete("1.0", tk.END)
        self.side_effects_txt.insert(tk.END, med.get('classification', 'N/A'))
        self.side_effects_txt.configure(state=tk.DISABLED)
        
        # Enforce gorgeous glow success status
        self.update_status(f"MATCH SUCCESSFUL ({score*100:.0f}% ACCURACY)", self.success_color)
        self.status_bar.configure(fg="#09090b")

        # Set Data Source row
        if data_source.upper() == "ONLINE":
            self.data_source_lbl.configure(text="Data Source: SECURE WEB SCRAPER", fg=self.success_color)
        else:
            self.data_source_lbl.configure(text="Data Source: LOCAL DATABASE", fg=self.accent_color)

    def display_no_match(self, raw_ocr: str = ""):
        """
        Resets card values.
        """
        self.drug_name_lbl.configure(text="NO ACCURATE MATCH FOUND", fg=self.alert_color)
        self.mfg_lbl.configure(text="-")
        self.strength_lbl.configure(text="-")
        self.form_lbl.configure(text="-")
        self.price_lbl.configure(text="-")
        
        self.indication_txt.configure(state=tk.NORMAL)
        self.indication_txt.delete("1.0", tk.END)
        self.indication_txt.insert(tk.END, f"Offline fuzzy checks returned ambiguous match scores. Extracted text: '{raw_ocr}'")
        self.indication_txt.configure(state=tk.DISABLED)

        self.side_effects_txt.configure(state=tk.NORMAL)
        self.side_effects_txt.delete("1.0", tk.END)
        self.side_effects_txt.insert(tk.END, "Database matches filtered to ensure product identification safety.")
        self.side_effects_txt.configure(state=tk.DISABLED)

        self.data_source_lbl.configure(text="Data Source: FAILED MATCH DEFERRAL", fg=self.alert_color)
        self.update_status("SAFETY CHECK PENDING: Please align bottle flat", self.alert_color)
        self.status_bar.configure(fg=self.text_color)

    def show_online_search_button(self):
        """
        Docks button overlay.
        """
        try:
            self.online_btn.pack(fill=tk.X, pady=4, after=self.reset_btn)
        except Exception:
            pass

    def hide_online_search_button(self):
        """
        Undocks button overlay.
        """
        try:
            self.online_btn.pack_forget()
        except Exception:
            pass
