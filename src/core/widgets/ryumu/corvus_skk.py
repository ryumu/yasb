import ctypes
import logging
from ctypes import wintypes

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel

from core.utils.utilities import build_widget_label
from core.validation.widgets.ryumu.corvus_skk import CorvusSKKConfig
from core.widgets.base import BaseWidget

# Windows API constants
WM_IME_CONTROL = 0x0283
IMC_GETOPENSTATUS = 0x0005
IMC_GETCONVERSIONMODE = 0x0001
IME_CMODE_NATIVE = 0x0001
IME_CMODE_KATAKANA = 0x0002
IME_CMODE_FULLSHAPE = 0x0008


class GUITHREADINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hwndActive", wintypes.HWND),
        ("hwndFocus", wintypes.HWND),
        ("hwndCapture", wintypes.HWND),
        ("hwndMenuOwner", wintypes.HWND),
        ("hwndMoveSize", wintypes.HWND),
        ("hwndCaret", wintypes.HWND),
        ("rcCaret", wintypes.RECT),
    ]


class CorvusSKKWidget(BaseWidget):
    validation_schema = CorvusSKKConfig

    def __init__(self, config: CorvusSKKConfig):
        super().__init__(config.update_interval, class_name="corvus-skk-widget")
        self.config = config
        self._label_content = config.label
        self._label_alt_content = config.label_alt
        self._show_alt = False

        # Load DLLs once
        try:
            self._user32 = ctypes.windll.user32
            self._imm32 = ctypes.windll.imm32
        except Exception:
            logging.exception("Failed to load user32 or imm32 DLLs")
            self._user32 = None
            self._imm32 = None

        # Setup container for build_widget_label
        self._widget_container_layout = QHBoxLayout()
        self._widget_container_layout.setSpacing(0)
        self._widget_container_layout.setContentsMargins(0, 0, 0, 0)
        self._widget_container = QFrame()
        self._widget_container.setLayout(self._widget_container_layout)
        self._widget_container.setProperty("class", "widget-container")
        self.widget_layout.addWidget(self._widget_container)

        # Build labels
        build_widget_label(self, self._label_content, self._label_alt_content)

        # Register callbacks
        self.register_callback("toggle_label", self.toggle_label)
        self.register_callback("update_status", self.update_status)

        # Start timer
        self.callback_timer = "update_status"
        self.start_timer()

    def toggle_label(self):
        self._show_alt = not self._show_alt
        self._update_visibility()
        self.update_status()

    def _update_visibility(self):
        for widget in self._widgets:
            widget.setVisible(not self._show_alt)
        if hasattr(self, "_widgets_alt"):
            for widget in self._widgets_alt:
                widget.setVisible(self._show_alt)

    def update_status(self):
        if not self._user32 or not self._imm32:
            return

        status_info = self._get_ime_status()

        # Update text on active widgets
        active_widgets = self._widgets_alt if self._show_alt and hasattr(self, "_widgets_alt") else self._widgets
        active_content = self._label_alt_content if self._show_alt else self._label_content

        try:
            # allow using {status}, {mode}, {label} in config string
            formatted_text = active_content.format(**status_info)
            for widget in active_widgets:
                if isinstance(widget, QLabel):
                    widget.setText(formatted_text)
        except Exception:
            # logging.exception("Failed to update CorvusSKK label") # Reduce noise
            pass

    def _get_ime_status(self):
        try:
            # 1. Try to get state via focus/foreground handles
            handles = []
            gti = GUITHREADINFO()
            gti.cbSize = ctypes.sizeof(GUITHREADINFO)
            if self._user32.GetGUIThreadInfo(0, ctypes.byref(gti)):
                if gti.hwndFocus:
                    handles.append(gti.hwndFocus)

            hwnd_fg = self._user32.GetForegroundWindow()
            if hwnd_fg:
                handles.append(hwnd_fg)

            is_open = 0
            mode = 0

            for h in handles:
                h_ime = self._imm32.ImmGetDefaultIMEWnd(h)
                if h_ime:
                    st = self._user32.SendMessageW(h_ime, WM_IME_CONTROL, IMC_GETOPENSTATUS, 0)
                    if st:
                        is_open = st
                        mode = self._user32.SendMessageW(h_ime, WM_IME_CONTROL, IMC_GETCONVERSIONMODE, 0)
                        break

            # 2. Global Fallback: Check CorvusSKKInputModeWindow visibility
            if not is_open:
                h_status = self._user32.FindWindowW("CorvusSKKInputModeWindow", None)
                if h_status and self._user32.IsWindowVisible(h_status):
                    is_open = 1
                    # If we couldn't get the specific mode, default to Hiragana
                    if mode == 0:
                        mode = 0x19  # Default Fallback

            if not is_open:
                return {"status": "OFF", "mode": "None", "label": "[EN]"}

            if mode & IME_CMODE_NATIVE:
                if mode & IME_CMODE_KATAKANA:
                    mode_str = "KANA"
                    label = "[カナ]"
                else:
                    mode_str = "HIRAGANA"
                    label = "[かな]"
            elif mode & IME_CMODE_FULLSHAPE:
                mode_str = "ZEN"
                label = "[全英]"
            else:
                mode_str = "SKK"
                label = "[SKK]"

            return {"status": "ON", "mode": mode_str, "label": label, "mode_raw": hex(mode)}
        except Exception as e:
            return {"status": "ERR", "mode": "Err", "label": "[!!]", "error": str(e)}
