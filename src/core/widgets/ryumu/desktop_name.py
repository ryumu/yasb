import logging
import re

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel

from core.utils.utilities import add_shadow
from core.utils.widgets.animation_manager import AnimationManager
from core.validation.widgets.ryumu.desktop_name import DesktopNameConfig
from core.widgets.base import BaseWidget

try:
    from pyvda import VirtualDesktop
except Exception:
    VirtualDesktop = None


class DesktopNameWidget(BaseWidget):
    validation_schema = DesktopNameConfig

    def __init__(self, config: DesktopNameConfig):
        class_name = f"desktop-name {config.class_name}".strip()
        super().__init__(
            int(config.update_interval * 1000),
            class_name=class_name,
        )
        self.config = config
        self._show_alt_label = False

        self._widget_container_layout = QHBoxLayout()
        self._widget_container_layout.setSpacing(0)
        self._widget_container_layout.setContentsMargins(0, 0, 0, 0)

        self._widget_container = QFrame()
        self._widget_container.setLayout(self._widget_container_layout)
        self._widget_container.setProperty("class", "widget-container")
        add_shadow(self._widget_container, self.config.container_shadow.model_dump())

        self.widget_layout.addWidget(self._widget_container)

        self.build_widget_label(
            self.config.label,
            self.config.label_alt,
            self.config.label_shadow.model_dump(),
        )

        self.register_callback("toggle_label", self._toggle_label)
        self.register_callback("update_label", self._update_label)

        self.callback_left = self.config.callbacks.on_left
        self.callback_middle = self.config.callbacks.on_middle
        self.callback_right = self.config.callbacks.on_right
        self.callback_timer = "update_label"

        self.start_timer()

    def _toggle_label(self):
        if self.config.animation.enabled:
            AnimationManager.animate(self, self.config.animation.type, self.config.animation.duration)

        self._show_alt_label = not self._show_alt_label

        for widget in self._widgets:
            widget.setVisible(not self._show_alt_label)
        if self.config.label_alt:
            for widget in self._widgets_alt:
                widget.setVisible(self._show_alt_label)

        self._update_label()

    def _get_current_desktop(self) -> dict[str, str | int]:
        if VirtualDesktop is None:
            return {"index": "?", "name": "Desktop"}

        try:
            current = VirtualDesktop.current()
            index = current.number
            name = (current.name or "").strip() or f"Desktop {index}"
            return {"index": index, "name": name}
        except Exception:
            logging.exception("Failed to get current virtual desktop")
            return {"index": "?", "name": "Desktop"}

    def _update_label(self):
        desktop = self._get_current_desktop()
        use_alt = self._show_alt_label and bool(self.config.label_alt)
        active_widgets = self._widgets_alt if use_alt else self._widgets
        active_label_content = self.config.label_alt if use_alt else self.config.label

        label_parts = re.split("(<span.*?>.*?</span>)", active_label_content)
        label_parts = [part for part in label_parts if part]

        widget_index = 0
        for part in label_parts:
            part = part.strip()
            if not part or widget_index >= len(active_widgets):
                continue

            widget = active_widgets[widget_index]
            if not isinstance(widget, QLabel):
                continue

            if "<span" in part and "</span>" in part:
                icon = re.sub(r"<span.*?>|</span>", "", part).strip()
                widget.setText(icon)
            else:
                try:
                    widget.setText(part.format(desktop=desktop, index=desktop["index"], name=desktop["name"]))
                except Exception:
                    widget.setText(part)

            widget_index += 1
