"""Bootstrap validation tests for EPREP.AI."""

import sys
import eprep
from eprep import __app_name__, __version__
from eprep.domain.language import SupportedLanguage
from eprep.main import main


def test_package_metadata():
    """Verify package name and version are properly exposed."""
    assert __version__ == "0.1.0"
    assert __app_name__ == "EPREP.AI"


def test_python_runtime_version():
    """Verify the execution environment is running on Python 3.12."""
    assert sys.version_info.major == 3
    assert sys.version_info.minor == 12


def test_approved_languages_count():
    """Verify exactly six approved programming languages are defined for V1."""
    languages = SupportedLanguage.get_all()
    assert len(languages) == 6


def test_approved_languages_set():
    """Verify the exact set of approved programming languages."""
    expected = {"Python", "Java", "C", "C++", "JavaScript", "TypeScript"}
    actual = set(SupportedLanguage.get_names())
    assert actual == expected


def test_main_entry_point(monkeypatch):
    """Verify main entry point runs cleanly without error."""
    monkeypatch.setattr("eprep.main.run_app", lambda: 0)
    exit_code = main()
    assert exit_code == 0
