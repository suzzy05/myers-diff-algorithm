import sys


def read_lines(path):
    with open(path, "rb") as f:
        data = f.read()

    lines = data.split(b"\n")

    if lines and lines[-1] == b"":
        lines.pop()

    return lines


def myers_diff(a, b):
    n = len(a)
    m = len(b)

    max_d = n + m
    offset = max_d

    v = [0] * (2 * max_d + 1)
    trace = []

    for d in range(max_d + 1):
        for k in range(-d, d + 1, 2):
            index = k + offset

            if k == -d:
                x = v[index + 1]
            elif k == d:
                x = v[index - 1] + 1
            elif v[index - 1] < v[index + 1]:
                x = v[index + 1]
            else:
                x = v[index - 1] + 1

            y = x - k

            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1

            v[index] = x

            if x >= n and y >= m:
                trace.append(v.copy())
                return backtrack(trace, a, b, d, offset)

        trace.append(v.copy())

    return []


def backtrack(trace, a, b, d, offset):
    x = len(a)
    y = len(b)
    edits = []

    for current_d in range(d, 0, -1):
        v = trace[current_d - 1]

        k = x - y
        index = k + offset

        if k == -current_d:
            previous_k = k + 1
        elif k == current_d:
            previous_k = k - 1
        elif v[index - 1] < v[index + 1]:
            previous_k = k + 1
        else:
            previous_k = k - 1

        previous_x = v[previous_k + offset]
        previous_y = previous_x - previous_k

        while x > previous_x and y > previous_y:
            edits.append((" ", a[x - 1]))
            x -= 1
            y -= 1

        if x == previous_x:
            edits.append(("+", b[y - 1]))
            y -= 1
        else:
            edits.append(("-", a[x - 1]))
            x -= 1

    while x > 0 and y > 0:
        edits.append((" ", a[x - 1]))
        x -= 1
        y -= 1

    while x > 0:
        edits.append(("-", a[x - 1]))
        x -= 1

    while y > 0:
        edits.append(("+", b[y - 1]))
        y -= 1

    edits.reverse()

    return edits


def changed_ranges(old_line, new_line):
    old_chars = list(old_line.decode("utf-8"))
    new_chars = list(new_line.decode("utf-8"))

    edits = myers_diff(old_chars, new_chars)

    old_pos = 0
    new_pos = 0

    old_changed = []
    new_changed = []

    for operation, char in edits:
        if operation == " ":
            old_pos += 1
            new_pos += 1

        elif operation == "-":
            old_changed.append(old_pos)
            old_pos += 1

        elif operation == "+":
            new_changed.append(new_pos)
            new_pos += 1

    def make_ranges(positions):
        if not positions:
            return "."

        ranges = []

        start = positions[0]
        end = start + 1

        for pos in positions[1:]:
            if pos == end:
                end += 1
            else:
                ranges.append(f"{start}-{end}")
                start = pos
                end = pos + 1

        ranges.append(f"{start}-{end}")

        return ",".join(ranges)

    return make_ranges(old_changed), make_ranges(new_changed)


def main() -> int:
    if len(sys.argv) != 4 or sys.argv[1] not in ("lines", "highlight"):
        print(
            "usage: main.py lines|highlight A_PATH B_PATH",
            file=sys.stderr
        )
        return 2

    command, a_path, b_path = sys.argv[1:]

    try:
        a = read_lines(a_path)
        b = read_lines(b_path)
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    edits = myers_diff(a, b)

    if command == "lines":
        for prefix, line in edits:
            sys.stdout.buffer.write(
                prefix.encode() + line + b"\n"
            )

        return 0

    # highlight mode
    i = 0

    while i < len(edits):
        prefix, line = edits[i]

        if prefix == " ":
            sys.stdout.buffer.write(b" " + line + b"\n")
            i += 1
            continue

        # Find the complete change block.
        j = i

        while j < len(edits) and edits[j][0] in ("-", "+"):
            j += 1

        block = edits[i:j]

        deleted = []
        inserted = []

        for op, value in block:
            if op == "-":
                deleted.append(value)
            else:
                inserted.append(value)

        delete_index = 0
        insert_index = 0

        # A change block always prints all deletions first,
        # followed by all insertions.
        for op, value in block:
            sys.stdout.buffer.write(
                op.encode() + value + b"\n"
            )

            if op == "+":
                if insert_index < len(deleted):
                    old_line = deleted[insert_index]
                    new_line = value

                    old_ranges, new_ranges = changed_ranges(
                        old_line,
                        new_line
                    )

                    sys.stdout.buffer.write(
                        b"? "
                        + old_ranges.encode()
                        + b" | "
                        + new_ranges.encode()
                        + b"\n"
                    )

                insert_index += 1

        i = j

    return 0


raise SystemExit(main())