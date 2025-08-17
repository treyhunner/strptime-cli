#!/usr/bin/env python3
"""
f-string format specification finder - reverse engineer format specs from output examples
"""

import re
import sys
from typing import List, Tuple, Optional, Dict


def split_numeric_literals(s: str) -> Tuple[str, str, str]:
    """
    Split a string into prefix literals, numeric part, and suffix literals.

    The numeric part is what could be produced by a Python format specification:
    - Digits (0-9)
    - Decimal point (.)
    - Comma thousands separator (,)
    - Minus sign (-) at the start
    - Plus sign (+) at the start
    - Percentage sign (%) at the end
    - Hex notation (0x/0X prefix with hex digits)
    - Scientific notation (e/E with exponent)

    Everything else is treated as literal text.
    """
    # Special case: hex format
    hex_match = re.match(r'^(.*?)(0[xX][0-9a-fA-F]+)(.*)$', s)
    if hex_match:
        prefix, num, suffix = hex_match.groups()
        # Check if prefix looks like padding (all same char)
        if prefix and all(c == prefix[0] for c in prefix):
            return '', s, ''
        return prefix, num, suffix

    # Special case: percentage (number with % at end)
    percent_match = re.match(r'^(.*?)([+-]?\d+\.?\d*%)(.*)$', s)
    if percent_match:
        prefix, num, suffix = percent_match.groups()
        # Check if prefix looks like padding
        if prefix and all(c == prefix[0] for c in prefix):
            return '', s, ''
        return prefix, num, suffix

    # Scientific notation
    sci_match = re.match(r'^(.*?)([+-]?\d+\.?\d*[eE][+-]?\d+)(.*)$', s)
    if sci_match:
        prefix, num, suffix = sci_match.groups()
        if prefix and all(c == prefix[0] for c in prefix):
            return '', s, ''
        return prefix, num, suffix

    # Regular number (possibly with commas, decimal point)
    # This regex finds the longest numeric sequence that could be from format()
    patterns = [
        # With thousands separator
        r'^(.*?)([+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?)(.*)$',
        # Decimal number
        r'^(.*?)([+-]?\d+\.\d+)(.*)$',
        # Integer (possibly with leading zeros)
        r'^(.*?)([+-]?\d+)(.*)$',
    ]

    for pattern in patterns:
        match = re.match(pattern, s)
        if match:
            prefix, num, suffix = match.groups()

            # Check if what we found as prefix/suffix is actually padding
            # Padding is: repeated same character AND (spaces or common fill chars)
            is_padding_char = lambda text, char: (
                text and
                all(c == char for c in text) and
                char in ' _*#=.-'
            )

            # If both prefix and suffix exist and are the same character, it's likely padding
            if prefix and suffix and prefix[0] == suffix[0] and is_padding_char(prefix, prefix[0]):
                return '', s, ''

            # If just prefix exists and looks like padding
            if prefix and is_padding_char(prefix, prefix[0]) and not suffix:
                return '', s, ''

            # If just suffix exists and looks like padding
            if suffix and is_padding_char(suffix, suffix[0]) and not prefix:
                return '', s, ''

            # Otherwise treat as literals
            return prefix, num, suffix

    # No numeric part found
    return '', s, ''


def detect_padding(s: str, pad_chars: str = ' _*#=.-') -> Tuple[str, str, str, str]:
    """
    Detect consistent padding in a string.
    Only considers padding if it's a repeated character.
    """
    # First check if we have literals (not padding)
    prefix, num, suffix = split_numeric_literals(s)
    if prefix or suffix:
        # We have actual literals, not padding
        return s, '', '', ' '

    # Now check for padding patterns
    for char in pad_chars:
        left = len(s) - len(s.lstrip(char))
        right = len(s) - len(s.rstrip(char))

        if left or right:
            core = s[left:len(s)-right] if right else s[left:]
            if core:  # Must have non-padding content
                return core, s[:left], s[len(s)-right:] if right else '', char

    return s, '', '', ' '


def parse_number(s: str) -> Optional[Dict]:
    """Parse a string as a number and return its properties."""
    # Hex format
    if re.match(r'^0[xX][0-9a-fA-F]+$', s):
        return {
            'type': 'hex',
            'value': int(s[2:], 16),
            'padded': len(s) > 3 and s[2] == '0',
            'width': len(s)
        }

    # Percentage
    if s.endswith('%'):
        num = s[:-1].strip()
        if re.match(r'^[+-]?\d+\.?\d*$', num):
            return {
                'type': 'percent',
                'value': float(num) / 100,
                'decimals': len(num.split('.')[1]) if '.' in num else 0,
                'has_sign': num.startswith('+') or num.startswith('-')
            }

    # Scientific notation
    if re.match(r'^[+-]?\d+\.?\d*[eE][+-]?\d+$', s):
        return {
            'type': 'scientific',
            'value': float(s),
            'has_sign': s.startswith('+') or s.startswith('-')
        }

    # Zero-padded number (only if no sign and starts with 0)
    # But not if it has commas
    if re.match(r'^0+\d', s) and not s.startswith('0.') and ',' not in s:
        return {
            'type': 'zero_pad',
            'value': float(s) if '.' in s else int(s),
            'width': len(s),
            'decimals': len(s.split('.')[1]) if '.' in s else 0
        }

    # Regular number
    clean = s.replace(',', '')
    if re.match(r'^[+-]?\d+\.?\d*$', clean):
        return {
            'type': 'number',
            'value': float(clean) if '.' in clean else int(clean),
            'has_comma': ',' in s,
            'decimals': len(clean.split('.')[1]) if '.' in clean else 0,
            'is_float': '.' in clean,
            'has_sign': s.startswith('+'),
            'is_negative': s.startswith('-')
        }

    return None


def build_format_spec(align: str = '', fill: str = '', width: int = 0,
                      comma: bool = False, decimals: Optional[int] = None,
                      type_char: str = '', sign: str = '',
                      prefix: str = '', suffix: str = '') -> str:
    """Build a format specification string."""
    parts = []

    # Fill and alignment
    if fill and fill != ' ':
        parts.append(fill)
    if align:
        parts.append(align)

    # Sign
    if sign:
        parts.append(sign)

    # Width
    if width:
        parts.append(str(width))

    # Comma separator
    if comma:
        parts.append(',')

    # Precision
    if decimals is not None:
        parts.append(f'.{decimals}')

    # Type - only add 'd' if we don't have comma or other modifiers
    if type_char:
        # Don't add 'd' if we have comma without width
        if not (type_char == 'd' and comma and not width):
            parts.append(type_char)

    spec = ''.join(parts)

    # Build the final f-string with literals
    if spec:
        return f'f"{prefix}{{variable:{spec}}}{suffix}"'
    else:
        return f'f"{prefix}{{variable}}{suffix}"'


def analyze_number_format(s: str) -> List[Tuple[str, str]]:
    """Analyze a string and return possible format specifications."""
    if not s:
        return [('str', 'f"{variable}"')]

    results = []

    # First, split into literals and numeric part
    prefix, number_part, suffix = split_numeric_literals(s)

    # If we have literals, work with just the number part
    if prefix or suffix:
        # Special case: if there's no actual number part, it's just a literal string
        num_info = parse_number(number_part) if number_part else None

        if not num_info and not number_part:
            # No number at all, just return as literal
            results.append(('str', f'f"{s}"'))
            return results

        if num_info:
            if num_info['type'] == 'hex':
                # Hex with literals
                if num_info['padded']:
                    spec = f'f"{prefix}{{variable:#0{num_info["width"]}x}}{suffix}"'
                else:
                    spec = f'f"{prefix}{{variable:#x}}{suffix}"'
                results.append(('int', spec))
                return results

            elif num_info['type'] == 'percent':
                # Percentage with literals
                sign = '+' if num_info.get('has_sign') else ''
                spec = build_format_spec(
                    sign=sign,
                    decimals=num_info['decimals'],
                    type_char='%',
                    prefix=prefix,
                    suffix=suffix
                )
                results.append(('float', spec))
                return results

            elif num_info['type'] == 'scientific':
                # Scientific notation with literals
                sign = '+' if num_info.get('has_sign') else ''
                spec = f'f"{prefix}{{variable:{sign}e}}{suffix}"'
                results.append(('float', spec))
                return results

            elif num_info['type'] == 'zero_pad':
                # Zero-padded with literals
                width = num_info['width']
                decimals = num_info['decimals']

                if decimals:
                    spec = f'f"{prefix}{{variable:0{width}.{decimals}f}}{suffix}"'
                    results.append(('float', spec))
                else:
                    spec = f'f"{prefix}{{variable:0{width}d}}{suffix}"'
                    results.append(('int', spec))
                    spec = f'f"{prefix}{{variable:0{width}.0f}}{suffix}"'
                    results.append(('float', spec))
                return results

            elif num_info['type'] == 'number':
                # Regular number with literals
                is_float = num_info['is_float']
                has_comma = num_info['has_comma']
                decimals = num_info['decimals']
                sign = '+' if num_info.get('has_sign') else ''

                if not is_float:
                    # Integer format
                    spec_int = build_format_spec(
                        sign=sign,
                        comma=has_comma,
                        type_char='d' if not has_comma else '',
                        prefix=prefix,
                        suffix=suffix
                    )
                    results.append(('int', spec_int))

                    # Float version
                    spec_float = build_format_spec(
                        sign=sign,
                        comma=has_comma,
                        decimals=0,
                        type_char='f',
                        prefix=prefix,
                        suffix=suffix
                    )
                    results.append(('float', spec_float))
                else:
                    # Float format
                    spec_float = build_format_spec(
                        sign=sign,
                        comma=has_comma,
                        decimals=decimals,
                        type_char='f',
                        prefix=prefix,
                        suffix=suffix
                    )
                    results.append(('float', spec_float))

                # String version
                results.append(('str', f'f"{prefix}{{variable}}{suffix}"'))
                return results

        # If we couldn't parse the number part, treat whole thing as string
        results.append(('str', f'f"{s}"'))
        return results

    # No literals found, check for padding
    core, left_pad, right_pad, fill_char = detect_padding(s)

    # Parse the core value
    num_info = parse_number(core)

    # Special case: no number found at all
    if not num_info:
        # It's just a plain string
        results.append(('str', f'f"{s}"'))
        return results

    # Special number formats without padding
    if not left_pad and not right_pad:
        # Hex format
        if num_info and num_info['type'] == 'hex':
            if num_info['padded']:
                results.append(('int', f'f"{{variable:#0{num_info["width"]}x}}"'))
            else:
                results.append(('int', 'f"{variable:#x}"'))
            return results

        # Percentage
        if num_info and num_info['type'] == 'percent':
            sign = '+' if num_info.get('has_sign') else ''
            results.append(('float', f'f"{{variable:{sign}.{num_info["decimals"]}%}}"'))
            return results

        # Scientific notation
        if num_info and num_info['type'] == 'scientific':
            sign = '+' if num_info.get('has_sign') else ''
            results.append(('float', f'f"{{variable:{sign}e}}"'))
            return results

        # Zero-padded
        if num_info and num_info['type'] == 'zero_pad':
            width = num_info['width']
            decimals = num_info['decimals']

            if decimals:
                results.append(('float', f'f"{{variable:0{width}.{decimals}f}}"'))
            else:
                results.append(('int', f'f"{{variable:0{width}d}}"'))
                results.append(('float', f'f"{{variable:0{width}.0f}}"'))
            return results

    # Determine alignment
    align = ''
    if left_pad and right_pad:
        align = '^'
    elif left_pad:
        align = '>'
    elif right_pad:
        align = '<'

    width = len(s) if (left_pad or right_pad) else 0

    # Generate format specs based on the content type
    if num_info and num_info['type'] == 'number':
        is_float = num_info['is_float']
        has_comma = num_info['has_comma']
        decimals = num_info['decimals']
        sign = '+' if num_info.get('has_sign') else ''

        if not is_float:
            # Integer format
            spec_int = build_format_spec(align, fill_char, width, has_comma, None, 'd', sign)
            results.append(('int', spec_int))

            # Float format
            spec_float = build_format_spec(align, fill_char, width, has_comma, 0, 'f', sign)
            results.append(('float', spec_float))
        else:
            # Float format
            spec_float = build_format_spec(align, fill_char, width, has_comma, decimals, 'f', sign)
            results.append(('float', spec_float))

    # String format
    if align or fill_char != ' ':
        spec_str = build_format_spec(align, fill_char, width)
        results.append(('str', spec_str))
    else:
        results.append(('str', 'f"{variable}"'))

    return results


def validate_format(format_spec: str, test_value, expected: str) -> bool:
    """Validate if a format specification produces the expected output."""
    try:
        # Extract the format string and parse prefix/suffix
        match = re.match(r'f"([^{]*)\{variable:?(.*?)\}([^}]*)"', format_spec)
        if match:
            prefix, fmt, suffix = match.groups()
            result = prefix + (format(test_value, fmt) if fmt else str(test_value)) + suffix
            return result == expected
    except (ValueError, TypeError):
        pass
    return False


def get_test_value(input_str: str, type_name: str):
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
        # For strings, use the numeric part or core
        if input_str.endswith('%'):
            input_str = input_str[:-1]
        input_str = input_str.replace(',', '').lstrip('+-')

        if re.match(r'^\d+\.?\d*$', input_str):
            return input_str.split('.')[0] if '.' in input_str else input_str
        return input_str

    elif type_name == 'int':
        # Parse as integer
        num_info = parse_number(input_str)
        if num_info:
            value = abs(int(num_info['value']))
            return value

        # Fallback
        clean = input_str.replace(',', '').split('.')[0].lstrip('+-')
        return int(clean) if clean and clean.isdigit() else 0

    else:  # float
        # Parse as float
        num_info = parse_number(input_str)
        if num_info:
            if num_info['type'] == 'percent':
                return num_info['value']
            else:
                return abs(float(num_info['value']))

        # Fallback
        clean = input_str.replace(',', '').lstrip('+-')
        return float(clean) if clean and re.match(r'^\d+\.?\d*$', clean) else 0.0


def main():
    """Main entry point for the CLI tool."""
    if len(sys.argv) > 1:
        input_str = sys.argv[1]
    else:
        print("Enter a formatted string (or 'quit' to exit):")
        input_str = input().strip()
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

            assert validate_format(format_spec, test_value, input_str)
            print(f"{type_name:5} → {format_spec}")
            print(f"        (e.g., variable = {repr(test_value)})")
            print()


if __name__ == "__main__":
    while True:
        main()
        if len(sys.argv) > 1:
            break
        print("\n" + "=" * 40)
