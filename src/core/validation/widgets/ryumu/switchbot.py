from pydantic import Field
from core.validation.widgets.base_model import CustomBaseModel, CallbacksConfig


class CallbacksSwitchBotConfig(CallbacksConfig):
    on_left: str = "toggle_label"
    on_right: str = "update_status"


class SwitchBotConfig(CustomBaseModel):
    token: str
    secret: str
    device_id: str
    class_name: str | None = None
    icon: str | None = None
    icon_path: str | None = None
    label: str | None = None
    label_alt: str = "{temp}°C / {humidity}% / {ah}g/m³"
    update_interval: int = Field(default=600000, ge=0, le=604800000)
    callbacks: CallbacksSwitchBotConfig = CallbacksSwitchBotConfig()
    tooltip_label: str = ""
