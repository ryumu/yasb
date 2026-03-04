from pydantic import Field
from core.validation.widgets.base_model import CustomBaseModel, CallbacksConfig

class CallbacksYukigaoConfig(CallbacksConfig):
    on_left: str = "update_status"
    on_right: str = "toggle_label"

class YukigaoConfig(CustomBaseModel):
    class_name: str | None = None
    label: str = "❄️{ranking}位{rawValue}P"
    label_alt: str = "❄️{ranking}位{rawValue}P"
    update_interval: int = Field(default=1800000, ge=0, le=604800000)
    api_url: str = "https://321-rankings.vercel.app/api/battle-live?battleId=akaaokimidoribattle2026"
    platform: str = "pococha"
    user_id: int = 9634862
    callbacks: CallbacksYukigaoConfig = CallbacksYukigaoConfig()
    tooltip_label: str = ""
