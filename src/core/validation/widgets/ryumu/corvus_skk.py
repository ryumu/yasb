from pydantic import Field
from core.validation.widgets.base_model import CustomBaseModel, CallbacksConfig


class CallbacksCorvusSKKConfig(CallbacksConfig):
    on_left: str = "do_nothing"
    on_middle: str = "do_nothing"
    on_right: str = "do_nothing"


class CorvusSKKConfig(CustomBaseModel):
    label: str = "SKK: {status}"
    label_alt: str = "{status}"
    update_interval: int = Field(default=1000, ge=100, le=60000)
    callbacks: CallbacksCorvusSKKConfig = CallbacksCorvusSKKConfig()
