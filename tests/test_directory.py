"""Test DWD Rain Radar directory parsing."""

from custom_components.dwd_rainradar.directory import DirectoryParser


def test_directory_parser_extracts_only_file_links() -> None:
    """Test file links are returned while directories and other tags are ignored."""

    html = """
    <html>
      <body>
        <span>ignored</span>
        <a>missing href</a>
        <a href="../">parent</a>
        <a href="subdirectory/">directory</a>
        <a href="first.hdf5">first</a>
        <a href="second.tar">second</a>
      </body>
    </html>
    """

    assert DirectoryParser.parse(
        html,
    ) == [
        "first.hdf5",
        "second.tar",
    ]


def test_directory_parser_filenames_property() -> None:
    """Test filenames can be read from a parser instance."""

    parser = DirectoryParser()

    parser.feed(
        '<a href="product.hdf5">product</a>'
    )

    assert parser.filenames == [
        "product.hdf5",
    ]
