#!/usr/bin/env python3
"""
f-string format specification finder - reverse engineer format specs from output examples
Now includes datetime format detection!
"""
from dataclasses import dataclass, field
import re
import sys
from typing import Optional
from datetime import datetime
from warnings import filterwarnings


HEX_RE = re.compile(r'0[xX][0-9a-fA-F]+')
UNPREFIXED_HEX_RE = re.compile(r'[0-9]*[a-fA-F]+[0-9]*')
PERCENT_RE = re.compile(r'[+-]?\d+\.?\d*%')
ZERO_PADDED_RE = re.compile(r'0+\d+\.?\d*')
THOUSANDS_RE = re.compile(r'[+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?')
UNDERSCORE_RE = re.compile(r'[+-]?\d{1,3}(?:_\d{3})+(?:\.\d+)?')
NUMBER_RE = re.compile(r'[+-]?\d+\.?\d*')

FULL_HEX_RE = re.compile(rf'(.*?)({HEX_RE.pattern})(.*)')
FULL_UNPREFIXED_HEX_RE = re.compile(rf'()({UNPREFIXED_HEX_RE.pattern})()')
FULL_PERCENT_RE = re.compile(rf'(.*?)({PERCENT_RE.pattern})(.*)')
FULL_THOUSANDS_RE = re.compile(rf'(.*?)({THOUSANDS_RE.pattern})(.*)')
FULL_UNDERSCORE_RE = re.compile(rf'(.*?)({UNDERSCORE_RE.pattern})(.*)')
FULL_NUMBER_RE = re.compile(rf'(.*?)({NUMBER_RE.pattern})(.*)')
PAD_CHARS = ' _*'

# Datetime detection components (from strptime.py)
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
        ["%d", "%B", "%Y", "%H", "%M"],                     # 24 January 2030 05 45
        ["%B", "%d", "%Y", "%H", "%M"],                     # January 24 2030 05 45
        ["%Y", "%m", "%d", "%H", "%M"],                     # 2030 01 24 05 45
        ["%Y", "%m", "%d", "%I", "%M%p"],                   # 2030 01 24 24 05 45AM
        ["%d", "%m", "%Y", "%H", "%M"],                     # 24 01 2030 05 45
        ["%b", "%d", "%Y", "%I", "%M%p"],                   # Jan 24 2030 05 45AM
        ["%d", "%b", "%Y", "%I", "%M%p"],                   # 24 Jan 2030 05 45AM
        ["%B", "%d", "%Y", "%I", "%M%p"],                   # January 24 2030 05 45AM
        ["%d", "%B", "%Y", "%I", "%M%p"],                   # 24 January 2030 05 45AM
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


@dataclass
class NumberParts:
    prefix: str
    num: str
    suffix: str

    def __iter__(self):
        return iter((self.prefix, self.num, self.suffix))


@dataclass
class FormatSpec:
    """Represents the components needed to build a format specification."""
    align: str = ''
    fill: str = ''
    width: int = 0
    comma: bool = False
    underscore: bool = False
    decimals: Optional[int] = None
    type_char: str = ''
    sign: str = ''
    prefix: str = ''
    suffix: str = ''

    # Metadata for generating variations
    value_type: str = 'str'  # 'int', 'float', 'str', or 'datetime'
    test_value: float = 0
    datetime_format: str = ''  # For datetime types, stores the strptime format

    def build(self):
        """Build the format specification string."""
        if self.value_type == 'datetime':
            if self.datetime_format:
                return f'f"{self.prefix}{{variable:{self.datetime_format}}}{self.suffix}"'
            else:
                return f'f"{self.prefix}{{variable}}{self.suffix}"'
        else:
            return build_format_spec(
                align=self.align,
                fill=self.fill,
                width=self.width,
                comma=self.comma,
                underscore=self.underscore,
                decimals=self.decimals,
                type_char=self.type_char,
                sign=self.sign,
                prefix=self.prefix,
                suffix=self.suffix
            )

    def as_tuple(self):
        """Return (value_type, format_spec) tuple for compatibility."""
        return (self.value_type, self.build())


def build_format_spec(
        align='',
        fill='',
        width=0,
        comma=False,
        underscore=False,
        decimals=None,
        type_char='',
        sign='',
        prefix='',
        suffix='',
):
    """Build a format specification string."""
    fill = fill if fill != ' ' else ''
    width_str = str(width) if width else ''
    comma_str = ',' if comma else ''
    underscore_str = '_' if underscore else ''
    decimals_str = f'.{decimals}' if decimals is not None else ''

    # Choose separator (underscore takes precedence over comma if both somehow set)
    separator_str = underscore_str or comma_str

    # Special case: integer with separator but no width should omit 'd'
    if type_char == 'd' and (comma or underscore) and not width:
        type_char = ''

    if align:
        spec = f'{fill}{align}{sign}{width_str}{separator_str}{decimals_str}{type_char}'
    else:
        spec = f'{sign}{fill}{width_str}{separator_str}{decimals_str}{type_char}'

    if spec:
        return f'f"{prefix}{{variable:{spec}}}{suffix}"'
    else:
        return f'f"{prefix}{{variable}}{suffix}"'


def is_padding(text):
    """Check if text represents padding characters."""
    return len(set(text)) == 1 and text[0] in PAD_CHARS


def count_decimals(number_string):
    """Return number of decimals in given numeric string."""
    return len(number_string.split('.')[1]) if '.' in number_string else 0


def split_numeric_literals(s):
    """Split a string into prefix literals, numeric part, and suffix literals."""
    # Check for hex with 0x prefix first
    if match := FULL_HEX_RE.fullmatch(s):
        return NumberParts(*match.groups())

    # Check for percentage
    if match := FULL_PERCENT_RE.fullmatch(s):
        return NumberParts(*match.groups())

    # Check for unprefixed hex (must contain a-f or A-F)
    if match := FULL_UNPREFIXED_HEX_RE.fullmatch(s):
        prefix, num, suffix = match.groups()
        # Check if prefix/suffix look like padding
        left_pad = is_padding(prefix)
        right_pad = is_padding(suffix)
        # If padding on both sides or neither side, treat whole thing as hex
        if not ((left_pad and not right_pad) or (right_pad and not left_pad)):
            return NumberParts(prefix, num, suffix)

    # Check for numbers with separators (thousands or underscore) and regular numbers
    for regex in [FULL_THOUSANDS_RE, FULL_UNDERSCORE_RE, FULL_NUMBER_RE]:
        if match := regex.fullmatch(s):
            prefix, num, suffix = match.groups()
            left_pad = is_padding(prefix)
            right_pad = is_padding(suffix)
            if (
                    (left_pad or right_pad)
                    and (left_pad != right_pad or prefix[0] == suffix[0])
            ):
                return NumberParts('', s, '')

            return NumberParts(prefix, num, suffix)

    return NumberParts('', s, '')


def detect_padding(s, pad_chars=PAD_CHARS):
    """Detect consistent padding in a string."""
    for char in pad_chars:
        left = len(s) - len(s.lstrip(char))
        right = len(s.rstrip(char))
        left_pad, core, right_pad = s[:left], s[left:right], s[right:]
        if (left_pad or right_pad) and core:
            return core, left_pad, right_pad, char

    return s, '', '', ' '


# Datetime detection functions (from strptime.py)
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


def detect_datetime_format(text):
    """Detect datetime format from text string."""
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

    return None


def is_single_numeric_datetime_format(datetime_format):
    """Check if datetime format is just a single numeric component like %d or %Y."""
    single_numeric_formats = {"%d", "%m", "%y", "%Y", "%H", "%I", "%M", "%S", "%j"}
    return datetime_format in single_numeric_formats


def has_datetime_structure(s):
    """Check if string has structure that suggests datetime (spaces, dashes, colons, etc)."""
    # Look for separators that commonly appear in datetime strings
    datetime_separators = {' ', '-', '/', ':', 'T', '+'}
    return any(sep in s for sep in datetime_separators)


def parse_number_to_spec(s, prefix='', suffix='', align='', fill='', width=0):
    """Parse a string as a number and return FormatSpec objects."""

    # Hex format with 0x prefix
    if HEX_RE.fullmatch(s):
        value = int(s.removeprefix('0x'), 16)
        is_padded = s.startswith('0x0')
        return [FormatSpec(
            fill="0" if is_padded else "",
            width=len(s) if is_padded else 0,
            type_char='x',
            sign='#',
            prefix=prefix,
            suffix=suffix,
            value_type='int',
            test_value=value
        )]

    # Unprefixed hex format (contains a-f or A-F)
    if UNPREFIXED_HEX_RE.fullmatch(s):
        value = int(s, 16)

        # Choose format based on what's present (uppercase takes precedence if both)
        hex_char = 'X' if s.isupper() else 'x'

        # Check for zero padding
        is_padded = len(s) > 1 and s[0] == '0'

        return [FormatSpec(
            fill="0" if is_padded else "",
            width=len(s) if is_padded else 0,
            type_char=hex_char,
            prefix=prefix,
            suffix=suffix,
            value_type='int',
            test_value=value
        )]

    # Percentage
    if PERCENT_RE.fullmatch(s):
        num = s.removesuffix('%')
        value = float(num) / 100
        decimals = count_decimals(num)
        has_sign = num.startswith('+')  # Only + triggers sign format, not -
        return [FormatSpec(
            sign='+' if has_sign else '',
            decimals=decimals,
            type_char='%',
            prefix=prefix,
            suffix=suffix,
            value_type='float',
            test_value=value
        )]

    if ZERO_PADDED_RE.fullmatch(s.removeprefix('+')):
        # Zero-padded number (possibly with sign)
        width_val = len(s)  # Include the sign in the width
        decimals = count_decimals(s)
        has_sign = s.startswith('+')
        value = float(s) if decimals else int(s)

        results = []
        if not decimals:
            spec = FormatSpec(
                fill="0",
                width=width_val,
                type_char='d',
                sign='+' if has_sign else '',
                prefix=prefix,
                suffix=suffix,
                value_type='int',
                test_value=abs(value)
            )
            results.append(spec)

        spec = FormatSpec(
            fill="0",
            width=width_val,
            decimals=decimals,
            type_char='f',
            sign='+' if has_sign else '',
            prefix=prefix,
            suffix=suffix,
            value_type='float',
            test_value=abs(float(value))
        )
        results.append(spec)
        return results

    # Regular number (check for separators)
    clean = s.replace(',', '').replace('_', '')
    if NUMBER_RE.fullmatch(clean):
        has_comma = THOUSANDS_RE.fullmatch(s)
        has_underscore = UNDERSCORE_RE.fullmatch(s)
        decimals = count_decimals(clean)
        has_sign = s.startswith('+')
        sign = '+' if has_sign else ''
        value = float(clean) if decimals else int(clean)

        results = []
        if not decimals and (align or has_comma or has_underscore or sign or fill.strip()):
            # Integer format
            spec = FormatSpec(
                align=align,
                fill=fill,
                width=width,
                comma=has_comma,
                underscore=has_underscore,
                type_char='d',
                sign=sign,
                prefix=prefix,
                suffix=suffix,
                value_type='int',
                test_value=abs(int(value))
            )
            results.append(spec)

        # Float format
        spec = FormatSpec(
            align=align,
            fill=fill,
            width=width,
            comma=has_comma,
            underscore=has_underscore,
            decimals=decimals,
            type_char='f',
            sign=sign,
            prefix=prefix,
            suffix=suffix,
            value_type='float',
            test_value=abs(float(value))
        )
        if not decimals and (has_comma or has_underscore):
            results.insert(0, spec)
        else:
            results.append(spec)
        return results

    return []


def split_datetime_literals(s):
    """Try to find datetime parts within a string with literals."""
    # Try to find potential datetime substrings
    # Look for patterns that commonly appear in datetimes
    datetime_patterns = [
        # ISO-like dates
        re.compile(r'(.*?)(\d{4}-\d{2}-\d{2}(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?(?:\s*[AP]M)?)(.*)', re.IGNORECASE),
        # US dates
        re.compile(r'(.*?)(\d{1,2}/\d{1,2}/\d{2,4}(?:\s+\d{1,2}:\d{2}(?::\d{2})?\s*[AP]M?)?)(.*)', re.IGNORECASE),
        # Times
        re.compile(r'(.*?)(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)(.*)', re.IGNORECASE),
        # Month names with dates/years
        re.compile(r'(.*?)(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:,?\s+\d{4})?(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?(?:\s*[AP]M)?)(.*)', re.IGNORECASE),
        # Weekday names with dates
        re.compile(r'(.*?)(\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:\s+\d{4})?(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?(?:\s*[AP]M)?)(.*)', re.IGNORECASE),
        # Just month or weekday names
        re.compile(r'(.*?)(\b(?:January|February|March|April|May|June|July|August|September|October|November|December|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b)(.*)', re.IGNORECASE),
    ]

    for pattern in datetime_patterns:
        match = pattern.fullmatch(s)
        if match:
            prefix, datetime_part, suffix = match.groups()
            # Try to detect datetime format on the extracted part
            datetime_format = detect_datetime_format(datetime_part.strip())
            if datetime_format:
                return prefix, datetime_part.strip(), suffix, datetime_format

    return None, s, None, None


def analyze_number_format(s):
    """Analyze a string and return possible format specifications."""
    results = []

    # Try datetime detection on full string first
    datetime_format = detect_datetime_format(s)
    datetime_prefix = ''
    datetime_suffix = ''
    datetime_part = s

    # If full string detection failed, try to find datetime parts within literals
    if not datetime_format:
        prefix, datetime_part, suffix, datetime_format = split_datetime_literals(s)
        if datetime_format:
            datetime_prefix = prefix or ''
            datetime_suffix = suffix or ''

    if datetime_format:
        # Determine test value for datetime
        try:
            test_dt = datetime.strptime(datetime_part, datetime_format)
        except ValueError:
            test_dt = datetime(2030, 1, 24, 5, 45, 13)  # Default test datetime

        spec = FormatSpec(
            value_type='datetime',
            datetime_format=datetime_format,
            prefix=datetime_prefix,
            suffix=datetime_suffix,
            test_value=0,  # Not used for datetime
        )

        # Check if this is a single numeric component
        is_single_numeric = is_single_numeric_datetime_format(datetime_format)

        if is_single_numeric:
            # Single numeric datetime formats get lower priority
            datetime_results = [spec.as_tuple()]
        else:
            # Multi-part datetime formats get higher priority
            datetime_results = [spec.as_tuple()]
    else:
        datetime_results = []
        is_single_numeric = False

    # Continue with existing numeric format detection
    # First, split into literals and numeric part
    prefix, number_part, suffix = split_numeric_literals(s)

    # Handle cases with literals
    if prefix or suffix:
        numeric_results = parse_number_to_spec(number_part, prefix, suffix)

        # Always add string version
        spec = FormatSpec(
            prefix=prefix,
            suffix=suffix,
            value_type='str',
            test_value=0
        )
        numeric_results.append(spec)
        numeric_results = [spec.as_tuple() for spec in numeric_results]
    else:
        # No literals found, check for padding
        core, left_pad, right_pad, fill_char = detect_padding(s)

        # Determine alignment and width
        if left_pad and right_pad:
            if len(left_pad) == len(right_pad):
                align = '^'  # True center alignment - equal padding on both sides
            else:
                # Unequal padding - treat as literals, not alignment
                spec = FormatSpec(
                    prefix=left_pad,
                    suffix=right_pad,
                    value_type='str'
                )
                return [spec.as_tuple()]
        elif left_pad:
            align = '>'
        elif right_pad:
            align = '<'
        else:
            align = ''

        width = len(s) if (left_pad or right_pad) else 0

        # Parse the core number
        if left_pad or right_pad:
            numeric_results = parse_number_to_spec(core, align=align, fill=fill_char, width=width)

            # Add string format if there's alignment or non-space fill
            if align or fill_char != ' ':
                spec = FormatSpec(
                    align=align,
                    fill=fill_char,
                    width=width,
                    value_type='str'
                )
                numeric_results.append(spec)
        else:
            numeric_results = parse_number_to_spec(core, align=align, fill=fill_char, width=width)

        numeric_results = [spec.as_tuple() for spec in numeric_results]

    # Now combine results with proper priority ordering
    # Priority rules:
    # 1. Multi-part datetime formats (highest priority when datetime structure detected)
    # 2. Numeric formats (int/float)
    # 3. String formats
    # 4. Single numeric datetime formats (lowest priority)

    if datetime_results and not is_single_numeric:
        # Multi-part datetime: prioritize datetime if string has datetime structure
        if has_datetime_structure(s):
            results.extend(datetime_results)
            results.extend(numeric_results)
        else:
            # No clear datetime structure, prioritize numeric
            results.extend(numeric_results)
            results.extend(datetime_results)
    elif datetime_results and is_single_numeric:
        # Single numeric datetime: lowest priority
        results.extend(numeric_results)
        results.extend(datetime_results)
    else:
        # No datetime formats found, just use numeric results
        results.extend(numeric_results)

    return results


def get_test_value(input_str, type_name):
    """Determine appropriate test value for validation."""
    if type_name == 'datetime':
        # Try to parse the original datetime
        datetime_format = detect_datetime_format(input_str)
        if datetime_format:
            try:
                return datetime.strptime(input_str, datetime_format)
            except ValueError:
                pass

        # If full string parsing failed, try to extract datetime part from literals
        prefix, datetime_part, suffix, datetime_format = split_datetime_literals(input_str)
        if datetime_format:
            try:
                return datetime.strptime(datetime_part, datetime_format)
            except ValueError:
                pass

        # Return default datetime if parsing fails
        return datetime(2030, 1, 24, 5, 45, 13)

    # Extract just the numeric part for non-datetime types
    prefix, number_part, suffix = split_numeric_literals(input_str)
    if prefix or suffix:
        input_str = number_part

    # If still no numeric part, check for padding
    core, _, _, _ = detect_padding(input_str)
    if core != input_str:
        input_str = core

    if type_name == 'str':
        return input_str

    elif type_name == 'int':
        # Parse as integer
        clean = input_str.replace(',', '').replace('_', '').removeprefix('+')
        if clean and clean.removeprefix('-').isdigit():
            return int(clean)
        # Try for hex with 0x prefix
        if HEX_RE.fullmatch(input_str):
            return int(input_str.removeprefix('0x'), 16)
        # Try for unprefixed hex
        if UNPREFIXED_HEX_RE.fullmatch(input_str):
            return int(input_str, 16)
        return 0

    else:  # float
        # Parse as float
        clean = input_str.replace(',', '').replace('_', '').removeprefix('+')
        if PERCENT_RE.fullmatch(input_str):
            clean = clean.removesuffix('%')
            if clean and NUMBER_RE.fullmatch(clean):
                return float(clean) / 100

        if clean and NUMBER_RE.fullmatch(clean):
            return float(clean)
        return 0.0


def main():
    """Main entry point for the CLI tool."""
    if len(sys.argv) > 1:
        input_str = sys.argv[1]
    else:
        print("Enter a formatted string (or 'quit' to exit):")
        input_str = input()
        if input_str.lower() == 'quit':
            return

    print(f"\nInput: '{input_str}'")
    print("-" * 40)

    results = analyze_number_format(input_str)

    if not results:
        print("No format specifications found")
        return

    # Display unique results
    seen = set()
    for type_name, format_spec in results:
        if (type_name, format_spec) not in seen:
            seen.add((type_name, format_spec))

            # Get test value and validate
            test_value = get_test_value(input_str, type_name)

            print(f"{type_name:8} → {format_spec}")
            print(f"           (e.g., variable = {repr(test_value)})")
            print()


if __name__ == "__main__":
    while True:
        main()
        if len(sys.argv) > 1:
            break
        print("\n" + "=" * 40)
