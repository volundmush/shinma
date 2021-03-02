import re
from typing import List, Tuple


def split_unescaped_text(text: str, split_at=" ", ignore_empty: bool = False, limit=None) -> List[str]:
    escaped = False
    paren_depth = 0
    square_depth = 0
    curly_depth = 0

    out = ''
    for i, c in enumerate(text):
        if escaped:
            escaped = False
        if c == "\\":
            escaped = True
        elif c == "{" and not escaped:
            curly_depth += 1
        elif c == "}" and not escaped and curly_depth > 0:
            curly_depth -= 1
        elif c == "[" and not escaped:
            square_depth += 1
        elif c == "]" and not escaped and square_depth > 0:
            square_depth -= 1
        elif c == "(" and not escaped:
            paren_depth += 1
        elif c == ")" and not escaped and paren_depth > 0:
            paren_depth -= 1
        elif c == split_at and not escaped and max(curly_depth, square_depth, paren_depth) == 0:
            yield out
            out = ''
            continue
        out += c

    if out:
        yield out


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