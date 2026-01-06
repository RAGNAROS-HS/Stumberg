from dataclasses import dataclass
from typing import Literal

Mode = Literal["personal", "work", "code", "fast"]

@dataclass
class AppState:
    mode: Mode = "fast"

STATE = AppState()