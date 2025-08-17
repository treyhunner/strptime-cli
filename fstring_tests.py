#!/usr/bin/env python3
"""
Comprehensive tests for the f-string format specification finder
"""

import pytest
from fstring import (
    split_numeric_literals,
    detect_padding,
    parse_number,
    analyze_number_format,
    validate_format
)


class TestSplitNumericLiterals:
    """Test the numeric/literal splitting function."""

    def test_currency_prefix(self):
        prefix, num, suffix = split_numeric_literals("$34.50")
        assert prefix == "$"
        assert num == "34.50"
        assert suffix == ""

    def test_currency_suffix(self):
        prefix, num, suffix = split_numeric_literals("34.50€")
        assert prefix == ""
        assert num == "34.50"
        assert suffix == "€"

    def test_label_prefix(self):
        prefix, num, suffix = split_numeric_literals("Item #123")
        assert prefix == "Item #"
        assert num == "123"
        assert suffix == ""

    def test_parentheses(self):
        prefix, num, suffix = split_numeric_literals("(42)")
        assert prefix == "("
        assert num == "42"
        assert suffix == ")"

    def test_percentage(self):
        prefix, num, suffix = split_numeric_literals("34.5%")
        assert prefix == ""
        assert num == "34.5%"
        assert suffix == ""

    def test_hex_number(self):
        prefix, num, suffix = split_numeric_literals("0x4a")
        assert prefix == ""
        assert num == "0x4a"
        assert suffix == ""

    def test_no_number(self):
        prefix, num, suffix = split_numeric_literals("hello")
        assert prefix == ""
        assert num == "hello"
        assert suffix == ""

    def test_number_with_units(self):
        prefix, num, suffix = split_numeric_literals("123.45km/s")
        assert prefix == ""
        assert num == "123.45"
        assert suffix == "km/s"


class TestDetectPadding:
    """Test padding detection function."""

    def test_space_padding_left(self):
        core, left, right, fill = detect_padding("  34")
        assert core == "34"
        assert left == "  "
        assert right == ""
        assert fill == " "

    def test_underscore_padding_right(self):
        core, left, right, fill = detect_padding("34__")
        assert core == "34"
        assert left == ""
        assert right == "__"
        assert fill == "_"

    def test_center_padding(self):
        core, left, right, fill = detect_padding("_34_")
        assert core == "34"
        assert left == "_"
        assert right == "_"
        assert fill == "_"

    def test_no_padding(self):
        core, left, right, fill = detect_padding("34")
        assert core == "34"
        assert left == ""
        assert right == ""
        assert fill == " "

    def test_literal_not_padding(self):
        # Should not detect "$" as padding
        core, left, right, fill = detect_padding("$34")
        assert core == "$34"
        assert left == ""
        assert right == ""


class TestParseNumber:
    """Test number parsing function."""

    def test_simple_integer(self):
        info = parse_number("123")
        assert info['type'] == 'number'
        assert info['value'] == 123
        assert not info['is_float']

    def test_float(self):
        info = parse_number("123.45")
        assert info['type'] == 'number'
        assert info['value'] == 123.45
        assert info['is_float']
        assert info['decimals'] == 2

    def test_comma_separator(self):
        info = parse_number("1,234")
        assert info['type'] == 'number'
        assert info['value'] == 1234
        assert info['has_comma']

    def test_percentage(self):
        info = parse_number("34.5%")
        assert info['type'] == 'percent'
        assert info['value'] == 0.345
        assert info['decimals'] == 1

    def test_hex(self):
        info = parse_number("0xff")
        assert info['type'] == 'hex'
        assert info['value'] == 255

    def test_zero_padded(self):
        info = parse_number("0034")
        assert info['type'] == 'zero_pad'
        assert info['value'] == 34
        assert info['width'] == 4


class TestBasicAlignment:
    """Test basic alignment detection."""

    def test_right_align_space(self):
        formats = analyze_number_format("  34")
        assert ('int', 'f"{variable:>4d}"') in formats
        assert ('str', 'f"{variable:>4}"') in formats

    def test_left_align_space(self):
        formats = analyze_number_format("34  ")
        assert ('int', 'f"{variable:<4d}"') in formats
        assert ('str', 'f"{variable:<4}"') in formats

    def test_center_align_space(self):
        formats = analyze_number_format(" 34 ")
        assert ('int', 'f"{variable:^4d}"') in formats
        assert ('str', 'f"{variable:^4}"') in formats


class TestCustomFillCharacter:
    """Test custom fill character detection."""

    def test_right_align_underscore(self):
        formats = analyze_number_format("__34")
        assert ('int', 'f"{variable:_>4d}"') in formats
        assert ('str', 'f"{variable:_>4}"') in formats

    def test_left_align_underscore(self):
        formats = analyze_number_format("34__")
        assert ('int', 'f"{variable:_<4d}"') in formats
        assert ('str', 'f"{variable:_<4}"') in formats

    def test_center_align_underscore(self):
        formats = analyze_number_format("_34_")
        assert ('int', 'f"{variable:_^4d}"') in formats
        assert ('str', 'f"{variable:_^4}"') in formats


class TestZeroPadding:
    """Test zero-padding detection."""

    def test_zero_padded_integer(self):
        formats = analyze_number_format("0034")
        assert ('int', 'f"{variable:04d}"') in formats
        assert ('float', 'f"{variable:04.0f}"') in formats

    def test_zero_padded_float(self):
        formats = analyze_number_format("0340.00")
        assert ('float', 'f"{variable:07.2f}"') in formats

    def test_zero_padded_larger(self):
        formats = analyze_number_format("00000123")
        assert ('int', 'f"{variable:08d}"') in formats


class TestLiterals:
    """Test literal prefix/suffix handling."""

    def test_currency_prefix(self):
        formats = analyze_number_format("$34.50")
        assert ('float', 'f"${variable:.2f}"') in formats
        assert ('str', 'f"${variable}"') in formats

    def test_currency_suffix(self):
        formats = analyze_number_format("99.99€")
        assert ('float', 'f"{variable:.2f}€"') in formats

    def test_label_with_number(self):
        formats = analyze_number_format("Item #42")
        assert ('int', 'f"Item #{variable:d}"') in formats
        assert ('str', 'f"Item #{variable}"') in formats

    def test_parentheses(self):
        formats = analyze_number_format("(123)")
        assert ('int', 'f"({variable:d})"') in formats

    def test_units(self):
        formats = analyze_number_format("5.5km")
        assert ('float', 'f"{variable:.1f}km"') in formats

    def test_complex_suffix(self):
        formats = analyze_number_format("123.45 USD/month")
        assert ('float', 'f"{variable:.2f} USD/month"') in formats

    def test_sign_prefix(self):
        formats = analyze_number_format("+42")
        assert ('int', 'f"{variable:+d}"') in formats


class TestDecimalNumbers:
    """Test decimal number formatting."""

    def test_simple_decimal(self):
        formats = analyze_number_format("3400.00")
        assert ('float', 'f"{variable:.2f}"') in formats

    def test_space_padded_decimal(self):
        formats = analyze_number_format(" 340.00")
        assert ('float', 'f"{variable:>7.2f}"') in formats

    def test_many_decimal_places(self):
        formats = analyze_number_format("3.14159")
        assert ('float', 'f"{variable:.5f}"') in formats


class TestThousandsSeparator:
    """Test thousands separator detection."""

    def test_integer_with_comma(self):
        formats = analyze_number_format("3,400")
        assert ('int', 'f"{variable:,}"') in formats
        assert ('float', 'f"{variable:,.0f}"') in formats

    def test_float_with_comma(self):
        formats = analyze_number_format("3,400.00")
        assert ('float', 'f"{variable:,.2f}"') in formats

    def test_large_number_with_commas(self):
        formats = analyze_number_format("1,234,567")
        assert ('int', 'f"{variable:,}"') in formats

    def test_padded_number_with_comma(self):
        formats = analyze_number_format("  3,400.00")
        assert ('float', 'f"{variable:>10,.2f}"') in formats


class TestHexFormat:
    """Test hexadecimal format detection."""

    def test_simple_hex(self):
        formats = analyze_number_format("0x4")
        assert ('int', 'f"{variable:#x}"') in formats

    def test_zero_padded_hex(self):
        formats = analyze_number_format("0x04")
        assert ('int', 'f"{variable:#04x}"') in formats

    def test_larger_hex(self):
        formats = analyze_number_format("0xff")
        assert ('int', 'f"{variable:#x}"') in formats

    def test_uppercase_hex(self):
        formats = analyze_number_format("0XFF")
        assert ('int', 'f"{variable:#x}"') in formats or ('int', 'f"{variable:#X}"') in formats

    def test_zero_padded_larger_hex(self):
        formats = analyze_number_format("0x00ff")
        assert ('int', 'f"{variable:#06x}"') in formats


class TestPercentageFormat:
    """Test percentage format detection."""

    def test_integer_percentage(self):
        formats = analyze_number_format("34%")
        assert ('float', 'f"{variable:.0%}"') in formats

    def test_decimal_percentage(self):
        formats = analyze_number_format("34.0%")
        assert ('float', 'f"{variable:.1%}"') in formats

    def test_multi_decimal_percentage(self):
        formats = analyze_number_format("34.56%")
        assert ('float', 'f"{variable:.2%}"') in formats

    def test_percentage_with_prefix(self):
        formats = analyze_number_format("Score: 85%")
        assert ('float', 'f"Score: {variable:.0%}"') in formats


class TestScientificNotation:
    """Test scientific notation support."""

    def test_basic_scientific(self):
        formats = analyze_number_format("1.23e+5")
        assert ('float', 'f"{variable:e}"') in formats

    def test_negative_exponent(self):
        formats = analyze_number_format("4.56e-3")
        assert ('float', 'f"{variable:e}"') in formats

    def test_scientific_with_prefix(self):
        formats = analyze_number_format("Value: 1.5e10")
        assert ('float', 'f"Value: {variable:e}"') in formats


class TestFormatValidation:
    """Test that generated formats produce expected output."""

    def test_validate_right_align(self):
        assert validate_format('f"{variable:>4}"', "34", "  34")
        assert validate_format('f"{variable:>4d}"', 34, "  34")

    def test_validate_left_align(self):
        assert validate_format('f"{variable:<4}"', "34", "34  ")
        assert validate_format('f"{variable:<4d}"', 34, "34  ")

    def test_validate_center_align(self):
        assert validate_format('f"{variable:^4}"', "34", " 34 ")
        assert validate_format('f"{variable:^5}"', "34", " 34  ")

    def test_validate_zero_padding(self):
        assert validate_format('f"{variable:04d}"', 34, "0034")
        assert validate_format('f"{variable:04.0f}"', 34.0, "0034")

    def test_validate_decimal(self):
        assert validate_format('f"{variable:.2f}"', 3400.0, "3400.00")
        assert validate_format('f"{variable:7.2f}"', 340.0, " 340.00")

    def test_validate_comma(self):
        assert validate_format('f"{variable:,}"', 3400, "3,400")
        assert validate_format('f"{variable:,.2f}"', 3400.0, "3,400.00")

    def test_validate_hex(self):
        assert validate_format('f"{variable:#x}"', 4, "0x4")
        assert validate_format('f"{variable:#04x}"', 4, "0x04")

    def test_validate_percentage(self):
        assert validate_format('f"{variable:.0%}"', 0.34, "34%")
        assert validate_format('f"{variable:.1%}"', 0.34, "34.0%")

    def test_validate_literals(self):
        assert validate_format('f"${variable:.2f}"', 34.50, "$34.50")
        assert validate_format('f"{variable:.1f}km"', 5.5, "5.5km")
        assert validate_format('f"Item #{variable:d}"', 42, "Item #42")


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_string(self):
        formats = analyze_number_format("")
        assert len(formats) >= 1

    def test_single_digit(self):
        formats = analyze_number_format("5")
        assert ('int', 'f"{variable:d}"') in formats or ('int', 'f"{variable}"') in formats
        assert ('str', 'f"{variable}"') in formats

    def test_negative_number(self):
        formats = analyze_number_format("-42")
        assert any(t == 'int' for t, f in formats)

    def test_negative_padded(self):
        formats = analyze_number_format(" -42")
        assert any('4' in f or '5' in f for t, f in formats if t == 'int')

    def test_very_long_number(self):
        formats = analyze_number_format("123456789")
        assert any(t == 'int' for t, f in formats)

    def test_mixed_padding(self):
        formats = analyze_number_format("  34_")  # Different padding on each side
        # This should be treated as literals, not padding
        assert any(' {variable}_' in f for t, f in formats)

    def test_plain_string(self):
        formats = analyze_number_format("hello")
        # No numeric part, should return as literal
        assert ('str', 'f"hello"') in formats

    def test_string_with_numbers(self):
        formats = analyze_number_format("test123")
        # Should split into "test" + "123"
        assert any('test' in f and 'variable' in f for t, f in formats)


class TestComplexCombinations:
    """Test complex formatting combinations."""

    def test_currency_with_comma(self):
        formats = analyze_number_format("$1,234.56")
        assert ('float', 'f"${variable:,.2f}"') in formats

    def test_percentage_with_label(self):
        formats = analyze_number_format("Accuracy: 98.5%")
        assert ('float', 'f"Accuracy: {variable:.1%}"') in formats

    def test_zero_padded_with_comma(self):
        # This is tricky - zero padding with comma separator
        formats = analyze_number_format("03,400")
        # Should be treated as literals "03," + number "400"
        assert len(formats) > 0

    def test_right_aligned_with_comma_and_decimal(self):
        formats = analyze_number_format("  1,234.56")
        assert any(',' in f and '.2f' in f for t, f in formats if t == 'float')

    def test_centered_decimal(self):
        formats = analyze_number_format(" 34.5 ")
        assert any('^' in f and '.1f' in f for t, f in formats if t == 'float')

    def test_custom_fill_with_decimal(self):
        formats = analyze_number_format("**34.50")
        assert any('*>' in f and '.2f' in f for t, f in formats if t == 'float')


class TestAllOriginalExamples:
    """Test all the examples from the original specification."""

    def test_example_right_align(self):
        formats = analyze_number_format("  34")
        assert ('str', 'f"{variable:>4}"') in formats

    def test_example_left_align(self):
        formats = analyze_number_format("34  ")
        assert ('str', 'f"{variable:<4}"') in formats

    def test_example_center_align(self):
        formats = analyze_number_format(" 34 ")
        assert ('str', 'f"{variable:^4}"') in formats

    def test_example_right_underscore(self):
        formats = analyze_number_format("__34")
        assert ('str', 'f"{variable:_>4}"') in formats

    def test_example_left_underscore(self):
        formats = analyze_number_format("34__")
        assert ('str', 'f"{variable:_<4}"') in formats

    def test_example_center_underscore(self):
        formats = analyze_number_format("_34_")
        assert ('str', 'f"{variable:_^4}"') in formats

    def test_example_zero_pad_int(self):
        formats = analyze_number_format("0034")
        assert ('int', 'f"{variable:04d}"') in formats
        assert ('float', 'f"{variable:04.0f}"') in formats

    def test_example_zero_pad_float(self):
        formats = analyze_number_format("0340.00")
        assert ('float', 'f"{variable:07.2f}"') in formats

    def test_example_space_pad_float(self):
        formats = analyze_number_format(" 340.00")
        assert ('float', 'f"{variable:>7.2f}"') in formats

    def test_example_comma_int(self):
        formats = analyze_number_format("3,400")
        assert ('int', 'f"{variable:,}"') in formats
        assert ('float', 'f"{variable:,.0f}"') in formats

    def test_example_comma_float(self):
        formats = analyze_number_format("3,400.00")
        assert ('float', 'f"{variable:,.2f}"') in formats

    def test_example_plain_float(self):
        formats = analyze_number_format("3400.00")
        assert ('float', 'f"{variable:.2f}"') in formats

    def test_example_hex(self):
        formats = analyze_number_format("0x4")
        assert ('int', 'f"{variable:#x}"') in formats

    def test_example_hex_padded(self):
        formats = analyze_number_format("0x04")
        assert ('int', 'f"{variable:#04x}"') in formats

    def test_example_percent_int(self):
        formats = analyze_number_format("34%")
        assert ('float', 'f"{variable:.0%}"') in formats

    def test_example_percent_float(self):
        formats = analyze_number_format("34.0%")
        assert ('float', 'f"{variable:.1%}"') in formats

    def test_example_currency(self):
        formats = analyze_number_format("$34.50")
        assert ('float', 'f"${variable:.2f}"') in formats

    def test_example_currency_suffix(self):
        formats = analyze_number_format("34.50€")
        assert ('float', 'f"{variable:.2f}€"') in formats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
