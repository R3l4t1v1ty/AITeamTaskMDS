from __future__ import annotations
from typing import TypeVar
from smart_devices import SmartDevice
from traits import Measurable, PowerUsage, Reading, Switchable, Trait

T = TypeVar("T", bound=Trait)

class Room:
    def __init__(self, name: str) -> None:
        self.name = name
        self._devices: dict[str, SmartDevice] = {}

    def add_device(self, device: SmartDevice, overwrite: bool = False) -> SmartDevice:
        if device.name in self._devices and not overwrite:
            raise KeyError(f"{self.name!r} already has a device named {device.name!r}")
        self._devices[device.name] = device
        return device

    def get_device(self, name: str) -> SmartDevice | None:
        return self._devices.get(name)

    @property
    def devices(self) -> list[SmartDevice]:
        return list(self._devices.values())

    def devices_with(self, trait_type: type[T]) -> list[SmartDevice]:
        return [d for d in self._devices.values() if d.has(trait_type)]

    def active_devices(self) -> list[SmartDevice]:
        return [d for d in self._devices.values() if d.is_active()]

    def total_power(self) -> float:
        return sum(d.power_draw() for d in self._devices.values())

    def measurements(self) -> list[tuple[SmartDevice, Reading]]:
        out: list[tuple[SmartDevice, Reading]] = []
        for device in self.devices_with(Measurable):
            reading = device.measure()
            if reading is not None:  # skip sensors that are switched off
                out.append((device, reading))
        return out

    def _switches(self) -> list[Switchable]:
        switches = (d.get(Switchable) for d in self._devices.values())
        return [s for s in switches if s is not None]

    def turn_all_on(self) -> None:
        for switch in self._switches():
            switch.turn_on()

    def turn_all_off(self) -> None:
        for switch in self._switches():
            switch.turn_off()

    def show_devices(self) -> None:
        print(f"[{self.name}]")
        for device in self._devices.values():
            print(f"{device}")
        print()

    def show_measurements(self) -> None:
        print(f"[{self.name}] measurements")
        readings = self.measurements()
        if not readings:
            print("(none)")
        for device, reading in readings:
            print(f"{device.name}: {reading}")
        print()

    def __str__(self) -> str:
        return f"Room({self.name}, {len(self._devices)} devices)"


class SmartHome:
    def __init__(self, name: str = "Home") -> None:
        self.name = name
        self._rooms: dict[str, Room] = {}

    def add_room(self, name: str) -> Room:
        if name in self._rooms:
            raise KeyError(f"room {name!r} already exists")
        self._rooms[name] = Room(name)
        return self._rooms[name]

    def get_room(self, name: str) -> Room | None:
        return self._rooms.get(name)

    @property
    def rooms(self) -> list[Room]:
        return list(self._rooms.values())

    def devices(self) -> list[SmartDevice]:
        return [d for room in self._rooms.values() for d in room.devices]

    def active_devices(self) -> list[tuple[Room, SmartDevice]]:
        return [(room, d) for room in self._rooms.values() for d in room.active_devices()]

    def total_power(self) -> float:
        return sum(room.total_power() for room in self._rooms.values())

    def measurements(self) -> list[tuple[Room, SmartDevice, Reading]]:
        return [(room, d, r)
                for room in self._rooms.values()
                for d, r in room.measurements()]

    def show_all_devices(self) -> None:
        for room in self._rooms.values():
            room.show_devices()

    def show_all_measurements(self) -> None:
        for room in self._rooms.values():
            room.show_measurements()

    def show_active_devices(self) -> None:
        print("Active devices")
        for room, device in self.active_devices():
            draw = device.power_draw()
            suffix = f"{draw:g} W" if device.has(PowerUsage) else "no power"
            print(f"{room.name} / {device.name} ({device.kind}) - {suffix}")
        print()

    def show_power_report(self) -> None:
        print("Power consumption")
        for room in self._rooms.values():
            print(f"{room.name}: {room.total_power():g} W")
        print(f"TOTAL: {self.total_power():g} W\n")
