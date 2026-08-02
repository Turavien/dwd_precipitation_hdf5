"""HTML directory parser for DWD directory listings."""

from __future__ import annotations

from html.parser import HTMLParser


class DirectoryParser(
    HTMLParser,
):
    """Extract filenames from a DWD directory listing."""

    def __init__(
        self,
    ) -> None:
        """Initialize the parser."""

        super().__init__()

        self._filenames: list[str] = []

    @property
    def filenames(
        self,
    ) -> list[str]:
        """Return all extracted filenames."""

        return self._filenames

    def handle_starttag(
        self,
        tag: str,
        attrs: list[
            tuple[
                str,
                str | None,
            ]
        ],
    ) -> None:
        """Process one HTML tag."""

        if tag != "a":
            return

        attributes = dict(
            attrs,
        )

        href = attributes.get(
            "href",
        )

        if href is None:
            return

        if href.endswith(
            "/",
        ):
            return

        self._filenames.append(
            href,
        )

    @classmethod
    def parse(
        cls,
        html: str,
    ) -> list[str]:
        """Parse one directory listing."""

        parser = cls()

        parser.feed(
            html,
        )

        return parser.filenames
