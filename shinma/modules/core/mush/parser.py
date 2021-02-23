import re
from typing import List, Tuple


def split_unescaped_text(text: str, split_at=" ", ignore_empty: bool = False, limit=None) -> List[str]:
    escaped = False
    paren_depth = 0
    square_depth = 0
    curly_depth = 0
    split_count = 0

    idx = [0]
    split = []

    for i, c in enumerate(text):
        if escaped:
            escaped = False
        else:
            if c == "\\":
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
                idx.append(i)
                idx.append(i+1)
                split_count += 1
                if split_count == limit:
                    break
            else:
                pass

    idx.append(len(text))

    it = iter(idx)
    if ignore_empty:
        for i in it:
            if found := text[i:next(it)]:
                split.append(found)
    else:
        for i in it:
            split.append(text[i:next(it)])
    return split


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