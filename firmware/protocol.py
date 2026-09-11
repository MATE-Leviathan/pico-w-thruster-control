ID_WIDTH = 2
VALUE_WIDTH = 5
UPDATE_WIDTH = ID_WIDTH + VALUE_WIDTH


def encode_update(output_id, value):
    update = f"{int(output_id):02d}{float(value):05.2f}"
    if len(update) != UPDATE_WIDTH:
        raise ValueError(f"value does not fit the {VALUE_WIDTH} character field")
    return update


def encode_commands(updates):
    return "z" + "".join(encode_update(i, v) for i, v in updates) + "x\n"


def decode_frame(frame):
    text = frame.strip()
    if len(text) < UPDATE_WIDTH + 2 or text[0] != "z" or text[-1] != "x":
        raise ValueError("frame must start with 'z' and end with 'x'")

    body = text[1:-1]
    if len(body) % UPDATE_WIDTH != 0:
        raise ValueError(f"frame body must be a multiple of {UPDATE_WIDTH} characters")

    updates = []
    for offset in range(0, len(body), UPDATE_WIDTH):
        chunk = body[offset : offset + UPDATE_WIDTH]
        id_text = chunk[:ID_WIDTH]
        value_text = chunk[ID_WIDTH:]
        updates.append((int(id_text), float(value_text)))
    return updates
