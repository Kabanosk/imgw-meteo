"""Typed exceptions for imgw_meteo."""


class IMGWError(Exception):
    """Base class for all imgw_meteo errors."""


class DownloadError(IMGWError):
    """A remote resource could not be downloaded."""


class ParseError(IMGWError):
    """A downloaded resource could not be parsed."""


class SchemaError(IMGWError):
    """A dataset does not match its expected / canonical schema."""


class SelectionError(IMGWError):
    """An invalid data selection was requested."""
