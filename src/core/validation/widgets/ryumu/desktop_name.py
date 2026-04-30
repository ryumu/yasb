from pydantic import Field

from core.validation.widgets.base_model import (
    CallbacksConfig,
    CustomBaseModel,
    KeybindingConfig,
)


class DesktopNameCallbacksConfig(CallbacksConfig):
    on_left: str = "toggle_label"


class DesktopNameConfig(CustomBaseModel):
    label: str = "{name}"
    label_alt: str = "Desktop {index}"
    update_interval: int = Field(default=1, ge=1, le=3600)
    class_name: str = ""
    keybindings: list[KeybindingConfig] = []
    callbacks: DesktopNameCallbacksConfig = DesktopNameCallbacksConfig()
