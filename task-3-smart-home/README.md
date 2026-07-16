# Task 3 — Smart Home

A small object-oriented smart home system

House has rooms, rooms have smart devices, smart devices have traits.

## Running

```
python main.py
```

Requires Python 3.14+

Requires pytest for test

## Files

| File | Contents                                         |
|---|--------------------------------------------------|
| `traits.py` | `Trait`, `Reading`, and the concrete capabilities |
| `smart_devices.py` | `SmartDevice` base + concrete devices            |
| `home.py` | `Room`, `SmartHome`          |
| `main.py` | Demo                                             |

## Design

The chosen design for smart devices is composition.
Each smart device contains traits as separate objects.
For example, smart lamp has switchable trait, power usage trait and 
tunable trait. Now, something else, a camera only has switchable and power usage
traits, while lock doesn't have switchable trait, it always works, and it has lockable
trait instead.

This way we can easily construct a smart device with any combination of traits.

Instead of having factory functions, each new smart device is subclass of SmartDevice
and the only thing we need to do is add traits we want to it. Devices have no
behavior.

Measurable trait measures input through a callable. It's a simulation of real reading. 


## OOP principles

- **Encapsulation** - it's python, but for optimal use, there is no need to ever cross
object boundaries.
- **Single responsibility** - traits do the job, devices contain and handle traits, 
rooms contain and handle devices and home contains rooms and handles aggregation.
- **Open/closed** - new device types and new capabilities are added by writing
  new classes. 
- **Liskov** - device subclasses add no behavior, so any
  `SmartDevice` is substitutable everywhere.
- **Interface segregation** - this is the whole point of splitting the traits, a
  `Lock` is never forced to implement `is_on()`.
- **Dependency inversion** - `Room` and `SmartHome` depend on the `Trait` abstraction, not
on `SmartDevice`.


## Assumptions

- A device with no `Switchable` is always active.
- Power is instantaneous draw in watts, if a device doesn't have `PowerUsage`
it's power draw is 0
- A switched-off sensor produces no reading
- Device names and room names are unique within their scope
- At most one trait of a given type per device.

## Limitations and trade-offs

- `get()` is a runtime lookup, meaning typos are caught at runtime and it should
be followed with `is None` check
- No persistence, concurrency or device I/O. Everything is in memory and
  single-threaded while readings are simulated.
- Rooms are just containers. There is no adjacency between rooms.
- Devices are addressed by string name.
- Traits are keyed by traits type, meaning one device cannot have more than
one of the same trait.
