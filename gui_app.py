"""
Module A: UI & User Interface Engine (Premium Edition)
Constructs a stunning, high-fidelity native Tkinter desktop interface tailored for accessibility.
Enforces Deep Matte Charcoal (#121212) backdrop, Sleek Velvet Graphite (#1A1A24) cards,
Vibrant Emerald Mint (#00F5D4) success indicators, and Neon Purple (#9D4EDD) hover control switches.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import logging
from typing import Dict, Any, Callable, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GUIApp")

class MedicineAssistantGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("👁️ AI Medicine Assistant - Premium Accessibility Suite")
        self.root.geometry("1200x780")
        
        # High-Fidelity Color Palette System
        self.bg_color = "#121212"          # Matte Charcoal Backdrop
        self.card_color = "#1A1A24"        # Sleek Dark Velvet Graphite
        self.border_color = "#2D2D3F"      # Soft outline accent
        self.accent_color = "#9D4EDD"      # Neon Purple
        self.hover_color = "#7B2CBF"       # Amethyst Violet
        
        # State Colors
        self.success_color = "#00F5D4"     # Vibrant Emerald Mint
        self.alert_color = "#FF0054"       # Neon Crimson
        self.warning_color = "#FFB703"     # Golden Warning
        
        self.text_color = "#FFFFFF"        # Crisp pure white
        self.muted_color = "#A5A5B2"       # Soft graphite lavender

        # Legacy Compatibility Color Hooks
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
        self.bind_network_callback = None
        self.online_search_callback = None

        # Two-Stage Layout Containers
        self.diag_frame = None
        self.main_frame = None

        # Network IP Address variable
        self.ip_url_var = tk.StringVar(value="http://192.168.100.67:8080/video")

        # Hardware connection states cache
        self.hardware_states = {
            "mouse": ("CONNECTED", True),
            "speakers": ("CONNECTED (Local Audio)", True),
            "network": ("DISCONNECTED", False),
            "camera": ("DISCONNECTED", False)
        }

        self._build_stages()
        self._bind_hotkeys()
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

    def _create_premium_button(self, parent, text, bg, fg, command, hover_bg=None, font=("Segoe UI", 12, "bold"), height=2) -> tk.Button:
        """
        Utility to spawn fully padded flat buttons with hover animations.
        """
        btn = tk.Button(parent, text=text, font=font, bg=bg, fg=fg, relief=tk.FLAT, bd=0, padx=20, pady=10,
                        activebackground=hover_bg or bg, activeforeground=fg, command=command, cursor="hand2")
        if hover_bg:
            btn.bind("<Enter>", lambda e: btn.configure(bg=hover_bg))
            btn.bind("<Leave>", lambda e: btn.configure(bg=bg))
        return btn

    def _draw_status_pills(self, parent_frame):
        """
        Draws a modern horizontal ribbon of custom connectivity pills.
        """
        ribbon = tk.Frame(parent_frame, bg=self.bg_color)
        ribbon.pack(fill=tk.X, pady=(15, 5))

        def create_pill(label, text, is_ok):
            glow = self.success_color if is_ok else self.alert_color
            pill = tk.Frame(ribbon, bg=self.card_color, relief=tk.SOLID, bd=1, highlightbackground=self.border_color, highlightcolor=self.border_color)
            pill.pack(side=tk.LEFT, padx=10, fill=tk.Y)

            # Icon/Name indicator
            tk.Label(pill, text=label, font=("Segoe UI", 10, "bold"), fg=self.muted_color, bg=self.card_color, padx=10, pady=6).pack(side=tk.LEFT)
            
            # Glowing badge
            badge = tk.Label(pill, text=text.upper(), font=("Segoe UI", 10, "bold"), fg="#121212", bg=glow, padx=12, pady=6)
            badge.pack(side=tk.RIGHT)

        m_text, m_ok = self.hardware_states["mouse"]
        create_pill("⌨️ INPUT", m_text, m_ok)
        
        s_text, s_ok = self.hardware_states["speakers"]
        create_pill("🔊 AUDIO", s_text, s_ok)

        n_text, n_ok = self.hardware_states["network"]
        create_pill("🌐 NETWORK", n_text, n_ok)

        c_text, c_ok = self.hardware_states["camera"]
        create_pill("📷 CAMERA", c_text, c_ok)

    def render_diagnostics(self, mouse_kb_status: str, audio_status: str, audio_ok: bool, camera_status: str, camera_ok: bool):
        """
        Constructs Stage 1 checklist widgets.
        """
        self.hardware_states["mouse"] = (mouse_kb_status, True)
        self.hardware_states["speakers"] = (audio_status, audio_ok)
        self.hardware_states["camera"] = (camera_status, camera_ok)
        self.hardware_states["network"] = ("CONNECTED" if "Webcam" in camera_status or not camera_ok else "LOCAL BRIDGE", not (not audio_ok or not camera_ok))

        for child in self.diag_frame.winfo_children():
            child.destroy()

        # Banner Ribbon Title
        header = tk.Frame(self.diag_frame, bg=self.card_color, relief=tk.SOLID, bd=1, highlightbackground=self.border_color)
        header.pack(fill=tk.X, pady=(15, 10), padx=20)
        
        tk.Label(header, text="🔧 Pre-Flight System Diagnostics Checklist", font=("Segoe UI", 20, "bold"), fg=self.accent_color, bg=self.card_color, pady=15).pack()

        # Render custom glowing pills ribbon
        self._draw_status_pills(self.diag_frame)

        # Main diagnostics card container
        card = tk.Frame(self.diag_frame, bg=self.card_color, relief=tk.SOLID, bd=1, highlightbackground=self.border_color)
        card.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Checklist rows
        def add_row(parent, icon, label, status_text, is_ok):
            row = tk.Frame(parent, bg=self.card_color)
            row.pack(fill=tk.X, pady=10, padx=25)
            
            lbl = tk.Label(row, text=f"{icon}  {label}", font=("Segoe UI", 13, "bold"), fg=self.text_color, bg=self.card_color)
            lbl.pack(side=tk.LEFT)
            
            glow_color = self.success_color if is_ok else self.alert_color
            status_lbl = tk.Label(row, text=status_text.upper(), font=("Segoe UI", 11, "bold"), fg=glow_color, bg=self.card_color)
            status_lbl.pack(side=tk.RIGHT)

        add_row(card, "⌨️", "Accessibility Tactile Peripherals (Keyboard/Mouse)", mouse_kb_status, True)
        add_row(card, "🔊", "Default SAPI5 Speaker Output Driver", audio_status, audio_ok)
        add_row(card, "📷", "Local Hardware USB Camera Capture Index", camera_status, camera_ok)

        # Premium IP entry field container
        needs_network = (not audio_ok) or (not camera_ok)
        net_box = tk.LabelFrame(card, text=" PREMIUM NETWORK PIPELINE BRIDGE CONFIGURATION ", font=("Segoe UI", 11, "bold"),
                                  bg=self.card_color, fg=self.accent_color, relief=tk.SOLID, bd=1)
        net_box.pack(fill=tk.X, padx=25, pady=20)

        desc = "CRITICAL BIND ACTIVE: Direct hardware inputs missing. Please connect mobile webcam client server to route frame inputs." if needs_network else \
               "OPTIONAL BIND ACTIVE: Local hardware intact. You may optionally bridge a wireless IP Webcam link over Wi-Fi."
        tk.Label(net_box, text=desc, font=("Segoe UI", 11), fg=self.muted_color, bg=self.card_color, wraplength=900, justify=tk.LEFT).pack(anchor=tk.W, padx=20, pady=8)

        input_row = tk.Frame(net_box, bg=self.card_color)
        input_row.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(input_row, text="Mobile IP Camera Target URI: ", font=("Segoe UI", 12, "bold"), fg=self.text_color, bg=self.card_color).pack(side=tk.LEFT)
        
        self.net_entry = tk.Entry(input_row, textvariable=self.ip_url_var, font=("Segoe UI", 12),
                                  bg="#242433", fg=self.text_color, bd=0, insertbackground="white",
                                  highlightbackground=self.border_color, highlightcolor=self.accent_color, highlightthickness=1)
        self.net_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=15, ipady=6)

        # Stylized Connection button
        self.bind_btn = self._create_premium_button(net_box, "⚡ Initialize Connection Bridge", self.accent_color, self.text_color, 
                                                    self._trigger_bind_network, hover_bg=self.hover_color)
        self.bind_btn.pack(fill=tk.X, padx=20, pady=(5, 15))

        # Bottom Proceed switch button
        self.proceed_btn = self._create_premium_button(self.diag_frame, "🚀 Launch Main Accessibility Dashboard", self.border_color, self.muted_color, 
                                                       self._trigger_proceed, hover_bg=self.accent_color)
        self.proceed_btn.configure(state=tk.DISABLED)
        self.proceed_btn.pack(fill=tk.X, padx=20, pady=(5, 20))

        if not needs_network:
            self.proceed_btn.configure(state=tk.NORMAL, bg=self.success_color, fg="#121212")

    def unlock_proceed(self):
        """
        Enables user launch transitions.
        """
        self.proceed_btn.configure(state=tk.NORMAL, bg=self.success_color, fg="#121212")
        logger.info("Diagnostics clear. Stage 2 launch interface unlocked.")

    def _trigger_bind_network(self):
        val = self.ip_url_var.get().strip()
        if self.bind_network_callback and val:
            self.bind_network_callback(val)

    def _trigger_proceed(self):
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
        header = tk.Frame(self.main_frame, bg=self.card_color, relief=tk.SOLID, bd=1, highlightbackground=self.border_color)
        header.pack(fill=tk.X, side=tk.TOP, padx=20, pady=(15, 5))
        
        tk.Label(header, text="👁️ AI MEDICINE ACCISTANT SYSTEM", font=("Segoe UI", 20, "bold"), fg=self.accent_color, bg=self.card_color, pady=10).pack()

        # Workspace split frames
        split_workspace = tk.Frame(self.main_frame, bg=self.bg_color)
        split_workspace.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # ------------------- LEFT PANEL: VIDEO CHANNEL -------------------
        left_panel = tk.Frame(split_workspace, bg=self.bg_color)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        tk.Label(left_panel, text="📷 LIVE STREAM ACCESSIBILITY FEED", font=("Segoe UI", 12, "bold"), fg=self.accent_color, bg=self.bg_color).pack(anchor=tk.W, pady=(0, 6))

        # Geometric neon bounding wrapper (fixed constraints to prevent dynamic layout sliding)
        self.video_wrapper = tk.Frame(left_panel, bg="#000000", width=640, height=480, relief=tk.SOLID, bd=2, highlightbackground=self.accent_color, highlightcolor=self.accent_color)
        self.video_wrapper.pack_propagate(False)
        self.video_wrapper.pack(fill=tk.BOTH, expand=True)

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
                                    bg=self.card_color, fg=self.accent_color, relief=tk.SOLID, bd=1, padx=20, pady=20)
        metrics_box.pack(fill=tk.X, pady=(0, 15))

        # Premium Row Spawners
        def spawn_row(parent, title, text, text_color="#FFFFFF", font_size=11):
            row = tk.Frame(parent, bg=self.card_color)
            row.pack(fill=tk.X, pady=8)
            
            lbl_title = tk.Label(row, text=f"{title}:", font=("Segoe UI", 11, "bold"), fg=self.muted_color, bg=self.card_color)
            lbl_title.pack(side=tk.LEFT, anchor=tk.NW)
            
            lbl_val = tk.Label(row, text=text, font=("Segoe UI", font_size, "bold"), fg=text_color, bg=self.card_color, wraplength=280, justify=tk.LEFT)
            lbl_val.pack(side=tk.RIGHT, anchor=tk.NE)
            return lbl_val

        self.drug_name_lbl = spawn_row(metrics_box, "Medicine Name", "Waiting...", font_size=15, text_color=self.success_color)
        self.strength_lbl = spawn_row(metrics_box, "Product Strength", "-")
        self.form_lbl = spawn_row(metrics_box, "Dosage Form", "-")
        self.mfg_lbl = spawn_row(metrics_box, "Manufacturer", "-")
        self.price_lbl = spawn_row(metrics_box, "Therapeutic Class", "-")

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

        self.capture_btn = self._create_premium_button(controls, "📸 CAPTURE BOTTLE LABEL [SPACE / C]", self.success_color, "#121212",
                                                       self._trigger_capture, hover_bg="#00D2B4")
        self.capture_btn.pack(fill=tk.X, pady=4)

        self.reset_btn = self._create_premium_button(controls, "🔄 RETRY LIVE SCANNER FEED [R]", self.warning_color, "#121212",
                                                     self._trigger_reset, hover_bg="#E29E00")
        self.reset_btn.pack(fill=tk.X, pady=4)

        self.quit_btn = self._create_premium_button(controls, "🛑 SHUTDOWN SYSTEM WORKSPACE [Q]", self.alert_color, self.text_color,
                                                    self._trigger_quit, hover_bg="#D00042")
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
        self.status_bar.configure(fg="#121212")

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
        self.update_status("SAFETY CHECK PENDING: Pleae align bottle flat", self.alert_color)
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
