import warnings

warnings.filterwarnings(
    action="ignore", category=DeprecationWarning, module=".*pkg_resources"
)
