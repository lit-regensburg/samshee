from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("samshee")
except PackageNotFoundError:
    # Package is not installed
    __version__ = "unknown"

import samshee.sectionedsheet as sectionedsheet
import samshee.samplesheetv2 as samplesheetv2
import samshee.validation as validation
