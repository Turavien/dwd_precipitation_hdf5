"""Extractor for DWD TAR archives."""

from __future__ import annotations

import tarfile

from io import BytesIO


class Extractor:
    """Extract files from DWD TAR archives."""

    def extract(
        self,
        data: bytes,
    ) -> dict[str, bytes]:
        """Extract all files from a TAR archive."""

        extracted: dict[str, bytes] = {}

        with tarfile.open(
            fileobj=BytesIO(data),
        ) as archive:

            for member in archive.getmembers():

                if not member.isfile():
                    continue

                file = archive.extractfile(member)

                if file is None:
                    continue

                extracted[member.name] = file.read()

        return extracted
