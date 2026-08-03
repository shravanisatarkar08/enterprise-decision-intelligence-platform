from typing import Dict, List


class DatasetUnderstandingEngine:
    """
    Generates high-level business insights
    from dataset metadata.
    """

    def analyze(
        self,
        rows: int,
        columns: List[str],
    ) -> Dict:

        text = " ".join(columns).lower()

        # Dataset Type
        if "sales" in text or "revenue" in text:
            dataset_type = "Retail Sales Dataset"

        elif "employee" in text or "salary" in text:
            dataset_type = "HR Dataset"

        elif "customer" in text:
            dataset_type = "Customer Dataset"

        elif "medical" in text or "patient" in text:
            dataset_type = "Healthcare Dataset"

        elif "stock" in text or "price" in text:
            dataset_type = "Financial Dataset"

        else:
            dataset_type = "General Business Dataset"

        # Business Summary
        business_summary = (
            f"This dataset contains {rows} records "
            f"across {len(columns)} variables."
        )

        # Charts
        recommended_charts = [
            "Bar Chart",
            "Line Chart",
            "Pie Chart",
            "Correlation Heatmap"
        ]

        # ML Tasks
        possible_ml_tasks = [
            "Classification",
            "Regression",
            "Clustering"
        ]

        return {
            "dataset_type": dataset_type,
            "business_summary": business_summary,
            "recommended_charts": recommended_charts,
            "possible_ml_tasks": possible_ml_tasks,
        }