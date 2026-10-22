def validate(config):
    outputs = [
        (f"{group}.{name}", int(entry["pin"]), 50)
        for group in ("thrusters", "aux_servos")
        for name, entry in (config.get(group) or {}).items()
    ]

    if actuator := config.get("actuator"):
        outputs.append(("actuator", int(actuator["speed_pin"]), int(actuator["pwm_freq"])))

    used = {}
    for name, pin, freq in outputs:
        slice_id, channel = (pin // 2) % 8, pin % 2
        label = f"{name} (GP{pin})"

        if (slice_id, channel) in used:
            raise ValueError(f"{label} conflicts with {used[slice_id, channel][0]}")

        other = used.get((slice_id, 1 - channel))
        if other and other[1] != freq:
            raise ValueError(
                f"{label} shares PWM slice {slice_id} with {other[0]} "
                f"at different frequencies ({freq} vs {other[1]} Hz)"
            )

        used[slice_id, channel] = (label, freq)

