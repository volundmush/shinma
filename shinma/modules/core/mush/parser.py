import re
from typing import List, Tuple


def split_unescaped_text(text: str, split_at=" ", ignore_empty: bool = False, limit=None) -> List[str]:
    escaped = False
    paren_depth = 0
    square_depth = 0
    curly_depth = 0

    remaining = text
    while len(remaining):
        found = None

        for i, c in enumerate(remaining):
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == "{":
                curly_depth += 1
            elif c == "}" and curly_depth > 0:
                curly_depth -= 1
            elif c == "[":
                square_depth += 1
            elif c == "]" and square_depth > 0:
                square_depth -= 1
            elif c == "(":
                paren_depth += 1
            elif c == ")" and paren_depth > 0:
                paren_depth -= 1
            elif c == split_at:
                found = i
                break
            else:
                pass

        if found is None:
            yield remaining
            remaining = ''
        else:
            before = remaining[:found]
            after = remaining[found:]
            remaining = after
            yield before


def identify_squares(text: str) -> List[Tuple[int, int]]:
    escaped = False
    idx = list()
    depth = 0

    for i, c in enumerate(text):
        if escaped:
            escaped = False
        else:
            if c == "[":
                if depth == 0:
                    idx.append(i)
                depth += 1
            elif c == "]" and depth > 0:
                depth -= 1
                if depth == 0:
                    idx.append(i)
            elif c == "\\":
                escaped = True
            else:
                pass

    # if it's not even, we don't count the unfinished square.
    if len(idx) % 2 == 1:
        idx.pop()

    it = iter(idx)
    out = list()
    for i in it:
        out.append((i, next(it)))
    return out