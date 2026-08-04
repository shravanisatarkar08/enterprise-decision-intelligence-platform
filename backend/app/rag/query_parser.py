class QueryParser:

    def parse(self, question: str, columns: list):

        question = question.lower()

        # Detect operation
        if "highest" in question or "maximum" in question or "max" in question:
            operation = "max"

        elif "lowest" in question or "minimum" in question or "min" in question:
            operation = "min"

        elif "average" in question or "mean" in question:
            operation = "mean"

        elif "count" in question or "how many" in question:
            operation = "count"

        else:
            operation = "unknown"

        # Detect column
        detected_column = None

        for column in columns:
            if column.lower() in question:
                detected_column = column
                break

        return {
            "operation": operation,
            "column": detected_column
        }