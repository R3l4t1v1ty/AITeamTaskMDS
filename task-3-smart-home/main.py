from home import *
from smart_devices import *
from traits import *


def build_home() -> SmartHome:
    home = SmartHome("Flat 12")

    living = home.add_room("Living Room")
    kitchen = home.add_room("Kitchen")
    bedroom = home.add_room("Bedroom")
    entrance = home.add_room("Entrance")

    living.add_device(Light("chandelier", watts=60))
    living.add_device(Light("lamp", watts=12, on=False))
    living.add_device(Thermostat("thermostat"))
    living.add_device(MotionSensor("motion_sensor"))

    kitchen.add_device(HumiditySensor("humidity_sensor"))
    kitchen.add_device(Light("ceiling_light"))

    bedroom.add_device(Light("lamp", on=False))

    entrance.add_device(Lock("main_door"))
    entrance.add_device(MotionSensor("motion_sensor"))
    entrance.add_device(Camera("doorbell_cam"))

    return home


def device_in(home: SmartHome, room_name: str, device_name: str) -> SmartDevice:
    room = home.get_room(room_name)
    if room is None:
        raise LookupError(f"no room named {room_name!r}")
    device = room.get_device(device_name)
    if device is None:
        raise LookupError(f"no device named {device_name!r} in {room_name!r}")
    return device


def main() -> None:
    home = build_home()

    print("=== All devices ===\n")
    home.show_all_devices()

    print("=== Switching things ===\n")

    chandelier = device_in(home, "Living Room", "chandelier")
    if (switch := chandelier.get(Switchable)) is not None:
        switch.turn_off()
    if (dimmer := chandelier.get(Tunable)) is not None:
        dimmer.change(-20)
        print(f"chandelier off, dimmed -> {dimmer.get_percentage():.0f}%")


    door = device_in(home, "Entrance", "main_door")
    if (lock := door.get(Lockable)) is not None:
        lock.unlock()
        print(f"main_door -> {lock}")


    sensor = device_in(home, "Living Room", "motion_sensor")
    print(f"motion_sensor switchable? {sensor.get(Switchable) is not None}"
          f" | active? {sensor.is_active()}")
    print()

    home.show_active_devices()
    home.show_power_report()

    print("=== Measurements ===\n")
    home.show_all_measurements()


if __name__ == "__main__":
    main()