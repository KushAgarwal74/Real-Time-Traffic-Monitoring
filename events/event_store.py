import json
from pathlib import Path
from datetime import datetime
import numpy as np


class EventStore:

    def __init__(self, output_path):

        self.output_path = Path(output_path)

        self.output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.file = open(
            self.output_path,
            "w",
            encoding="utf-8"
        )


    def _json_serializer(self, obj):

        """
        Converts objects that JSON does not understand
        into JSON-compatible values.
        """

        # Python datetime
        if isinstance(obj, datetime):

            return obj.isoformat()

        # NumPy integer
        if isinstance(obj, np.integer):

            return int(obj)

        # NumPy float
        if isinstance(obj, np.floating):

            return float(obj)

        # NumPy boolean
        if isinstance(obj, np.bool_):

            return bool(obj)

        raise TypeError(
            f"Object of type {type(obj).__name__} "
            f"is not JSON serializable"
        )


    def write_event(self, event):

        json.dump(
            event,
            self.file,
            default=self._json_serializer
        )

        self.file.write("\n")

        # Important for safety while processing
        self.file.flush()


    def close(self):

        if self.file:

            self.file.close()

            self.file = None