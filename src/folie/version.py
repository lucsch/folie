"""Version commune, enrichie par tools/createversion.py lors des builds."""

try:
    from ._build_version import BRANCH_NAME, COMMIT_ID, COMMIT_NUMBER, VERSION_MAJOR_MINOR
except ImportError:
    VERSION_MAJOR_MINOR = "1.0"
    COMMIT_NUMBER = "0"
    COMMIT_ID = "unknown"
    BRANCH_NAME = "unknown"
