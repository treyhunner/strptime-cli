"""
Usage:
$ python -m strptime "2030-01-24 05:45"
%Y-%m-%d %H:%M
"""
from datetime import datetime
import sys


__version__ = "0.1.0"

NO_FORMAT="\033[0m"
F_BOLD="\033[1m"
C_YELLOW="\033[38;5;227m"

formats = {
    "RFC 2822": "%a, %d %b %Y %H:%M:%S",
    "Timestamp": "%Y-%m-%d %H:%M:%S",
    "ISO 8601 Extended": "%Y-%m-%dT%H:%M:%S%z",
    "ISO 8601 Extended, no timezone": "%Y-%m-%dT%H:%M:%S",
    "American Date & Time": "%m/%d/%Y %I:%M:%S %p",
    "European Date & Time": "%d/%m/%Y %H:%M:%S",
    "RFC 2822": "%a, %d %b %Y %H:%M:%S",
    "Hyphenated Name with Time": "%d-%b-%Y %H:%M",
    "ISO 8601 Basic": "%Y%m%dT%H%M%SZ",
    "RFC 3339 with offset": "%Y-%m-%d %H:%M:%S%z",
    "RFC 2822, no seconds": "%a, %d %b %Y %H:%M",
    "Timestamp, no seconds": "%Y-%m-%d %H:%M",
    "American, secondless": "%m/%d/%Y %I:%M %p",
    "European, secondless": "%d/%m/%Y %H:%M",
    "Short Date": "%m/%d/%y",
    "Year First Date": "%Y-%m-%d",
    "Long Date": "%B %d, %Y",
    "Date with Month Name": "%d %b %Y",
    "PostgreSQL Timestamp": "%Y-%m-%d %H:%M:%S.%f",
    "Year and Day of Year": "%Y-%j",
}
more_formats = [
    "%c",
    "%b %d %Y %I:%M%p",
    "%d %b %Y %H:%M:%S",
    "%Y.%m.%d",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%H:%M:%S",
    "%Y-%m-%d_%H-%M",
    "%a %b %e %H:%M:%S %Z %Y",
    "%H:%M%z",
    "%H:%M%-z",
    "%b %Y",
    "%A",
    "%a",
    "%b",
    "%B",
    "%b %d, %Y",
    "%a, %d %b %Y",
    "%a %d %b %Y",
    "%H:%M:%S%z",
    "%I:%M:%S %p",
    "%I:%M %p",
    "%Y-%m-%d %H:%M%p",
    "%Y_%m_%d",
    "%d.%m.%Y",
    "%m-%d-%Y",
    "%d/%m/%Y",
]

def sample_code(text, date_format):
    print(f"{F_BOLD}Sample Code:{NO_FORMAT}")
    return f"""from datetime import datetime
example = "{text}"
parsed = datetime.strptime(example, "{date_format}")
formatted_again = f"{{parsed:{date_format}}}" """

def detect_format(text):
    all_formats = [*formats.values(), *more_formats]
    date_format = ""
    for date_format in all_formats:
        try:
            datetime.strptime(text, date_format)
        except ValueError:
            continue
        else:
            break

    return date_format

def launch_tui():
    print(f"{F_BOLD}Paste an example date/time string to see the guessed format or paste a format string to see a formatted example.{NO_FORMAT}")
    text = input(f"{F_BOLD}{C_YELLOW}> {NO_FORMAT}")

    date_format = detect_format(text)
    print(date_format)
    print(sample_code(text, date_format))

def main():
    text = " ".join(sys.argv[1:])
    if not text:
        launch_tui()
    date_format = detect_format(text)
    print(date_format)

if __name__ == "__main__":
    main()
