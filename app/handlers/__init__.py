# Регистрируем под-роутеры здесь
from .assistance import router as chat_router
from .lead_fsm import router as lead_router

__all__ = ["chat_router", "lead_router"]
