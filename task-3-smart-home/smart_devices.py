from __future__ import annotations
from traits import *
from typing import TypeVar, Type, Callable

T = TypeVar("T", bound=Trait)

class SmartDevice:
    kind: str = "device"

    def __init__(self, name: str) -> None:
        self.name = name
        self._traits: dict[type[Trait], Trait] = {}

    def add(self, trait: Trait) -> SmartDevice:
        self._traits[type(trait)] = trait
        return self

    def get(self, trait_type: type[T]) -> T | None:
        return self._traits.get(trait_type)

    def has(self, trait_type: type[Trait]) -> bool:
        return trait_type in self._traits

    def is_active(self) -> bool:
        switch = self.get(Switchable)
        return switch.is_on() if switch else True

    def power_draw(self) -> float:
        power = self.get(PowerUsage)
        return power.get_power() if power else 0.0

    def measure(self) -> Reading | None:
        sensor = self.get(Measurable)
        return sensor.measure() if sensor else None

    def __str__(self) -> str:
        parts = [f"{self.name} ({self.kind})"]
        parts += [f"- {trait}" for trait in self._traits.values()]
        return "\n".join(parts)


class Light(SmartDevice):
    kind = "light"

    def __init__(self, name: str, watts: float = 20, on: bool = True, brightness: float = 50.0) -> None:
        super().__init__(name)
        self.add(Switchable(on)).add(PowerUsage(watts)).add(Tunable(brightness))


class Thermostat(SmartDevice):
    kind = "thermostat"

    def __init__(self, name: str, watts: float = 5, on: bool = True, target: float = 22.0) -> None:
        super().__init__(name)
        self.add(Switchable(on)).add(PowerUsage(watts)).add(Measurable(read_temperature)).add(Tunable(target, floor=10.0, roof=30.0))


class Camera(SmartDevice):
    kind = "camera"

    def __init__(self, name: str, watts: float = 10, on: bool = True) -> None:
        super().__init__(name)
        self.add(Switchable(on)).add(PowerUsage(watts))


class Lock(SmartDevice):
    kind = "lock"

    def __init__(self, name: str, watts: float = 1, locked: bool = True) -> None:
        super().__init__(name)
        self.add(Lockable(locked)).add(PowerUsage(watts))


class MotionSensor(SmartDevice):
    kind = "motion sensor"

    def __init__(self, name: str, watts: float = 1) -> None:
        super().__init__(name)
        self.add(Measurable(read_motion)).add(PowerUsage(watts))


class HumiditySensor(SmartDevice):
    kind = "humidity sensor"

    def __init__(self, name: str, watts: float = 1) -> None:
        super().__init__(name)
        self.add(Measurable(read_humidity)).add(PowerUsage(watts))
