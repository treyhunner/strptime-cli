#!/usr/bin/env python3
"""
f-string format specification finder - reverse engineer format specs from output examples
"""
from dataclasses import dataclass, field
import re
import sys
from typing import Optional


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
    value_type: str = 'str'  # 'int', 'float', or 'str'
    test_value: float = 0

    def build(self):
        """Build the format specification string."""
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


def analyze_number_format(s):
    """Analyze a string and return possible format specifications."""

    # First, split into literals and numeric part
    prefix, number_part, suffix = split_numeric_literals(s)

    # Handle cases with literals
    if prefix or suffix:
        results = parse_number_to_spec(number_part, prefix, suffix)

        # Always add string version
        spec = FormatSpec(
            prefix=prefix,
            suffix=suffix,
            value_type='str',
            test_value=0
        )
        results.append(spec)
        return [spec.as_tuple() for spec in results]

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
    results = parse_number_to_spec(core, align=align, fill=fill_char, width=width)

    # Add string format if there's alignment or non-space fill
    if align or fill_char != ' ':
        spec = FormatSpec(
            align=align,
            fill=fill_char,
            width=width,
            value_type='str'
        )
        results.append(spec)

    return [spec.as_tuple() for spec in results]


def get_test_value(input_str, type_name):
    """Determine appropriate test value for validation."""
    # Extract just the numeric part
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

            print(f"{type_name:5} → {format_spec}")
            print(f"        (e.g., variable = {repr(test_value)})")
            print()


if __name__ == "__main__":
    while True:
        main()
        if len(sys.argv) > 1:
            break
        print("\n" + "=" * 40)
