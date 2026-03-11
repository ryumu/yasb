import json
import logging
import re
import urllib.error
import urllib.request
import math
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMenu

from core.utils.tooltip import set_tooltip
from core.utils.utilities import build_widget_label
from core.validation.widgets.ryumu.yukigao import YukigaoConfig
from core.widgets.base import BaseWidget
from core.utils.win32.utilities import apply_qmenu_style


class YukigaoWidget(BaseWidget):
    validation_schema = YukigaoConfig

    def __init__(self, config: YukigaoConfig):
        super().__init__(config.update_interval, class_name=config.class_name)
        self.config: YukigaoConfig = config
        self._api_url = config.api_url
        self._target_platform = config.platform
        self._target_user_id = str(config.user_id)
        
        self._label_content = config.label
        self._label_alt_content = config.label_alt
        self._tooltip_label_content = config.tooltip_label
        self._show_alt = False

        self._ranking = "--"
        self._raw_value = "--"
        self._group_rankings = []

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

        # Register callbacks
        self.register_callback("toggle_label", self.toggle_label)
        self.register_callback("update_status", self.update_status)
        self.register_callback("show_menu", self.show_menu)

        self.callback_left = config.callbacks.on_left
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

    def show_menu(self):
        if not self._group_rankings:
            return
            
        menu = QMenu(self.window())
        
        # Apply Windows rounded corners if applicable
        from core.utils.win32.utilities import apply_qmenu_style
        apply_qmenu_style(menu)
            
        for index, (group_name, score) in enumerate(self._group_rankings):
            # Format the score
            try:
                formatted_score = f"{int(score):,}"
            except ValueError:
                formatted_score = str(score)
            
            action = QAction(f"{index + 1}位 {group_name} : {formatted_score}pt", self)
            menu.addAction(action)
            
        # Optional: styling
        # menu.setStyleSheet(...) 
        
        # Calculate menu position (bottom of the widget)
        # Using global position
        pos = self.mapToGlobal(self.rect().bottomLeft())
        menu.exec(pos)

    def update_status(self):
        try:
            req = urllib.request.Request(self._api_url, headers={"User-Agent": "yasb/mozilla"})
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    
                    found = False
                    groups = data.get("groups", {}) if isinstance(data, dict) else {}
                    
                    group_totals = []
                    my_group_users = []
                    
                    if isinstance(groups, dict):
                        for group_id, group_list in groups.items():
                            if isinstance(group_list, list):
                                group_name = "不明"
                                group_total = 0
                                
                                is_my_group = False
                                for item in group_list:
                                    if str(item.get("platform", "")) == self._target_platform and str(item.get("userId", "")) == self._target_user_id:
                                        is_my_group = True
                                        found = True
                                        try:
                                            # Format points with commas
                                            raw_val = int(item.get("rawValue", 0))
                                            self._raw_value = f"{raw_val:,}"
                                        except ValueError:
                                            self._raw_value = str(item.get("rawValue", "--"))
                                        break
                                
                                for index, item in enumerate(group_list):
                                    if index == 0:
                                        # Attempt to infer group color/name from the top user's team or fallback
                                        pass
                                    # Platform multiplier calculation
                                    raw_val = int(item.get("rawValue", 0))
                                    platform = str(item.get("platform", ""))
                                    if platform == "tiktok":
                                        point_rate = 1.8
                                    elif platform == "colorsing":
                                        point_rate = 0.3
                                    elif platform == "whowatch":
                                        point_rate = 2.0
                                    elif platform == "showroom":
                                        point_rate = 1 / 1.1
                                    elif platform == "17live":
                                        point_rate = 1 / 3.14
                                    elif platform == "mixch":
                                        point_rate = 1 / 1.14
                                    elif platform == "palmu":
                                        point_rate = 4.0
                                    else:
                                        point_rate = 1.0
                                        
                                    calc_point = round(raw_val * point_rate)
                                    group_total += calc_point
                                    
                                    if is_my_group:
                                        user_id = str(item.get("userId", ""))
                                        my_group_users.append({
                                            "platform": platform,
                                            "userId": user_id,
                                            "point": calc_point,
                                            "rawValue": raw_val
                                        })
                                
                                # In this specific battle, the group key is the team ID. 
                                # Since we don't have explicit team names in the structure except maybe inferred, 
                                # let's just map known IDs if possible, or use team ID
                                if group_id == "3027d16b":
                                    group_name = "🔴赤組"
                                elif group_id == "ed253a64":
                                    group_name = "🔵青組"
                                elif group_id == "3186657b":
                                    group_name = "🟢緑組"
                                elif group_id == "a96f3848":
                                    group_name = "🟡黄組"
                                else:
                                    group_name = f"Group {group_id[:4]}"
                                    
                                group_totals.append((group_name, group_total))
                                
                    group_totals.sort(key=lambda x: x[1], reverse=True)
                    self._group_rankings = group_totals
                    
                    if found:
                        # Sort my group participants to find ranking based on calculated point (and then rawValue)
                        my_group_users.sort(key=lambda x: (x["point"], x["rawValue"]), reverse=True)
                        for rank, u in enumerate(my_group_users):
                            if u["platform"] == self._target_platform and u["userId"] == self._target_user_id:
                                self._ranking = str(rank + 1)
                                break
                    else:
                        self._ranking = "??"
                        self._raw_value = "--"
                else:
                    logging.error(f"Yukigao API returned status code: {response.getcode()}")

        except Exception as e:
            logging.error(f"Failed to fetch Yukigao status: {e}")

        self._update_label_text()

    def _update_label_text(self):
        active_widgets = self._widgets_alt if self._show_alt and hasattr(self, "_widgets_alt") else self._widgets
        active_content = self._label_alt_content if self._show_alt else self._label_content

        if not active_content:
            return

        format_data = {"ranking": self._ranking, "rawValue": self._raw_value}

        label_parts = re.split("(<span.*?>.*?</span>)", active_content)
        label_parts = [part for part in label_parts if part]
        
        widget_index = 0
        
        try:
            for part in label_parts:
                part = part.strip()
                if part and widget_index < len(active_widgets) and isinstance(active_widgets[widget_index], QLabel):
                    if "<span" in part and "</span>" in part:
                        # Icon part - we just set text directly
                        icon_text = re.sub(r"<span.*?>|</span>", "", part).strip()
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
            logging.debug(f"Failed to update Yukigao label: {e}")
