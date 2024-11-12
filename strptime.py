"""
Usage:
$ python -m strptime "2030-01-24 05:45"
%Y-%m-%d %H:%M
"""
from datetime import datetime
import re
import sys


__version__ = "0.2.0"

NO_FORMAT="\033[0m"
F_BOLD="\033[1m"

PARTS_RE = re.compile(r"""
    (
        # %S%z matching
        [0-9+]*
        [+] \d{2} :? \d{2}
    |
        [A-Za-z0-9]+
    )
""", flags=re.VERBOSE)

specific_custom_formats = [
    "%m/%d/%Y %I:%M %p",
    "%m/%d/%Y",
    "%m/%d/%y",
    "%m-%d-%Y",
]

generic_formats = {
    1: [
        ['%Y%m%dT%H%M%SZ'],
        ['%c'],
        ['%A'],
        ['%a'],
        ['%b'],
        ['%B'],
        ['%d'],
        ['%Y'],
    ],
    2: [
        ['%Y', '%j'],
        ['%H', '%M%z'],
        ['%H', '%M%-z'],
        ['%H', '%M%'],
        ['%b', '%d'],
        ['%d', '%b'],
        ['%b', '%Y'],
        ['%a', '%b'],
        ['%a', '%B'],
        ['%A', '%b'],
        ['%A', '%B'],
        ['%H', '%M'],
        ['%I', '%M%p'],
    ],
    3: [
        ['%Y', '%m', '%d'],
        ['%B', '%d', '%Y'],
        ['%d', '%b', '%Y'],
        ['%b', '%d', '%Y'],
        ['%d', '%m', '%Y'],
        ['%H', '%M', '%S'],
        ['%a', '%b', '%d'],
        ['%A', '%b', '%d'],
        ['%A', '%B', '%d'],
        ['%a', '%B', '%d'],
        ['%H', '%M', '%Z'],
        ['%H', '%M', '%S%z'],
        ['%I', '%M', '%p'],
    ],
    4: [
        ['%a', '%b', '%d', '%Y'],
        ['%A', '%b', '%d', '%Y'],
        ['%A', '%B', '%d', '%Y'],
        ['%H', '%M', '%S', '%Z'],
        ['%a', '%d', '%b', '%Y'],
        ['%I', '%M', '%S', '%p'],
    ],
    5: [
        ['%Y', '%m', '%dT%H', '%M', '%S%z'],
        ['%Y', '%m', '%dT%H', '%M', '%S'],
        ['%d', '%b', '%Y', '%H', '%M'],
        ['%b', '%d', '%Y', '%H', '%M'],
        ['%Y', '%m', '%d', '%H', '%M'],
        ['%d', '%m', '%Y', '%H', '%M'],
        ['%b', '%d', '%Y', '%I', '%M%p'],
        ['%Y', '%m', '%d', '%H', '%M%p'],
    ],
    6: [
        ['%b', '%d', '%Y', '%H', '%M', '%S'],
        ['%Y', '%m', '%d', '%H', '%M', '%S'],
        ['%d', '%m', '%Y', '%H', '%M', '%S'],
        ['%Y', '%m', '%d', '%H', '%M', '%S%z'],
        ['%Y', '%m', '%d', '%H', '%M', '%SZ'],
        ['%a', '%d', '%b', '%Y', '%H', '%M'],
        ['%m', '%d', '%Y', '%I', '%M', '%p'],
        ['%d', '%b', '%Y', '%H', '%M', '%S'],
        ['%Y', '%m', '%dT%H', '%M', '%S', '%fZ'],
        ['%Y', '%m', '%dT%H', '%M', '%S', '%f'],
        ['%b', '%d', '%Y', '%I', '%M', '%p']
    ],
    7: [
        ['%a', '%d', '%b', '%Y', '%H', '%M', '%S'],
        ['%a', '%b', '%d', '%Y', '%H', '%M', '%S'],
        ['%m', '%d', '%Y', '%I', '%M', '%S', '%p'],
        ['%b', '%d', '%Y', '%H', '%M', '%S', '%Z'],
        ['%d', '%b', '%Y', '%H', '%M', '%S', '%Z'],
        ['%Y', '%m', '%d', '%H', '%M', '%S', '%f'],
    ],
    8: [
        ['%a', '%d', '%b', '%Y', '%H', '%M', '%S', '%Z'],
        ['%a', '%b', '%d', '%Y', '%H', '%M', '%S', '%Z'],
        ['%a', '%b', '%e', '%H', '%M', '%S', '%Z', '%Y'],
    ]
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


def detect_format(text):
    for date_format in specific_custom_formats:
        try:
            datetime.strptime(text, date_format)
        except ValueError:
            continue
        else:
            break
    else:
        all_parts = [p for p in PARTS_RE.split(text) if p]
        significant_parts = len([p for p in all_parts if PARTS_RE.fullmatch(p)])
        for format_parts in generic_formats.get(significant_parts, []):
            date_format = make_new_format(format_parts, all_parts)
            try:
                datetime.strptime(text, date_format)
            except ValueError:
                continue
            else:
                break
        else:
            raise ValueError("No valid format found.")
    return date_format


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
