"""HTTP download layer with a simple on-disk cache."""

from pathlib import Path
from typing import Self
from urllib.parse import urlparse

import httpx
from loguru import logger

from .exceptions import DownloadError

DEFAULT_CACHE_DIR = Path.home() / ".cache" / "imgw-meteo"


class Downloader:
    """Fetches URLs with a filesystem cache keyed by URL path.

    :param cache_dir: Directory for cached downloads. Created on demand.
    :param offline: If ``True``, never hit the network; raise if a resource is
        not cached.
    :param refresh: One of ``"never"``, ``"if-stale"``, ``"always"``.
        ``"if-stale"`` re-downloads when the remote size differs from the
        cached file.
    :param timeout: Per-request timeout in seconds.
    """

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        *,
        offline: bool = False,
        refresh: str = "if-stale",
        timeout: float = 30.0,
    ) -> None:
        self.cache_dir = Path(cache_dir).expanduser() if cache_dir else DEFAULT_CACHE_DIR
        self.offline = offline
        self.refresh = refresh
        self.timeout = timeout
        self._client: httpx.Client | None = None

    def _http(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout, follow_redirects=True)
        return self._client

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _cache_path(self, url: str) -> Path:
        path = urlparse(url).path.lstrip("/")
        return self.cache_dir / path

    def fetch_text(self, url: str) -> str:
        """Fetch a text resource (not cached to disk; used for index pages).

        :param url: Absolute URL to fetch.
        :returns: The response body as text.
        :rtype: str
        :raises imgw_meteo.exceptions.DownloadError: In offline mode, or if the
            request fails.
        """
        if self.offline:
            raise DownloadError(f"offline mode: cannot fetch {url}")
        try:
            resp = self._http().get(url)
            resp.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - network
            raise DownloadError(f"failed to fetch {url}: {exc}") from exc
        return resp.text

    def fetch_file(self, url: str) -> Path:
        """Fetch a binary resource into the cache and return the local path.

        Honors the ``refresh`` policy and ``offline`` mode: a cached copy is
        reused when allowed, otherwise the file is downloaded.

        :param url: Absolute URL of the file to download.
        :returns: Local filesystem path of the cached file.
        :rtype: pathlib.Path
        :raises imgw_meteo.exceptions.DownloadError: In offline mode with no
            cached copy, or if the download fails.
        """
        dest = self._cache_path(url)
        if dest.exists() and self.refresh == "never":
            return dest
        if dest.exists() and self.refresh == "if-stale" and not self._is_stale(url, dest):
            return dest
        if self.offline:
            if dest.exists():
                return dest
            raise DownloadError(f"offline mode: {url} not in cache")

        dest.parent.mkdir(parents=True, exist_ok=True)
        logger.info("downloading {}", url)
        try:
            resp = self._http().get(url)
            resp.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - network
            raise DownloadError(f"failed to download {url}: {exc}") from exc
        tmp = dest.with_suffix(dest.suffix + ".part")
        tmp.write_bytes(resp.content)
        tmp.replace(dest)
        return dest

    def _is_stale(self, url: str, dest: Path) -> bool:
        """Check staleness via a HEAD request comparing Content-Length."""
        if self.offline:
            return False
        try:
            resp = self._http().head(url)
            resp.raise_for_status()
        except httpx.HTTPError:  # pragma: no cover - network
            return False  # can't tell; keep cached copy
        remote_len = resp.headers.get("content-length")
        if remote_len is None:
            return False
        return int(remote_len) != dest.stat().st_size
