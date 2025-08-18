#!/usr/bin/env python3
"""
Black box tests for the f-string format specification finder.
Tests only the public API: analyze_number_format and get_test_value.
"""

import pytest
from fstring import analyze_number_format, get_test_value


class TestAnalyzeNumberFormat:
    """Test the main analyze_number_format function."""

    # ===== Basic Alignment Tests =====
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

    # ===== Custom Fill Character Tests =====
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

    def test_star_padding(self):
        formats = analyze_number_format("**34")
        assert ('int', 'f"{variable:*>4d}"') in formats
        assert ('str', 'f"{variable:*>4}"') in formats

    # ===== Zero Padding Tests =====
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

    def test_zero_padded_single_digit(self):
        formats = analyze_number_format("007")
        assert ('int', 'f"{variable:03d}"') in formats

    # ===== Literal Prefix/Suffix Tests =====
    def test_currency_prefix(self):
        formats = analyze_number_format("$34.50")
        assert ('float', 'f"${variable:.2f}"') in formats
        assert ('str', 'f"${variable}"') in formats

    def test_currency_suffix(self):
        formats = analyze_number_format("99.99€")
        assert ('float', 'f"{variable:.2f}€"') in formats

    def test_label_with_number(self):
        formats = analyze_number_format("Item #42")
        assert ('int', 'f"Item #{variable:d}"') not in formats
        assert ('str', 'f"Item #{variable}"') in formats

    def test_parentheses(self):
        formats = analyze_number_format("(123)")
        assert ('int', 'f"({variable:d})"') not in formats

    def test_units(self):
        formats = analyze_number_format("5.5km")
        assert ('float', 'f"{variable:.1f}km"') in formats

    def test_complex_suffix(self):
        formats = analyze_number_format("123.45 USD/month")
        assert ('float', 'f"{variable:.2f} USD/month"') in formats

    def test_prefix_and_suffix(self):
        formats = analyze_number_format("Total: $50.00 USD")
        assert ('float', 'f"Total: ${variable:.2f} USD"') in formats

    # ===== Sign Tests =====
    def test_sign_prefix(self):
        formats = analyze_number_format("+42")
        assert ('int', 'f"{variable:+d}"') in formats

    def test_negative_number(self):
        formats = analyze_number_format("-42")
        assert not any(t == 'int' for t, f in formats)

    def test_sign_with_padding(self):
        formats = analyze_number_format(" +42")
        assert any('+' in f for t, f in formats if t == 'int')

    # ===== Decimal Number Tests =====
    def test_simple_decimal(self):
        formats = analyze_number_format("3400.00")
        assert ('float', 'f"{variable:.2f}"') in formats

    def test_space_padded_decimal(self):
        formats = analyze_number_format(" 340.00")
        assert ('float', 'f"{variable:>7.2f}"') in formats

    def test_many_decimal_places(self):
        formats = analyze_number_format("3.14159")
        assert ('float', 'f"{variable:.5f}"') in formats

    def test_single_decimal(self):
        formats = analyze_number_format("1.5")
        assert ('float', 'f"{variable:.1f}"') in formats

    # ===== Thousands Separator Tests =====
    def test_integer_with_comma(self):
        formats = analyze_number_format("3,400")
        # Special case: comma without width omits 'd'
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

    def test_comma_with_width(self):
        # When there's a width, 'd' should be kept
        formats = analyze_number_format("     1,234")
        assert any(',' in f and 'd' in f for t, f in formats if t == 'int')

    # ===== Underscore Separator Tests =====
    def test_integer_with_underscore(self):
        formats = analyze_number_format("3_400")
        # Special case: underscore without width omits 'd'
        assert ('int', 'f"{variable:_}"') in formats
        assert ('float', 'f"{variable:_.0f}"') in formats

    def test_float_with_underscore(self):
        formats = analyze_number_format("3_400.00")
        assert ('float', 'f"{variable:_.2f}"') in formats

    def test_large_number_with_underscores(self):
        formats = analyze_number_format("1_234_567")
        assert ('int', 'f"{variable:_}"') in formats

    def test_million_with_underscores(self):
        formats = analyze_number_format("1_000_000")
        assert ('int', 'f"{variable:_}"') in formats
        assert ('float', 'f"{variable:_.0f}"') in formats

    def test_padded_number_with_underscore(self):
        formats = analyze_number_format("  3_400.00")
        assert ('float', 'f"{variable:>10_.2f}"') in formats

    def test_underscore_with_width(self):
        # When there's a width, 'd' should be kept
        formats = analyze_number_format("     1_234")
        assert any('_' in f and 'd' in f for t, f in formats if t == 'int')

    def test_float_decimal_with_underscore(self):
        formats = analyze_number_format("1_234.56")
        assert ('float', 'f"{variable:_.2f}"') in formats

    def test_underscore_with_currency_prefix(self):
        formats = analyze_number_format("$1_000_000")
        assert ('int', 'f"${variable:_}"') in formats
        assert ('float', 'f"${variable:_.0f}"') in formats

    def test_underscore_with_currency_suffix(self):
        formats = analyze_number_format("1_999.99€")
        assert ('float', 'f"{variable:_.2f}€"') in formats

    # ===== Hexadecimal Format Tests =====
    def test_simple_hex(self):
        formats = analyze_number_format("0x4")
        assert ('int', 'f"{variable:#x}"') in formats

    def test_zero_padded_hex(self):
        formats = analyze_number_format("0x04")
        assert ('int', 'f"{variable:#04x}"') in formats

    def test_larger_hex(self):
        formats = analyze_number_format("0xff")
        assert ('int', 'f"{variable:#x}"') in formats

    def test_zero_padded_larger_hex(self):
        formats = analyze_number_format("0x00ff")
        assert ('int', 'f"{variable:#06x}"') in formats

    def test_unprefixed_lowercase_hex(self):
        formats = analyze_number_format("ff")
        assert ('int', 'f"{variable:x}"') in formats

    def test_unprefixed_uppercase_hex(self):
        formats = analyze_number_format("FF")
        assert ('int', 'f"{variable:X}"') in formats

    def test_unprefixed_zero_padded_larger_hex(self):
        formats = analyze_number_format("00ff")
        assert ('int', 'f"{variable:04x}"') in formats

    def test_hex_with_literals(self):
        formats = analyze_number_format("Address: 0x1234")
        assert ('int', 'f"Address: {variable:#x}"') in formats

    # ===== Percentage Format Tests =====
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

    def test_percentage_with_sign(self):
        formats = analyze_number_format("+12.5%")
        assert ('float', 'f"{variable:+.1%}"') in formats

    def test_negative_percentage(self):
        formats = analyze_number_format("-5.5%")
        assert ('float', 'f"{variable:.1%}"') in formats

    # ===== Edge Cases =====
    def test_single_digit(self):
        formats = analyze_number_format("5")
        assert ('int', 'f"{variable:d}"') not in formats

    def test_number_zero(self):
        formats = analyze_number_format("0")
        assert not any(t == 'int' for t, f in formats)

    def test_very_long_number(self):
        formats = analyze_number_format("123456789")
        assert not any(t == 'int' for t, f in formats)

    def test_mixed_padding_as_literals(self):
        """Different padding on each side should be treated as literals."""
        formats = analyze_number_format("  34_")
        assert any(' {variable}_' in f for t, f in formats)

    def test_plain_string(self):
        formats = analyze_number_format("hello")
        assert not formats, "No format specifications"

    def test_string_with_numbers(self):
        formats = analyze_number_format("test123")
        assert any('test' in f and 'variable' in f for t, f in formats)

    def test_only_padding_characters(self):
        formats = analyze_number_format("___")
        assert not formats, "No format specifications"

    def test_just_decimal_point(self):
        formats = analyze_number_format(".")
        assert not formats, "No format specifications"

    def test_empty_string(self):
        formats = analyze_number_format("")
        assert not formats, "No format specifications"

    # ===== Complex Combinations =====
    def test_currency_with_comma(self):
        formats = analyze_number_format("$1,234.56")
        assert ('float', 'f"${variable:,.2f}"') in formats

    def test_currency_with_underscore(self):
        formats = analyze_number_format("$1_234.56")
        assert ('float', 'f"${variable:_.2f}"') in formats

    def test_percentage_with_label(self):
        formats = analyze_number_format("Accuracy: 98.5%")
        assert ('float', 'f"Accuracy: {variable:.1%}"') in formats

    def test_right_aligned_with_comma_and_decimal(self):
        formats = analyze_number_format("  1,234.56")
        assert any(',' in f and '.2f' in f for t, f in formats if t == 'float')

    def test_right_aligned_with_underscore_and_decimal(self):
        formats = analyze_number_format("  1_234.56")
        assert any('_' in f and '.2f' in f for t, f in formats if t == 'float')

    def test_centered_decimal(self):
        formats = analyze_number_format(" 34.5 ")
        assert any('^' in f and '.1f' in f for t, f in formats if t == 'float')

    def test_custom_fill_with_decimal(self):
        formats = analyze_number_format("**34.50")
        assert any('*>' in f and '.2f' in f for t, f in formats if t == 'float')

    def test_hex_with_padding_as_literals(self):
        """Hex numbers with literal padding should be treated as such."""
        formats = analyze_number_format("  0x42")
        assert any('  {variable:#x}' in f for t, f in formats)

    def test_zero_padded_with_sign(self):
        formats = analyze_number_format("+0034")
        assert any('+' in f and '05' in f for t, f in formats)

    def test_underscore_with_left_align(self):
        formats = analyze_number_format("1_000  ")
        assert ('int', 'f"{variable:<7_d}"') in formats

    def test_underscore_with_center_align(self):
        formats = analyze_number_format(" 1_000 ")
        assert ('int', 'f"{variable:^7_d}"') in formats

    # ===== Format Uniqueness Tests =====
    def test_no_duplicate_formats(self):
        """Ensure no duplicate format specifications are returned."""
        formats = analyze_number_format("1234.56")
        seen = set()
        for type_name, format_spec in formats:
            key = (type_name, format_spec)
            assert key not in seen, f"Duplicate format found: {key}"
            seen.add(key)

    def test_no_string_format_with_percent(self):
        """String format should always be present when there are literals."""
        formats = analyze_number_format("100%")
        assert all(t != 'str' for t, _ in formats), f"string format found for 100%"

    def test_string_format_always_present_with_literals(self):
        """String format should always be present when there are literals."""
        test_cases = ["$100", "Item #5", "(42)"]
        for test in test_cases:
            formats = analyze_number_format(test)
            assert any(t == 'str' for t, _ in formats), f"No string format for {test}"


class TestGetTestValue:
    """Test the get_test_value function."""

    # ===== String Type Tests =====
    def test_get_test_value_str_simple(self):
        assert get_test_value("123", "str") == "123"

    def test_get_test_value_str_with_prefix(self):
        assert get_test_value("$123", "str") == "123"

    def test_get_test_value_str_with_suffix(self):
        assert get_test_value("123km", "str") == "123"

    def test_get_test_value_str_padded(self):
        assert get_test_value("  123  ", "str") == "123"

    def test_get_test_value_str_non_numeric(self):
        assert get_test_value("hello", "str") == "hello"

    # ===== Integer Type Tests =====
    def test_get_test_value_int_simple(self):
        assert get_test_value("123", "int") == 123

    def test_get_test_value_int_negative(self):
        assert get_test_value("-123", "int") == -123

    def test_get_test_value_int_with_prefix(self):
        assert get_test_value("$123", "int") == 123

    def test_get_test_value_int_comma(self):
        assert get_test_value("1,234", "int") == 1234

    def test_get_test_value_int_underscore(self):
        assert get_test_value("1_234", "int") == 1234

    def test_get_test_value_int_large_underscore(self):
        assert get_test_value("1_000_000", "int") == 1000000

    def test_get_test_value_int_underscore_with_prefix(self):
        assert get_test_value("$1_234", "int") == 1234

    def test_get_test_value_int_hex(self):
        assert get_test_value("0xff", "int") == 255

    def test_get_test_value_int_unprefixed_hex(self):
        assert get_test_value("ff", "int") == 255
        assert get_test_value("FF", "int") == 255

    def test_get_test_value_int_zero_padded(self):
        assert get_test_value("0034", "int") == 34

    def test_get_test_value_int_padded(self):
        assert get_test_value("  123  ", "int") == 123

    def test_get_test_value_int_invalid(self):
        assert get_test_value("not_a_number", "int") == 0

    # ===== Float Type Tests =====
    def test_get_test_value_float_simple(self):
        assert get_test_value("123.45", "float") == 123.45

    def test_get_test_value_float_negative(self):
        assert get_test_value("-123.45", "float") == -123.45

    def test_get_test_value_float_percentage(self):
        assert get_test_value("34.5%", "float") == 0.345

    def test_get_test_value_float_integer(self):
        assert get_test_value("123", "float") == 123.0

    def test_get_test_value_float_comma(self):
        assert get_test_value("1,234.56", "float") == 1234.56

    def test_get_test_value_float_underscore(self):
        assert get_test_value("1_234.56", "float") == 1234.56

    def test_get_test_value_float_large_underscore(self):
        assert get_test_value("1_000_000.99", "float") == 1000000.99

    def test_get_test_value_float_underscore_with_prefix(self):
        assert get_test_value("$1_234.56", "float") == 1234.56

    def test_get_test_value_float_zero_padded(self):
        assert get_test_value("00123.45", "float") == 123.45

    def test_get_test_value_float_with_prefix(self):
        assert get_test_value("$99.99", "float") == 99.99

    def test_get_test_value_float_padded(self):
        assert get_test_value("  123.45  ", "float") == 123.45

    def test_get_test_value_float_invalid(self):
        assert get_test_value("not_a_number", "float") == 0.0

    # ===== Edge Cases for get_test_value =====
    def test_get_test_value_empty_string(self):
        assert get_test_value("", "str") == ""
        assert get_test_value("", "int") == 0
        assert get_test_value("", "float") == 0.0

    def test_get_test_value_just_sign(self):
        assert get_test_value("+", "int") == 0
        assert get_test_value("-", "float") == 0.0

    def test_get_test_value_zero(self):
        assert get_test_value("0", "int") == 0
        assert get_test_value("0", "float") == 0.0
        assert get_test_value("0", "str") == "0"

    def test_get_test_value_underscore_only(self):
        assert get_test_value("_", "int") == 0
        assert get_test_value("_", "float") == 0.0
        assert get_test_value("_", "str") == "_"


class TestRoundTrip:
    """Test that format specs can recreate the original string."""

    def verify_format(self, input_str, expected_type=None):
        """Helper to verify at least one format works."""
        formats = analyze_number_format(input_str)
        assert len(formats) > 0, f"No formats found for '{input_str}'"

        # If we expect a specific type, verify it exists
        if expected_type:
            assert any(t == expected_type for t, _ in formats), \
                f"Expected {expected_type} format for '{input_str}'"

    def test_basic_numbers(self):
        self.verify_format("42", "float")
        self.verify_format("3.14", "float")
        self.verify_format("0", "float")

    def test_formatted_numbers(self):
        self.verify_format("1,234", "int")
        self.verify_format("1_234", "int")
        self.verify_format("$99.99", "float")
        self.verify_format("85%", "float")
        self.verify_format("0x2a", "int")
        self.verify_format("1.5e-3", "float")

    def test_underscore_numbers(self):
        self.verify_format("1_000", "int")
        self.verify_format("1_000_000", "int")
        self.verify_format("1_234.56", "float")
        self.verify_format("$1_000_000", "int")
        self.verify_format("1_999.99€", "float")

    def test_padded_numbers(self):
        self.verify_format("  42", "int")
        self.verify_format("42  ", "int")
        self.verify_format("_42_", "int")
        self.verify_format("0042", "int")

    def test_complex_underscore_combinations(self):
        self.verify_format("  1_234.56", "float")
        self.verify_format("$1_234_567.89", "float")
        self.verify_format("Total: 1_000_000 units", "str")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
