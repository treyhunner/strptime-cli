import pytest
from datetime import datetime
import sys
from strptime import main, formats, more_formats

@pytest.fixture
def mock_argv(monkeypatch):
    def _mock_argv(args):
        monkeypatch.setattr(sys, "argv", ["strptime.py"] + args)
    return _mock_argv

def test_main_with_valid_format(mock_argv, capsys):
    mock_argv(["2030-01-24 05:45"])
    main()
    captured = capsys.readouterr()
    assert captured.out.strip() == "%Y-%m-%d %H:%M"

def test_main_with_no_args(mock_argv):
    mock_argv([])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert "Usage:" in str(excinfo.value)

def test_main_with_invalid_format(mock_argv):
    mock_argv(["invalid-date-format"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert "No valid format found." in str(excinfo.value)

@pytest.mark.parametrize("date_string, expected_format", [
    ("2030-01-24 05:45:30", "%Y-%m-%d %H:%M:%S"),
    ("Thu, 24 Jan 2030 05:45:30", "%a, %d %b %Y %H:%M:%S"),
    ("2030-01-24T05:45:30+0000", "%Y-%m-%dT%H:%M:%S%z"),
    ("01/24/2030 05:45:30 AM", "%m/%d/%Y %I:%M:%S %p"),
    ("24/01/2030 05:45:30", "%d/%m/%Y %H:%M:%S"),
    ("24-Jan-2030 05:45", "%d-%b-%Y %H:%M"),
    ("20300124T054530Z", "%Y%m%dT%H%M%SZ"),
    ("2030-01-24 05:45:30+01:00", "%Y-%m-%d %H:%M:%S%z"),
    ("2030-01-24 05:45:30Z", "%Y-%m-%d %H:%M:%S%z"),
    ("Thu, 24 Jan 2030 05:45", "%a, %d %b %Y %H:%M"),
    ("2030-01-24 05:45", "%Y-%m-%d %H:%M"),
    ("01/24/2030 05:45 AM", "%m/%d/%Y %I:%M %p"),
    ("24/01/2030 05:45", "%d/%m/%Y %H:%M"),
    ("01/24/30", "%m/%d/%y"),
    ("2030-01-24", "%Y-%m-%d"),
    ("January 24, 2030", "%B %d, %Y"),
    ("24 Jan 2030", "%d %b %Y"),
    ("2030-01-24 05:45:30.123456", "%Y-%m-%d %H:%M:%S.%f"),
    ("2030-024", "%Y-%j"),
])
def test_various_date_formats(mock_argv, capsys, date_string, expected_format):
    mock_argv([date_string])
    main()
    captured = capsys.readouterr()
    assert captured.out.strip() == expected_format, date_string

def test_formats_dict():
    assert isinstance(formats, dict)
    assert all(isinstance(k, str) and isinstance(v, str) for k, v in formats.items())

def test_more_formats_list():
    assert isinstance(more_formats, list)
    assert all(isinstance(f, str) for f in more_formats)

def test_all_formats_are_valid():
    for format_string in list(formats.values()) + more_formats:
        try:
            datetime.now().strftime(format_string)
        except ValueError:
            pytest.fail(f"Invalid format string: {format_string}")

if __name__ == "__main__":
    pytest.main()
