"""Test DWD Rain Radar TAR extractor."""

from io import BytesIO
import tarfile
from unittest.mock import MagicMock, patch

from custom_components.dwd_rainradar.extractor import Extractor


def _build_tar() -> bytes:
    """Build a TAR archive containing files and a directory."""

    buffer = BytesIO()

    with tarfile.open(
        fileobj=buffer,
        mode="w",
    ) as archive:

        directory = tarfile.TarInfo(
            "nested",
        )

        directory.type = tarfile.DIRTYPE

        archive.addfile(
            directory,
        )

        for filename, content in (
            (
                "first.h5",
                b"first",
            ),
            (
                "nested/second.h5",
                b"second",
            ),
        ):

            member = tarfile.TarInfo(
                filename,
            )

            member.size = len(
                content
            )

            archive.addfile(
                member,
                BytesIO(
                    content
                ),
            )

    return buffer.getvalue()


def test_extract_returns_only_regular_files() -> None:
    """Test regular TAR members are returned and directories ignored."""

    extracted = Extractor().extract(
        _build_tar(),
    )

    assert extracted == {
        "first.h5": b"first",
        "nested/second.h5": b"second",
    }


def test_extract_ignores_member_without_file_object() -> None:
    """Test an unreadable regular member is ignored safely."""

    member = MagicMock()

    member.isfile.return_value = True

    with patch(
        "custom_components.dwd_rainradar.extractor.tarfile.open"
    ) as mock_open:

        archive = (
            mock_open.return_value
            .__enter__.return_value
        )

        archive.getmembers.return_value = [
            member,
        ]

        archive.extractfile.return_value = None

        assert Extractor().extract(
            b"test",
        ) == {}
