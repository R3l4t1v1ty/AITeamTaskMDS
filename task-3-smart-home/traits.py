from abc import ABC, abstractmethod
from typing import Callable
import random
from dataclasses import dataclass

@dataclass(frozen=True)
class Reading:
    quantity: str
    value: float
    unit: str = ""

    def __str__(self) -> str:
        return f"{self.quantity}: {self.value:.1f}{self.unit}"


class Trait(ABC):
    @abstractmethod
    def __str__(self) -> str: ...


class Switchable(Trait):
    def __init__(self, on: bool) -> None:
        self._on = on
    def turn_on(self) -> None:
        self._on = True
    def turn_off(self) -> None:
        self._on = False
    def toggle(self) -> None:
        self._on ^= True
    def is_on(self) -> bool:
        return self._on

    def __str__(self) -> str:
        return f"Switched: {self._on}"


class Measurable(Trait):
    def __init__(self, read: Callable[[],Reading]) -> None:
        self._read = read

    def measure(self) -> Reading:
        return self._read()

    def __str__(self) -> str:
        return f"Measurable"


class PowerUsage(Trait):
    def __init__(self, power: float) -> None:
        if power < 0:
            raise ValueError("power draw cannot be negative")
        self._power = power

    def get_power(self) -> float:
        return self._power

    def __str__(self) -> str:
        return f"Power usage: {self._power:g} W"


class Lockable(Trait):
    def __init__(self, locked) -> None:
        self._locked = locked

    def lock(self) -> None:
        self._locked = True

    def unlock(self) -> None:
        self._locked = False

    def toggle(self) -> None:
        self._locked ^= True

    def is_locked(self) -> bool:
        return self._locked

    def __str__(self) -> str:
        return f"Locked: {self._locked}"


class Tunable(Trait):
    def __init__(self, value: float, floor: float = 0.0, roof: float = 100.0) -> None:
        if floor > roof:
            raise ValueError("floor must not exceed roof")
        self._floor = floor
        self._roof = roof
        self._value = self._clamp(value)

    def _clamp(self, value: float) -> float:
        return min(max(value, self._floor), self._roof)

    def set_value(self, value: float) -> float:
        self._value = self._clamp(value)
        return self._value

    def change(self, delta: float) -> float:
        return self.set_value(self._value + delta)

    def get_value(self) -> float:
        return self._value

    def get_percentage(self) -> float:
        if self._floor == self._roof:
            return 100.0
        return (self._value - self._floor) / (self._roof - self._floor) * 100

    def __str__(self) -> str:
        return f"Tunable: {self._value} ({self.get_percentage():.0f}%)"


def read_temperature() -> Reading:
    return Reading("Temperature", 20 + random.gauss(0, 5), " C")


def read_humidity() -> Reading:
    return Reading("Humidity", 40 + random.gauss(0, 10), "%")


def read_motion() -> Reading:
    return Reading("Motion", float(random.randint(0, 1)))
