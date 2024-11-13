"""
Usage:
$ python -m strptime "2030-01-24 05:45"
%Y-%m-%d %H:%M
"""
from datetime import datetime
import re
import sys
from warnings import filterwarnings


__version__ = "0.4.0"

NO_FORMAT="\033[0m"
F_BOLD="\033[1m"

PARTS_RE = re.compile(r"""
    (
        # %S%z matching
        [0-9]{2}
        [+-] \d{2} :? \d{2}
    |
        [A-Za-z0-9]+
    )
""", flags=re.VERBOSE)

specific_custom_formats = [
    "%m/%d/%Y %I:%M %p",
    "%m/%d/%Y",
    "%m/%d/%y",
    "%m-%d-%Y",
    "%c",
]

generic_formats = {
    1: [
        ["%Y%m%dT%H%M%SZ"],                                 # 20300124T054513Z
        ["%A"],                                             # Thursday
        ["%a"],                                             # Thu
        ["%b"],                                             # Jan
        ["%B"],                                             # January
        ["%d"],                                             # 24
        ["%Y"],                                             # 2024
    ],
    2: [
        ["%Y", "%j"],                                       # 2024 24 (day of year)
        ["%b", "%d"],                                       # Jan 24
        ["%B", "%d"],                                       # January 24
        ["%d", "%b"],                                       # 24 Jan
        ["%d", "%B"],                                       # 24 January
        ["%b", "%Y"],                                       # Jan 2024
        ["%a", "%b"],                                       # Thu Jan
        ["%a", "%B"],                                       # Thu January
        ["%A", "%b"],                                       # Thursday Jan
        ["%A", "%B"],                                       # Thursday January
        ["%H", "%M"],                                       # 05 45
        ["%I", "%M%p"],                                     # 05 45AM
    ],
    3: [
        ["%Y", "%m", "%d"],                                 # 2030 01 24
        ["%B", "%d", "%Y"],                                 # January 24 2030
        ["%d", "%b", "%Y"],                                 # 24 Jan 2030
        ["%b", "%d", "%Y"],                                 # Jan 24 2030
        ["%d", "%m", "%Y"],                                 # 23 01 2024
        ["%H", "%M", "%S"],                                 # 05 45 13
        ["%a", "%b", "%d"],                                 # Thu Jan 24
        ["%A", "%B", "%d"],                                 # Thursday January 24
        ["%A", "%b", "%d"],                                 # Thursday Jan 24
        ["%a", "%B", "%d"],                                 # Thu January 24
        ["%a", "%d", "%b"],                                 # Thu 24 Jan
        ["%A", "%d", "%B"],                                 # Thursday 24 January
        ["%A", "%d", "%b"],                                 # Thursday 24 Jan
        ["%a", "%d", "%B"],                                 # Thu 24 January
        ["%H", "%M", "%Z"],                                 # 05 45 PST
        ["%I", "%M", "%p"],                                 # 05 45 AM
        ["%H", "%M", "%S%z"],                               # 05 45 13-0700
        ["%I", "%M", "%S%p"],                               # 05 45 13AM
    ],
    4: [
        ["%a", "%b", "%d", "%Y"],                           # Thu Jan 24 2030
        ["%A", "%B", "%d", "%Y"],                           # Thursday January 24 2030
        ["%A", "%b", "%d", "%Y"],                           # Thursday Jan 24 2030
        ["%a", "%B", "%d", "%Y"],                           # Thu January 24 2030
        ["%A", "%d", "%B", "%Y"],                           # Thursday 24 January 2030
        ["%a", "%d", "%b", "%Y"],                           # Thu 24 Jan 2030
        ["%H", "%M", "%S", "%Z"],                           # 05 45 13 PST
        ["%I", "%M", "%S", "%p"],                           # 05 45 13 AM
    ],
    5: [
        ["%Y", "%m", "%dT%H", "%M", "%S%z"],                # 2030 01 24T05 45 13-0700
        ["%Y", "%m", "%dT%H", "%M", "%S"],                  # 2030 01 24T05 45 13
        ["%d", "%b", "%Y", "%H", "%M"],                     # 24 Jan 2030 05 45
        ["%b", "%d", "%Y", "%H", "%M"],                     # Jan 24 2030 05 45
        ["%Y", "%m", "%d", "%H", "%M"],                     # 2030 01 24 05 45
        ["%Y", "%m", "%d", "%I", "%M%p"],                   # 2030 01 24 24 05 45AM
        ["%d", "%m", "%Y", "%H", "%M"],                     # 24 01 2030 05 45
        ["%b", "%d", "%Y", "%I", "%M%p"],                   # Jan 24 2030 05 45AM
    ],
    6: [
        ["%b", "%d", "%Y", "%H", "%M", "%S"],               # Jan 24 2030 05 45 13
        ["%Y", "%m", "%d", "%H", "%M", "%S"],               # 2030 01 24 05 45 13
        ["%d", "%m", "%Y", "%H", "%M", "%S"],               # 24 01 2030 05 45 13
        ["%Y", "%m", "%d", "%H", "%M", "%S%z"],             # 2030 01 24 05 45 13PST
        ["%Y", "%m", "%d", "%H", "%M", "%SZ"],              # 2030 01 24 05 45 13Z
        ["%a", "%d", "%b", "%Y", "%H", "%M"],               # Thu 24 Jan 2030 05 45
        ["%a", "%d", "%b", "%Y", "%I", "%M%p"],             # Thu 24 Jan 2030 05 45AM
        ["%m", "%d", "%Y", "%I", "%M", "%p"],               # 01 24 2030 05 45 AM
        ["%d", "%b", "%Y", "%H", "%M", "%S"],               # 24 Jan 2030 05 45 13
        ["%Y", "%m", "%dT%H", "%M", "%S", "%fZ"],           # 2030 01 24T05 45 13 337392Z
        ["%Y", "%m", "%dT%H", "%M", "%S", "%f"],            # 2030 01 24T05 45 13 337392
        ["%b", "%d", "%Y", "%I", "%M", "%p"],               # Jan 24 2030 05 45 AM
        ["%B", "%d", "%Y", "%H", "%M", "%S"],               # January 24 2030 05 45 13
        ["%A", "%d", "%B", "%Y", "%H", "%M"],               # Thursday 24 January 2030 05 45
        ["%A", "%d", "%B", "%Y", "%I", "%M%p"],             # Thursday 24 January 2030 05 45AM
        ["%d", "%B", "%Y", "%H", "%M", "%S"],               # 24 January 2030 05 45 13
        ["%B", "%d", "%Y", "%I", "%M", "%p"],               # January 24 2030 05 45 AM
        ["%A", "%d", "%b", "%Y", "%H", "%M"],               # Thursday 24 Jan 2030 05 45
        ["%A", "%d", "%b", "%Y", "%I", "%M%p"],             # Thursday 24 Jan 2030 05 45AM
    ],
    7: [
        ["%a", "%d", "%b", "%Y", "%H", "%M", "%S"],         # Thu 24 Jan 2030 05 45 13
        ["%a", "%b", "%d", "%Y", "%H", "%M", "%S"],         # Thu Jan 24 2030 05 45 13
        ["%m", "%d", "%Y", "%I", "%M", "%S", "%p"],         # 01 24 2030 05 45 13 AM
        ["%b", "%d", "%Y", "%H", "%M", "%S", "%Z"],         # Jan 24 2030 05 45 13 PST
        ["%d", "%b", "%Y", "%H", "%M", "%S", "%Z"],         # 24 Jan 2030 05 45 13 PST
        ["%Y", "%m", "%d", "%H", "%M", "%S", "%f"],         # 2030 01 24 05 45 13 337392
        ["%A", "%d", "%B", "%Y", "%H", "%M", "%S"],         # Thursday 24 January 2030 05 45 13
        ["%A", "%B", "%d", "%Y", "%H", "%M", "%S"],         # Thursday January 24 2030 05 45 13
        ["%A", "%d", "%b", "%Y", "%H", "%M", "%S"],         # Thursday 24 Jan 2030 05 45 13
        ["%A", "%b", "%d", "%Y", "%H", "%M", "%S"],         # Thursday Jan 24 2030 05 45 13
        ["%a", "%d", "%B", "%Y", "%H", "%M", "%S"],         # Thu 24 January 2030 05 45 13
        ["%a", "%B", "%d", "%Y", "%H", "%M", "%S"],         # Thu January 24 2030 05 45 13
        ["%d", "%B", "%Y", "%H", "%M", "%S", "%Z"],         # 24 January 2030 05 45 13 PST
        ["%A", "%d", "%B", "%Y", "%I", "%M", "%S%p"],       # Thursday 24 January 2030 05 45 13AM
        ["%A", "%B", "%d", "%Y", "%I", "%M", "%S%p"],       # Thursday January 24 2030 05 45 13AM
        ["%A", "%d", "%b", "%Y", "%I", "%M", "%S%p"],       # Thursday 24 Jan 2030 05 45 13AM
        ["%A", "%b", "%d", "%Y", "%I", "%M", "%S%p"],       # Thursday Jan 24 2030 05 45 13AM
        ["%a", "%d", "%B", "%Y", "%I", "%M", "%S%p"],       # Thu 24 January 2030 05 45 13AM
        ["%a", "%B", "%d", "%Y", "%I", "%M", "%S%p"],       # Thu January 24 2030 05 45 13AM
        ["%a", "%d", "%b", "%Y", "%I", "%M", "%p"],         # Thu 24 Jan 2030 05 45 AM
        ["%A", "%d", "%B", "%Y", "%I", "%M", "%p"],         # Thursday 24 January 2030 05 45 AM
        ["%A", "%B", "%d", "%Y", "%I", "%M", "%p"],         # Thursday January 24 2030 05 45 AM
        ["%A", "%d", "%b", "%Y", "%I", "%M", "%p"],         # Thursday 24 Jan 2030 05 45 AM
        ["%A", "%b", "%d", "%Y", "%I", "%M", "%p"],         # Thursday Jan 24 2030 05 45 AM
        ["%a", "%d", "%B", "%Y", "%I", "%M", "%p"],         # Thu 24 January 2030 05 45 AM
        ["%a", "%B", "%d", "%Y", "%I", "%M", "%p"],         # Thu January 24 2030 05 45 AM
    ],
    8: [
        ["%a", "%d", "%b", "%Y", "%H", "%M", "%S", "%Z"],   # Thu 24 Jan 2030 05 45 13 PST
        ["%a", "%b", "%d", "%Y", "%H", "%M", "%S", "%Z"],   # Thu Jan 24 2030 05 45 13 PST
        ["%A", "%d", "%B", "%Y", "%H", "%M", "%S", "%Z"],   # Thursday 24 January 2030 05 45 13 PST
        ["%A", "%B", "%d", "%Y", "%H", "%M", "%S", "%Z"],   # Thursday January 24 2030 05 45 13 PST
        ["%A", "%d", "%b", "%Y", "%H", "%M", "%S", "%Z"],   # Thursday 24 Jan 2030 05 45 13 PST
        ["%A", "%b", "%d", "%Y", "%H", "%M", "%S", "%Z"],   # Thursday Jan 24 2030 05 45 13 PST
        ["%a", "%d", "%B", "%Y", "%H", "%M", "%S", "%Z"],   # Thu 24 January 2030 05 45 13 PST
        ["%a", "%B", "%d", "%Y", "%H", "%M", "%S", "%Z"],   # Thu January 24 2030 05 45 13 PST
        ["%a", "%d", "%b", "%Y", "%I", "%M", "%S", "%p"],   # Thu 24 Jan 2030 05 45 13 AM
        ["%a", "%b", "%d", "%Y", "%I", "%M", "%S", "%p"],   # Thu Jan 24 2030 05 45 13 AM
        ["%A", "%d", "%B", "%Y", "%I", "%M", "%S", "%p"],   # Thursday 24 January 2030 05 45 13 AM
        ["%A", "%B", "%d", "%Y", "%I", "%M", "%S", "%p"],   # Thursday January 24 2030 05 45 13 AM
        ["%A", "%d", "%b", "%Y", "%I", "%M", "%S", "%p"],   # Thursday 24 Jan 2030 05 45 13 AM
        ["%A", "%b", "%d", "%Y", "%I", "%M", "%S", "%p"],   # Thursday Jan 24 2030 05 45 13 AM
        ["%a", "%d", "%B", "%Y", "%I", "%M", "%S", "%p"],   # Thu 24 January 2030 05 45 13 AM
        ["%a", "%B", "%d", "%Y", "%I", "%M", "%S", "%p"],   # Thu January 24 2030 05 45 13 AM
    ],
}


def make_new_format(format_parts, date_string_parts):
    format_parts = iter(format_parts)
    date_string_parts = iter(date_string_parts)
    date_format = ""
    for string_part in date_string_parts:
        if PARTS_RE.fullmatch(string_part):
            date_format += next(format_parts)
        else:
            date_format += string_part
    return date_format


def can_parse(date_format, text):
    try:
        datetime.strptime(text, date_format)
    except ValueError:
        return False
    else:
        return True


def detect_format(text):
    filterwarnings(
        "ignore",
        category=DeprecationWarning,
        message=r"[\s\S]*https://github.com/python/cpython/issues/70647[\s\S]*",
    )
    for date_format in specific_custom_formats:
        if can_parse(date_format, text):
            return date_format
    all_parts = [p for p in PARTS_RE.split(text) if p]
    significant_parts = len([p for p in all_parts if PARTS_RE.fullmatch(p)])
    for format_parts in generic_formats.get(significant_parts, []):
        date_format = make_new_format(format_parts, all_parts)
        if can_parse(date_format, text):
            return date_format
    raise ValueError("No valid format found.")


def prompt_for_date():
    print(f"{F_BOLD}Paste an example date/time string to see the guessed format.{NO_FORMAT}")
    return input(f"{F_BOLD}> {NO_FORMAT}")


def main():
    if "--help" in sys.argv:
        sys.exit(__doc__.strip())
    text = " ".join(sys.argv[1:])
    if not text:
        text = prompt_for_date()
    try:
        print(detect_format(text))
    except ValueError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
