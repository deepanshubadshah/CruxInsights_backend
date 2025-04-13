import requests
import logging
from django.conf import settings
from .exceptions import InvalidURLError, ApiConnectionError, ApiResponseError

# Set up logging
logger = logging.getLogger(__name__)

class CruxService:
    """Service for interacting with the Chrome UX Report API"""
    
    API_ENDPOINT = "https://chromeuxreport.googleapis.com/v1/records:queryRecord"
    
    @staticmethod
    def validate_url(url):
        if not url or not isinstance(url, str):
            raise InvalidURLError("URL must be a non-empty string")
        if not (url.startswith('http://') or url.startswith('https://')):
            raise InvalidURLError("URL must start with http:// or https://")
        return True
    
    @classmethod
    def fetch_crux_data(cls, url):
        try:
            cls.validate_url(url)
            
            params = {
                'key': settings.GOOGLE_API_KEY
            }
            
            payload = {
                "url": url,
                "formFactor": "PHONE",
                "metrics": [
                    "largest_contentful_paint",
                    "cumulative_layout_shift",
                    "first_contentful_paint",
                    "interaction_to_next_paint",
                    "experimental_time_to_first_byte"
                ]
            }
            
            try:
                response = requests.post(
                    cls.API_ENDPOINT,
                    params=params,
                    json=payload,
                    timeout=10
                )
                
                if response.status_code != 200:
                    error_message = response.json().get('error', {}).get('message', 'Unknown error')
                    raise ApiResponseError(response.status_code, error_message)
                
                return cls.process_crux_data(response.json())
                
            except requests.exceptions.Timeout:
                logger.error(f"Timeout while fetching CrUX data for URL: {url}")
                raise ApiConnectionError("Request to CrUX API timed out")
            except requests.exceptions.ConnectionError:
                logger.error(f"Connection error while fetching CrUX data for URL: {url}")
                raise ApiConnectionError("Failed to connect to CrUX API")
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching CrUX data for URL {url}: {str(e)}")
                raise ApiConnectionError(f"Error connecting to CrUX API: {str(e)}")
                
        except Exception as e:
            logger.exception(f"Unexpected error processing URL {url}: {str(e)}")
            raise
    
    @staticmethod
    def process_crux_data(raw_data):
        processed_data = {
            "url": raw_data.get("record", {}).get("key", {}).get("url", "Unknown URL"),
            "metrics": {}
        }
        
        metrics = raw_data.get("record", {}).get("metrics", {})
        for metric_name, metric_data in metrics.items():
            histogram = metric_data.get("histogram", [])
            percentiles = metric_data.get("percentiles", {})
            
            processed_data["metrics"][metric_name] = {
                "histogram": histogram,
                "percentiles": percentiles
            }
        
        return processed_data
    
    @classmethod
    def calculate_statistics(cls, processed_data_list):
        if not processed_data_list:
            return {}

        statistics = {
            "averages": {},
            "sums": {},
            "urls": [],
            "count": len(processed_data_list)
        }

        for data in processed_data_list:
            statistics["urls"].append(data["url"])

        all_metrics = set()
        for data in processed_data_list:
            for metric_name in data.get("metrics", {}).keys():
                all_metrics.add(metric_name)

        for metric_name in all_metrics:
            p75_values = []
            p95_values = []

            for data in processed_data_list:
                metrics = data.get("metrics", {})
                if metric_name in metrics:
                    percentiles = metrics[metric_name].get("percentiles", {})
                    try:
                        if "p75" in percentiles:
                            p75_values.append(float(percentiles["p75"]))
                        if "p95" in percentiles:
                            p95_values.append(float(percentiles["p95"]))
                    except (ValueError, TypeError):
                        continue

            if p75_values:
                statistics["averages"][f"{metric_name}_p75"] = sum(p75_values) / len(p75_values)
                statistics["sums"][f"{metric_name}_p75"] = sum(p75_values)
                statistics.setdefault("min", {})[f"{metric_name}_p75"] = min(p75_values)
                statistics.setdefault("max", {})[f"{metric_name}_p75"] = max(p75_values)

            if p95_values:
                statistics["averages"][f"{metric_name}_p95"] = sum(p95_values) / len(p95_values)
                statistics["sums"][f"{metric_name}_p95"] = sum(p95_values)
                statistics.setdefault("min", {})[f"{metric_name}_p95"] = min(p95_values)
                statistics.setdefault("max", {})[f"{metric_name}_p95"] = max(p95_values)

        return statistics

    @classmethod
    def calculate_insights(cls, processed_data_list):
        """
        Analyze the processed data and return insights/recommendations.
        For demonstration, we use hardcoded thresholds.
        """
        insights = []
        # Example thresholds (in milliseconds, except for CLS which is unit-less)
        thresholds = {
            "largest_contentful_paint": {"p75": 2500},
            "first_contentful_paint": {"p75": 1800},
            "cumulative_layout_shift": {"p75": 0.1},
        }
        
        # Loop over each record to generate per-URL insights
        for data in processed_data_list:
            url = data.get("url")
            url_insights = {"url": url, "recommendations": []}
            metrics = data.get("metrics", {})
            
            # For each metric, check if it exceeds our defined threshold
            for metric, limits in thresholds.items():
                if metric in metrics:
                    percentiles = metrics[metric].get("percentiles", {})
                    # Check for the p75 value if available
                    p75_value = None
                    try:
                        p75_value = float(percentiles.get("p75"))
                    except (TypeError, ValueError):
                        p75_value = None
                    
                    if p75_value is not None:
                        if p75_value > limits["p75"]:
                            if metric == "largest_contentful_paint":
                                url_insights["recommendations"].append(
                                    f"Optimize images and server responses to improve LCP (p75: {p75_value} ms)."
                                )
                            elif metric == "first_contentful_paint":
                                url_insights["recommendations"].append(
                                    f"Consider lazy-loading and code splitting to lower FCP (p75: {p75_value} ms)."
                                )
                            elif metric == "cumulative_layout_shift":
                                url_insights["recommendations"].append(
                                    f"Reserve space for dynamic content to reduce CLS (p75: {p75_value})."
                                )
            if url_insights["recommendations"]:
                insights.append(url_insights)
        
        # Optionally, add global insights based on the aggregated statistics
        if not insights:
            insights.append({"message": "All URLs appear to meet performance criteria."})
            
        return insights