
line = "z2600.550701.00x"
line = "z0300.50x"
if line[0] != "z" or line[-1] != "x":
    exit()

offset = 1
while line[offset] != "x":
    motor_idx_str = line[offset : offset + 2]

    motor_idx = int(motor_idx_str)
    speed_str = line[offset + 2 : offset + 7]
    speed = float(speed_str)
    offset += 7
    print(f"Got motor idx {motor_idx_str} at {speed_str}")
