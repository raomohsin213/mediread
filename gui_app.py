"""
Module A: UI & User Interface Engine (Premium Obsidian Edition)
Constructs a high-fidelity native Tkinter desktop interface tailored for accessibility.
Supports full bilingual localization: Urdu (Default) and English with instant dynamic toggle.
Enforces Obsidian Black (#09090b) backdrop, Sleek Velvet Zinc (#18181b) cards,
Vibrant Emerald Mint (#10b981) success indicators, and Radiant Purple (#8b5cf6) accents.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import logging
from typing import Dict, Any, Callable, Optional

# Import localization
from localization import (
    get_text,
    get_spoken,
    DEFAULT_LANGUAGE,
    LANG_URDU,
    LANG_ENGLISH,
    translate_form_to_urdu,
    translate_indication_to_urdu
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GUIApp")


class GradientCanvas(tk.Canvas):
    """
    Custom vertical gradient canvas widget that supports shadow text for accessibility.
    Supports dynamic text updating for language switching.
    """
    def __init__(self, parent, color1: str, color2: str, text: str = "", font: tuple = ("Segoe UI", 18, "bold"), fg: str = "#c084fc", **kwargs):
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

    def set_text(self, new_text: str):
        """Updates text dynamically on language toggle."""
        self.text_content = new_text
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
        self.language = DEFAULT_LANGUAGE  # "ur" (Urdu) by default
        
        self.root.title("👁️ AI Medicine Assistant - AI میڈیسن اسسٹنٹ")
        self.root.geometry("1240x820")
        
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

        # Ensure window is brought to the foreground
        try:
            self.root.lift()
            self.root.attributes('-topmost', True)
            self.root.after(300, lambda: self.root.attributes('-topmost', False))
            self.root.focus_force()
        except Exception:
            pass

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
        self.speak_callback = None
        self.language_change_callback = None

        # Two-Stage Layout Containers
        self.diag_frame = None
        self.main_frame = None

        # Configuration variables
        self.camera_type_var = tk.StringVar(value="local")
        self.usb_index_var = tk.StringVar(value="0")
        self.ip_url_var = tk.StringVar(value="http://192.168.100.67:8080/video")

        # Hardware connection states cache
        self.hardware_states = {
            "mouse": ("CONNECTED", True),
            "speakers": ("CONNECTED", True),
            "camera": ("DISCONNECTED", False)
        }

        # Cache of last matched medicine for on-the-fly language switching
        self.last_matched_med = None
        self.last_matched_score = 1.0
        self.last_matched_source = "LOCAL"

        # References to dynamically updateable widgets in Stage 2
        self.stage2_labels = {}

        self._build_stages()
        self._bind_hotkeys()
        
        # Start status bar pulsing loop
        self.root.after(500, self.pulse_status_bar)
        
        logger.info(f"Accessibility UI Engine initialized under Obsidian-Urdu Theme (Default: '{self.language}').")

    def t(self, key: str, default: str = "") -> str:
        """Helper to get translated string for current language."""
        return get_text(key, self.language, default)

    def toggle_language(self):
        """
        Toggles the application language between Urdu and English seamlessly.
        Updates all UI widgets dynamically in place without interrupting camera feeds.
        """
        self.language = LANG_ENGLISH if self.language == LANG_URDU else LANG_URDU
        logger.info(f"Language toggled to: {self.language.upper()}")

        # 1. Update Stage 1 if visible
        if self.diag_frame.winfo_ismapped():
            m_text, m_ok = self.hardware_states["mouse"]
            s_text, s_ok = self.hardware_states["speakers"]
            c_text, c_ok = self.hardware_states["camera"]
            self.render_diagnostics(m_text, s_text, s_ok, c_text, c_ok)

        # 2. Update Stage 2 if visible
        if self.main_frame.winfo_ismapped():
            self._update_stage2_language()

        # 3. Notify orchestrator callback
        if self.language_change_callback:
            self.language_change_callback(self.language)

    def _update_stage2_language(self):
        """Updates all text in Stage 2 dashboard when language is toggled."""
        try:
            if hasattr(self, 'header_stage2'):
                self.header_stage2.set_text(self.t("app_header"))

            if hasattr(self, 'live_feed_lbl'):
                self.live_feed_lbl.configure(text=self.t("live_feed_title"))

            if hasattr(self, 'metrics_box'):
                self.metrics_box.configure(text=self.t("product_sig_title"))

            # Update row title labels
            for key, lbl in self.stage2_labels.items():
                if key in ["medicine_name", "product_strength", "dosage_form", "manufacturer", "therapeutic_class"]:
                    lbl.configure(text=f"{self.t(key)}:")

            if hasattr(self, 'ind_title_lbl'):
                self.ind_title_lbl.configure(text=self.t("indications_title"))

            if hasattr(self, 'prec_title_lbl'):
                self.prec_title_lbl.configure(text=self.t("precautions_title"))

            # Update control buttons
            if hasattr(self, 'capture_btn'):
                self.capture_btn.configure(text=self.t("capture_btn"))
            if hasattr(self, 'reset_btn'):
                self.reset_btn.configure(text=self.t("retry_btn"))
            if hasattr(self, 'quit_btn'):
                self.quit_btn.configure(text=self.t("quit_btn"))
            if hasattr(self, 'online_btn'):
                self.online_btn.configure(text=self.t("online_search_btn"))
            if hasattr(self, 'lang_btn_stage2'):
                self.lang_btn_stage2.configure(text=self.t("change_lang_btn"))

            # Re-render active medicine match if present
            if self.last_matched_med:
                self.display_matched_results(self.last_matched_med, self.last_matched_score, self.last_matched_source)
        except Exception as e:
            logger.debug(f"Stage 2 language update error: {e}")

    def _build_stages(self):
        """Initializes primary Tkinter layouts."""
        self.diag_frame = tk.Frame(self.root, bg=self.bg_color)
        self.diag_frame.pack(fill=tk.BOTH, expand=True)

        self.main_frame = tk.Frame(self.root, bg=self.bg_color)

    def _create_premium_button(self, parent, text, bg, fg, command, hover_bg=None, font=("Segoe UI", 11, "bold"), height=2) -> tk.Button:
        """Utility to spawn flat buttons with hover animations and outline glow."""
        btn = tk.Button(parent, text=text, font=font, bg=bg, fg=fg, relief=tk.FLAT, bd=0, padx=20, pady=10,
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
        """Binds enter/leave events to apply highlights to frames."""
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
        """Pulsates the status bar color when in warning, alert or loading states."""
        try:
            if hasattr(self, 'status_bar') and self.status_bar.winfo_exists():
                current_text = self.status_bar.cget("text").upper()
                current_bg = self.status_bar.cget("bg")
                
                is_alert = any(kw in current_text for kw in ["ALERT", "FAILED", "REQUIRED", "RESCAN", "ERROR", "WARNING", "OFFLINE", "انتباہ", "ناکام", "خرابی"])
                is_loading = any(kw in current_text for kw in ["ANALYZING", "EXTRACTING", "SCANNING", "QUERYING", "تجزیہ", "نکالا جا رہا", "تلاش"])
                
                if is_alert:
                    color1 = self.alert_color
                    color2 = "#881337"
                    new_bg = color2 if current_bg == color1 else color1
                    self.status_bar.configure(bg=new_bg, fg=self.text_color)
                elif is_loading:
                    color1 = self.warning_color
                    color2 = "#78350f"
                    new_bg = color2 if current_bg == color1 else color1
                    self.status_bar.configure(bg=new_bg, fg=self.text_color)
                else:
                    if "LIVE" in current_text or "ACTIVE" in current_text or "فعال" in current_text:
                        color1 = self.accent_color
                        color2 = "#4c1d95"
                        new_bg = color2 if current_bg == color1 else color1
                        self.status_bar.configure(bg=new_bg, fg=self.text_color)
                    elif "SUCCESS" in current_text or "کامیابی" in current_text:
                        color1 = self.success_color
                        color2 = "#064e3b"
                        new_bg = color2 if current_bg == color1 else color1
                        self.status_bar.configure(bg=new_bg, fg="#fafafa" if new_bg == color2 else "#09090b")
        except Exception:
            pass
        finally:
            self.root.after(500, self.pulse_status_bar)

    def _draw_status_pills(self, parent_frame):
        """Draws horizontal status indicators ribbon."""
        ribbon = tk.Frame(parent_frame, bg=self.bg_color)
        ribbon.pack(fill=tk.X, pady=(6, 8))

        def create_pill(label, text, is_ok):
            glow = self.success_color if is_ok else self.alert_color
            pill = tk.Frame(ribbon, bg=self.card_color, highlightthickness=1, highlightbackground=self.border_color, highlightcolor=self.border_color, bd=0)
            pill.pack(side=tk.LEFT, padx=8, fill=tk.Y)
            self._bind_hover_glow(pill, normal_border=self.border_color, hover_border=self.accent_color)

            tk.Label(pill, text=label, font=("Segoe UI", 9, "bold"), fg=self.muted_color, bg=self.card_color, padx=10, pady=5).pack(side=tk.LEFT)
            badge = tk.Label(pill, text=text.upper(), font=("Segoe UI", 9, "bold"), fg="#09090b", bg=glow, padx=12, pady=5)
            badge.pack(side=tk.RIGHT)

        m_text, m_ok = self.hardware_states["mouse"]
        s_text, s_ok = self.hardware_states["speakers"]
        c_text, c_ok = self.hardware_states["camera"]

        create_pill(self.t("input_pill"), self.t("connected") if m_ok else self.t("disconnected"), m_ok)
        create_pill(self.t("audio_pill"), self.t("connected") if s_ok else self.t("audio_missing"), s_ok)
        create_pill(self.t("camera_pill"), self.t("connected") if c_ok else self.t("disconnected"), c_ok)

        # Stage 1 Language Toggle Button in top ribbon
        lang_label = "🌐 English" if self.language == LANG_URDU else "🌐 اردو"
        self.lang_btn_stage1 = self._create_premium_button(ribbon, lang_label, self.card_color, self.accent_color,
                                                           self.toggle_language, hover_bg="#262630",
                                                           font=("Segoe UI", 9, "bold"), height=1)
        self.lang_btn_stage1.configure(padx=12, pady=5)
        self.lang_btn_stage1.pack(side=tk.RIGHT, padx=8)

    def render_diagnostics(self, mouse_kb_status: str, audio_status: str, audio_ok: bool, camera_status: str, camera_ok: bool):
        """Constructs Stage 1 checklist and Camera selection wizard widgets."""
        self.hardware_states["mouse"] = (mouse_kb_status, True)
        self.hardware_states["speakers"] = (audio_status, audio_ok)
        self.hardware_states["camera"] = (camera_status, camera_ok)

        for child in self.diag_frame.winfo_children():
            child.destroy()

        # Banner Ribbon Title
        header = GradientCanvas(self.diag_frame, color1="#1e1b4b", color2="#311042", text=self.t("wizard_title"),
                                font=("Segoe UI", 20, "bold"), fg="#c084fc", height=58)
        header.pack(fill=tk.X, pady=(12, 6), padx=20)

        # Render status pills ribbon
        self._draw_status_pills(self.diag_frame)
        
        btn_state = tk.NORMAL if camera_ok else tk.DISABLED
        btn_bg = self.success_color if camera_ok else self.border_color
        btn_fg = "#09090b" if camera_ok else self.muted_color
        hover_color = "#059669" if camera_ok else self.accent_color
        
        self.proceed_btn = self._create_premium_button(self.diag_frame, self.t("launch_dashboard_btn"), btn_bg, btn_fg, 
                                                       self._trigger_proceed, hover_bg=hover_color)
        self.proceed_btn.configure(state=btn_state)
        self.proceed_btn.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(5, 15))

        # Main diagnostics card container (split columns)
        card = tk.Frame(self.diag_frame, bg=self.card_color, highlightthickness=1, highlightbackground=self.border_color, highlightcolor=self.border_color, bd=0)
        card.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=20, pady=8)
        self._bind_hover_glow(card, normal_border=self.border_color, hover_border=self.accent_color)

        left_col = tk.Frame(card, bg=self.card_color)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=15)

        right_col = tk.Frame(card, bg=self.card_color)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, padx=20, pady=15)

        # --- LEFT COLUMN CONTENT ---
        # 1. System diagnostics checks
        diag_box = tk.LabelFrame(left_col, text=self.t("sys_diag_title"), font=("Segoe UI", 10, "bold"),
                                 bg=self.card_color, fg=self.accent_color, highlightthickness=1, highlightbackground=self.border_color, highlightcolor=self.border_color, bd=0, padx=15, pady=10)
        diag_box.pack(fill=tk.X, pady=(0, 12))
        self._bind_hover_glow(diag_box, normal_bg=self.card_color, hover_bg="#202024", normal_border=self.border_color, hover_border=self.accent_color)

        def add_row(parent, icon, label, status_text, is_ok):
            row = tk.Frame(parent, bg=self.card_color)
            row.pack(fill=tk.X, pady=5)
            lbl = tk.Label(row, text=f"{icon}  {label}", font=("Segoe UI", 10, "bold"), fg=self.text_color, bg=self.card_color)
            lbl.pack(side=tk.LEFT)
            glow_color = self.success_color if is_ok else self.alert_color
            status_lbl = tk.Label(row, text=status_text.upper(), font=("Segoe UI", 9, "bold"), fg=glow_color, bg=self.card_color)
            status_lbl.pack(side=tk.RIGHT)

        kb_disp = self.t("mouse_kb_connected") if True else self.t("disconnected")
        aud_disp = self.t("audio_connected") if audio_ok else self.t("audio_missing")
        add_row(diag_box, "⌨️", self.t("tactile_peripherals"), kb_disp, True)
        add_row(diag_box, "🔊", self.t("sapi_audio"), aud_disp, audio_ok)

        # 2. Camera Configuration options card
        camera_box = tk.LabelFrame(left_col, text=self.t("cam_conn_title"), font=("Segoe UI", 10, "bold"),
                                   bg=self.card_color, fg=self.accent_color, highlightthickness=1, highlightbackground=self.border_color, highlightcolor=self.border_color, bd=0, padx=15, pady=12)
        camera_box.pack(fill=tk.X, pady=5)
        self._bind_hover_glow(camera_box, normal_bg=self.card_color, hover_bg="#202024", normal_border=self.border_color, hover_border=self.accent_color)

        tk.Label(camera_box, text=self.t("cam_conn_prompt"), font=("Segoe UI", 10), fg=self.muted_color, bg=self.card_color).pack(anchor=tk.W, pady=(0, 8))

        # Radio buttons
        radio_frame = tk.Frame(camera_box, bg=self.card_color)
        radio_frame.pack(fill=tk.X, pady=4)

        toggle_frame = tk.Frame(camera_box, bg=self.card_color)
        toggle_frame.pack(fill=tk.X, pady=8)

        # Local Webcam UI Box
        local_widget_frame = tk.Frame(toggle_frame, bg=self.card_color)
        tk.Label(local_widget_frame, text=self.t("local_webcam_lbl"), font=("Segoe UI", 10, "bold"), fg=self.text_color, bg=self.card_color).pack(side=tk.LEFT)
        self.local_status_lbl = tk.Label(local_widget_frame, text="Auto-detecting...", font=("Segoe UI", 10, "italic"), fg=self.warning_color, bg=self.card_color)
        self.local_status_lbl.pack(side=tk.LEFT, padx=10)

        # IP Webcam UI Box
        ip_widget_frame = tk.Frame(toggle_frame, bg=self.card_color)
        tk.Label(ip_widget_frame, text=self.t("ip_stream_url_lbl"), font=("Segoe UI", 10, "bold"), fg=self.text_color, bg=self.card_color).pack(side=tk.LEFT)
        ip_entry = tk.Entry(ip_widget_frame, textvariable=self.ip_url_var, font=("Segoe UI", 10),
                            bg="#242433", fg=self.text_color, bd=0, insertbackground="white",
                            highlightbackground=self.border_color, highlightcolor=self.accent_color, highlightthickness=1)
        ip_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8, ipady=3)

        self.scan_wifi_btn = self._create_premium_button(ip_widget_frame, self.t("scan_wifi_btn"), self.accent_color, self.text_color,
                                                         self._trigger_scan_wifi, hover_bg=self.hover_color, font=("Segoe UI", 9, "bold"), height=1)
        self.scan_wifi_btn.configure(padx=10, pady=3)
        self.scan_wifi_btn.pack(side=tk.RIGHT, padx=4)

        self.local_widget_frame = local_widget_frame
        self.ip_widget_frame = ip_widget_frame

        usb_radio = tk.Radiobutton(radio_frame, text=self.t("local_usb_cam"), variable=self.camera_type_var, value="local",
                                    font=("Segoe UI", 10), bg=self.card_color, fg=self.text_color, selectcolor=self.card_color,
                                    activebackground=self.card_color, activeforeground=self.accent_color, command=self.switch_camera_inputs)
        usb_radio.pack(side=tk.LEFT, padx=(0, 20))

        ip_radio = tk.Radiobutton(radio_frame, text=self.t("wireless_ip_cam"), variable=self.camera_type_var, value="ip",
                                    font=("Segoe UI", 10), bg=self.card_color, fg=self.text_color, selectcolor=self.card_color,
                                    activebackground=self.card_color, activeforeground=self.accent_color, command=self.switch_camera_inputs)
        ip_radio.pack(side=tk.LEFT, padx=10)

        self.switch_camera_inputs()

        # Connect button
        self.verify_btn = self._create_premium_button(camera_box, self.t("verify_cam_btn"), self.accent_color, self.text_color,
                                                      self._trigger_verify_camera, hover_bg=self.hover_color)
        self.verify_btn.pack(fill=tk.X, pady=(12, 0))

        # --- RIGHT COLUMN CONTENT ---
        preview_box = tk.LabelFrame(right_col, text=self.t("preview_box_title"), font=("Segoe UI", 10, "bold"),
                                    bg=self.card_color, fg=self.accent_color, highlightthickness=1, highlightbackground=self.border_color, highlightcolor=self.accent_color, bd=0, padx=15, pady=15)
        preview_box.pack(fill=tk.BOTH, expand=True)
        self._bind_hover_glow(preview_box, normal_bg=self.card_color, hover_bg="#202024", normal_border=self.border_color, hover_border=self.accent_color)

        self.preview_canvas = tk.Label(preview_box, text=self.t("preview_standby"),
                                       font=("Segoe UI", 10), bg="#050507", fg=self.muted_color, relief=tk.SOLID, bd=1, width=42, height=16)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)

        if camera_ok:
            self.unlock_proceed()

    def unlock_proceed(self):
        """Enables user launch transitions."""
        if hasattr(self, 'proceed_btn'):
            self.proceed_btn.default_bg = self.success_color
            self.proceed_btn.hover_bg = "#059669"
            self.proceed_btn.configure(state=tk.NORMAL, bg=self.success_color, fg="#09090b",
                                       highlightbackground=self.success_color, highlightcolor=self.success_color)
        logger.info("Diagnostics clear. Stage 2 launch interface unlocked.")

    def update_preview_frame(self, pil_image: Image.Image):
        """Updates the small preview canvas in the diagnostic setup stage."""
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
            self.speak_feedback(self.t("cannot_launch_need_verify"))
            return
        self.diag_frame.pack_forget()
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self._build_stage2_workspace()
        if self.proceed_callback:
            self.proceed_callback()

    def _build_stage2_workspace(self):
        """Draws Stage 2 layout with bilingual responsiveness."""
        for child in self.main_frame.winfo_children():
            child.destroy()

        self.stage2_labels.clear()

        # Ribbon Status Header
        top_bar = tk.Frame(self.main_frame, bg=self.bg_color)
        top_bar.pack(fill=tk.X, side=tk.TOP, padx=20, pady=(12, 4))

        self.header_stage2 = GradientCanvas(top_bar, color1="#1e1b4b", color2="#311042", text=self.t("app_header"),
                                            font=("Segoe UI", 18, "bold"), fg="#c084fc", height=54)
        self.header_stage2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Language toggle button placed prominently in header
        lang_switch_label = "🌐 English" if self.language == LANG_URDU else "🌐 اردو"
        self.header_lang_btn = self._create_premium_button(top_bar, lang_switch_label, self.card_color, self.accent_color,
                                                           self.toggle_language, hover_bg="#262630",
                                                           font=("Segoe UI", 10, "bold"), height=1)
        self.header_lang_btn.configure(padx=14, pady=10)
        self.header_lang_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # Workspace split frames
        split_workspace = tk.Frame(self.main_frame, bg=self.bg_color)
        split_workspace.pack(fill=tk.BOTH, expand=True, padx=20, pady=8)

        # ------------------- LEFT PANEL: VIDEO CHANNEL -------------------
        left_panel = tk.Frame(split_workspace, bg=self.bg_color)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.live_feed_lbl = tk.Label(left_panel, text=self.t("live_feed_title"), font=("Segoe UI", 12, "bold"), fg=self.accent_color, bg=self.bg_color)
        self.live_feed_lbl.pack(anchor=tk.W, pady=(0, 6))

        self.video_wrapper = tk.Frame(left_panel, bg="#000000", width=640, height=480, highlightthickness=2, highlightbackground=self.accent_color, highlightcolor=self.accent_color, bd=0)
        self.video_wrapper.pack_propagate(False)
        self.video_wrapper.pack(fill=tk.BOTH, expand=True)
        self._bind_hover_glow(self.video_wrapper, normal_border=self.accent_color, hover_border=self.success_color)

        self.video_canvas = tk.Label(self.video_wrapper, bg="#000000")
        self.video_canvas.pack(fill=tk.BOTH, expand=True)

        # ------------------- RIGHT PANEL: METRICS DESK -------------------
        self.right_panel = tk.Frame(split_workspace, bg=self.bg_color, width=490)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        self.right_panel.pack_propagate(False)

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

        # Metrics Card Container
        self.metrics_box = tk.LabelFrame(desk_card, text=self.t("product_sig_title"), font=("Segoe UI", 12, "bold"),
                                         bg=self.card_color, fg=self.accent_color, highlightthickness=1, highlightbackground=self.border_color, highlightcolor=self.border_color, bd=0, padx=18, pady=16)
        self.metrics_box.pack(fill=tk.X, pady=(0, 12))
        self._bind_hover_glow(self.metrics_box, normal_bg=self.card_color, hover_bg="#202024", normal_border=self.border_color, hover_border=self.accent_color)

        def spawn_row(parent, key, text, text_color="#FFFFFF", font_size=11):
            row = tk.Frame(parent, bg=self.card_color)
            row.pack(fill=tk.X, pady=6)
            
            lbl_title = tk.Label(row, text=f"{self.t(key)}:", font=("Segoe UI", 10, "bold"), fg=self.muted_color, bg=self.card_color)
            lbl_title.pack(side=tk.LEFT, anchor=tk.NW)
            self.stage2_labels[key] = lbl_title
            
            lbl_val = tk.Label(row, text=text, font=("Segoe UI", font_size, "bold"), fg=text_color, bg=self.card_color, wraplength=250, justify=tk.LEFT)
            lbl_val.pack(side=tk.RIGHT, anchor=tk.NE)
            return lbl_val

        self.drug_name_lbl = spawn_row(self.metrics_box, "medicine_name", self.t("waiting"), font_size=14, text_color=self.success_color)
        self.strength_lbl = spawn_row(self.metrics_box, "product_strength", "-")
        self.form_lbl = spawn_row(self.metrics_box, "dosage_form", "-")
        self.mfg_lbl = spawn_row(self.metrics_box, "manufacturer", "-")
        self.price_lbl = spawn_row(self.metrics_box, "therapeutic_class", "-")

        self.ind_title_lbl = tk.Label(self.metrics_box, text=self.t("indications_title"), font=("Segoe UI", 10, "bold"), fg=self.accent_color, bg=self.card_color)
        self.ind_title_lbl.pack(anchor=tk.W, pady=(12, 2))
        self.indication_txt = tk.Text(self.metrics_box, height=3, font=("Segoe UI", 10), bg=self.bg_color, fg=self.text_color, wrap=tk.WORD, relief=tk.FLAT, state=tk.DISABLED, highlightthickness=1, highlightbackground=self.border_color)
        self.indication_txt.pack(fill=tk.X, pady=(0, 8))

        self.prec_title_lbl = tk.Label(self.metrics_box, text=self.t("precautions_title"), font=("Segoe UI", 10, "bold"), fg=self.warning_color, bg=self.card_color)
        self.prec_title_lbl.pack(anchor=tk.W, pady=(4, 2))
        self.side_effects_txt = tk.Text(self.metrics_box, height=3, font=("Segoe UI", 10), bg=self.bg_color, fg=self.text_color, wrap=tk.WORD, relief=tk.FLAT, state=tk.DISABLED, highlightthickness=1, highlightbackground=self.border_color)
        self.side_effects_txt.pack(fill=tk.X, pady=(0, 8))

        self.data_source_lbl = tk.Label(self.metrics_box, text=self.t("data_source_standby"), font=("Segoe UI", 9, "bold"), fg=self.muted_color, bg=self.card_color, pady=8)
        self.data_source_lbl.pack(fill=tk.X)

        # Status Banner
        self.status_bar = tk.Label(desk_card, text=f"STATUS: {self.t('status_active').upper()}", font=("Segoe UI", 11, "bold"),
                                   bg=self.hover_color, fg=self.text_color, height=2, relief=tk.SOLID, bd=1)
        self.status_bar.pack(fill=tk.X, pady=(0, 12))

        # Controls
        controls = tk.Frame(desk_card, bg=self.bg_color)
        controls.pack(fill=tk.X)

        self.capture_btn = self._create_premium_button(controls, self.t("capture_btn"), self.success_color, "#09090b",
                                                       self._trigger_capture, hover_bg="#059669")
        self.capture_btn.pack(fill=tk.X, pady=3)

        self.reset_btn = self._create_premium_button(controls, self.t("retry_btn"), self.warning_color, "#09090b",
                                                     self._trigger_reset, hover_bg="#d97706")
        self.reset_btn.pack(fill=tk.X, pady=3)

        self.quit_btn = self._create_premium_button(controls, self.t("quit_btn"), self.alert_color, self.text_color,
                                                    self._trigger_quit, hover_bg="#e11d48")
        self.quit_btn.pack(fill=tk.X, pady=3)

        # Language toggle button in controls deck
        self.lang_btn_stage2 = self._create_premium_button(controls, self.t("change_lang_btn"), self.card_color, self.accent_color,
                                                           self.toggle_language, hover_bg="#262630")
        self.lang_btn_stage2.pack(fill=tk.X, pady=3)

        # Online Fallback Button
        self.online_btn = self._create_premium_button(controls, self.t("online_search_btn"), self.accent_color, self.text_color,
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
        # Hotkey T to toggle language
        self.root.bind("<t>", lambda e: self.toggle_language())
        self.root.bind("<T>", lambda e: self.toggle_language())

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
                self.verify_btn.configure(text=self.t("rescan_local_btn"))
            self.speak_feedback(self.t("auto_detect_cam"))
        else:
            self.local_widget_frame.pack_forget()
            self.ip_widget_frame.pack(fill=tk.X, pady=5)
            if hasattr(self, 'verify_btn'):
                self.verify_btn.configure(text=self.t("verify_ip_btn"))
            self.speak_feedback(self.t("selected_ip_cam"))

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
        """Updates Left Frame canvas."""
        try:
            if not self.video_canvas.winfo_exists():
                return
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
        """Updates bottom Status text and colors."""
        if not color:
            color = self.hover_color
        try:
            self.status_bar.configure(text=f"STATUS: {text.upper()}", bg=color)
        except Exception:
            pass

    def display_matched_results(self, med: Dict[str, Any], score: float, data_source: str = "LOCAL"):
        """Populates widgets with localized drug information."""
        self.last_matched_med = med
        self.last_matched_score = score
        self.last_matched_source = data_source

        name = med.get('name', med.get('drug_name', 'N/A'))
        raw_form = med.get('dosage_form', med.get('form', 'N/A'))
        raw_indication = med.get('indication', 'N/A')
        
        display_form = translate_form_to_urdu(raw_form) if self.language == LANG_URDU else raw_form
        display_indication = translate_indication_to_urdu(raw_indication) if self.language == LANG_URDU else raw_indication

        self.drug_name_lbl.configure(text=name.upper())
        self.mfg_lbl.configure(text=med.get('manufacturer', 'N/A'))
        self.strength_lbl.configure(text=med.get('strength', 'N/A'))
        self.form_lbl.configure(text=display_form)
        self.price_lbl.configure(text=med.get('category', 'N/A'))
        
        self.indication_txt.configure(state=tk.NORMAL)
        self.indication_txt.delete("1.0", tk.END)
        self.indication_txt.insert(tk.END, display_indication)
        self.indication_txt.configure(state=tk.DISABLED)

        self.side_effects_txt.configure(state=tk.NORMAL)
        self.side_effects_txt.delete("1.0", tk.END)
        self.side_effects_txt.insert(tk.END, med.get('classification', 'N/A'))
        self.side_effects_txt.configure(state=tk.DISABLED)
        
        match_msg = f"{self.t('match_successful')} ({score*100:.0f}%)"
        self.update_status(match_msg, self.success_color)
        self.status_bar.configure(fg="#09090b")

        if data_source.upper() == "ONLINE":
            self.data_source_lbl.configure(text=self.t("data_source_online"), fg=self.success_color)
        else:
            self.data_source_lbl.configure(text=self.t("data_source_local"), fg=self.accent_color)

    def display_no_match(self, raw_ocr: str = ""):
        """Resets card values on failed scan."""
        self.last_matched_med = None
        self.drug_name_lbl.configure(text=self.t("no_accurate_match"), fg=self.alert_color)
        self.mfg_lbl.configure(text="-")
        self.strength_lbl.configure(text="-")
        self.form_lbl.configure(text="-")
        self.price_lbl.configure(text="-")
        
        self.indication_txt.configure(state=tk.NORMAL)
        self.indication_txt.delete("1.0", tk.END)
        msg_ambiguous = self.t("ambiguous_match_text").replace("{raw_ocr}", raw_ocr)
        self.indication_txt.insert(tk.END, msg_ambiguous)
        self.indication_txt.configure(state=tk.DISABLED)

        self.side_effects_txt.configure(state=tk.NORMAL)
        self.side_effects_txt.delete("1.0", tk.END)
        self.side_effects_txt.insert(tk.END, self.t("safety_filtered_text"))
        self.side_effects_txt.configure(state=tk.DISABLED)

        self.data_source_lbl.configure(text=self.t("data_source_failed"), fg=self.alert_color)
        self.update_status(self.t("align_bottle_flat_status"), self.alert_color)
        self.status_bar.configure(fg=self.text_color)

    def show_online_search_button(self):
        try:
            self.online_btn.pack(fill=tk.X, pady=3, after=self.reset_btn)
        except Exception:
            pass

    def hide_online_search_button(self):
        try:
            self.online_btn.pack_forget()
        except Exception:
            pass
