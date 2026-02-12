import base64
import hashlib
import hmac
import json
import logging
import math
import time
import re
import urllib.error
import urllib.request
import uuid

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from core.utils.tooltip import set_tooltip
from core.utils.utilities import build_widget_label
from core.validation.widgets.ryumu.switchbot import SwitchBotConfig
from core.widgets.base import BaseWidget


class SwitchBotWidget(BaseWidget):
    validation_schema = SwitchBotConfig

    def __init__(self, config: SwitchBotConfig):
        super().__init__(config.update_interval, class_name=config.class_name)
        self.config = config
        self._token = config.token
        self._secret = config.secret
        self._device_id = config.device_id
        self._label_content = config.label
        self._label_alt_content = config.label_alt
        self._tooltip_label_content = config.tooltip_label
        self._show_alt = False

        self._temp = "--"
        self._humidity = "--"
        self._ah = "--"

        # Setup container for build_widget_label
        self._widget_container_layout = QHBoxLayout()
        self._widget_container_layout.setSpacing(0)
        self._widget_container_layout.setContentsMargins(0, 0, 0, 0)
        self._widget_container = QFrame()
        self._widget_container.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._widget_container.setLayout(self._widget_container_layout)
        self._widget_container.setProperty("class", "widget-container")
        self.widget_layout.addWidget(self._widget_container)

        # Build labels
        build_widget_label(self, self._label_content, self._label_alt_content)

        # Handle image icons
        self._image_label = None
        self._image_label_alt = None

        if self.config.icon_path:
            self._image_label = QLabel()
            self._set_icon_pixmap(self._image_label, self.config.icon_path)
            self._widget_container_layout.insertWidget(0, self._image_label)
            self._widgets.insert(0, self._image_label)

            if hasattr(self, "_widgets_alt"):
                self._image_label_alt = QLabel()
                self._set_icon_pixmap(self._image_label_alt, self.config.icon_path)
                self._widget_container_layout.insertWidget(0, self._image_label_alt)
                self._widgets_alt.insert(0, self._image_label_alt)
                self._image_label_alt.hide()

        # Register callbacks
        self.register_callback("toggle_label", self.toggle_label)
        self.register_callback("update_status", self.update_status)

        self.callback_left = config.callbacks.on_left
        self.callback_middle = config.callbacks.on_middle
        self.callback_right = config.callbacks.on_right

        # Start timer
        self.callback_timer = "update_status"
        self.start_timer()

        # Initial update
        self.update_status()

    def toggle_label(self):
        self._show_alt = not self._show_alt
        self._update_visibility()
        self._update_label_text()

    def _update_visibility(self):
        for widget in self._widgets:
            widget.setVisible(not self._show_alt)
        if hasattr(self, "_widgets_alt"):
            for widget in self._widgets_alt:
                widget.setVisible(self._show_alt)

    def _get_auth_headers(self):
        nonce = str(uuid.uuid4())
        t = int(round(time.time() * 1000))
        string_to_sign = "{}{}{}".format(self._token, t, nonce)

        string_to_sign_bytes = bytes(string_to_sign, "utf-8")
        secret_bytes = bytes(self._secret, "utf-8")

        sign = base64.b64encode(hmac.new(secret_bytes, msg=string_to_sign_bytes, digestmod=hashlib.sha256).digest())
        sign_str = str(sign, "utf-8")

        return {
            "Authorization": self._token,
            "Content-Type": "application/json",
            "charset": "utf8",
            "t": str(t),
            "sign": sign_str,
            "nonce": nonce,
        }

    def _calculate_absolute_humidity(self, temp, humidity):
        if temp is None or humidity is None:
            return 0.0
        try:
            e = 6.1078 * math.pow(10, (7.5 * temp) / (temp + 237.3)) * (humidity / 100.0)
            ah = 217 * (e / (temp + 273.15))
            return round(ah, 2)
        except Exception:
            return 0.0

    def update_status(self):
        try:
            headers = self._get_auth_headers()
            url = f"https://api.switch-bot.com/v1.1/devices/{self._device_id}/status"

            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    body = data.get("body", {})
                    temp = body.get("temperature")
                    humidity = body.get("humidity")

                    if temp is not None and humidity is not None:
                        self._temp = temp
                        self._humidity = humidity
                        self._ah = self._calculate_absolute_humidity(temp, humidity)
                else:
                    logging.error(f"SwitchBot API returned status code: {response.getcode()}")

        except Exception as e:
            logging.error(f"Failed to fetch SwitchBot status: {e}")

        self._update_label_text()

    def _set_icon_pixmap(self, label: QLabel, icon_path: str):
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            # Try to get bar height, fallback to 24
            height = self.bar.height() if self.bar else 24
            scaled_pixmap = pixmap.scaledToHeight(height - 4 if height > 4 else height, Qt.TransformationMode.SmoothTransformation)
            label.setPixmap(scaled_pixmap)
        else:
            logging.error(f"Failed to load SwitchBot icon: {icon_path}")

    def _update_label_text(self):
        active_widgets = self._widgets_alt if self._show_alt and hasattr(self, "_widgets_alt") else self._widgets
        active_content = self._label_alt_content if self._show_alt else self._label_content

        if not active_content:
            return

        icon = self.config.icon if self.config.icon else "\ue30d"

        format_data = {"temp": self._temp, "humidity": self._humidity, "ah": self._ah, "icon": icon}

        label_parts = re.split("(<span.*?>.*?</span>)", active_content)
        label_parts = [part for part in label_parts if part]
        
        widget_index = 0
        
        # Skip image label if it's at the start
        if (self._show_alt and self._image_label_alt) or (not self._show_alt and self._image_label):
            widget_index = 1

        try:
            for part in label_parts:
                part = part.strip()
                if part and widget_index < len(active_widgets) and isinstance(active_widgets[widget_index], QLabel):
                    if "<span" in part and "</span>" in part:
                        # Icon part
                        icon_text = re.sub(r"<span.*?>|</span>", "", part).strip()
                        # If icon_text contains a placeholder, format it
                        if "{" in icon_text and "}" in icon_text:
                            icon_text = icon_text.format(**format_data)
                        active_widgets[widget_index].setText(icon_text)
                    else:
                        # Text part
                        formatted_text = part.format(**format_data)
                        active_widgets[widget_index].setText(formatted_text)
                    widget_index += 1

            if self._tooltip_label_content:
                tooltip_text = self._tooltip_label_content.format(**format_data)
                set_tooltip(self, tooltip_text)

        except Exception as e:
            logging.debug(f"Failed to update SwitchBot label: {e}")
