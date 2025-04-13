from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
import logging

from .services import CruxService
from .serializers import SingleUrlSerializer, MultiUrlExtendedSerializer
from .exceptions import CrUXApiError, InvalidURLError, ApiConnectionError, ApiResponseError

# Set up logging
logger = logging.getLogger(__name__)

class CruxDataView(APIView):
    """API view for fetching CrUX data for a single URL"""
    
    def post(self, request):
        """Handle POST request with a single URL"""
        serializer = SingleUrlSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid input", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        url = serializer.validated_data['url']
        
        try:
            processed_data = CruxService.fetch_crux_data(url)
            # Optionally, you could also generate insights for the single URL here
            insights = CruxService.calculate_insights([processed_data])
            processed_data["insights"] = insights
            return Response(processed_data)
            
        except InvalidURLError as e:
            logger.warning(f"Invalid URL provided: {url}. Error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        except ApiConnectionError as e:
            logger.error(f"API connection error for URL {url}: {str(e)}")
            return Response(
                {"error": "Connection error", "details": str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
            
        except ApiResponseError as e:
            logger.error(f"API response error for URL {url}: {str(e)}")
            return Response(
                {"error": "API error", "details": str(e)},
                status=status.HTTP_502_BAD_GATEWAY
            )
            
        except Exception as e:
            logger.exception(f"Unexpected error processing URL {url}: {str(e)}")
            return Response(
                {"error": "Server error", "details": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MultiUrlCruxDataView(APIView):
    """API view for fetching CrUX data for multiple URLs with filtering, sorting, and insights."""
    
    def post(self, request):
        """Handle POST request with multiple URLs and optional filter/sort parameters"""
        serializer = MultiUrlExtendedSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid input", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        urls = serializer.validated_data['urls']
        sort_by = serializer.validated_data.get('sort_by', "")
        sort_order = serializer.validated_data.get('sort_order', "asc")
        filter_threshold = serializer.validated_data.get('filter_threshold')

        processed_data_list = []
        error_urls = []
        
        for url in urls:
            try:
                processed_data = CruxService.fetch_crux_data(url)
                processed_data_list.append(processed_data)
            except CrUXApiError as e:
                error_urls.append({"url": url, "error": str(e)})
                logger.warning(f"Error processing URL {url}: {str(e)}")
        
        # Calculate statistics if we have any successful data
        statistics = {}
        if processed_data_list:
            statistics = CruxService.calculate_statistics(processed_data_list)
        
        # Filtering: if sort_by and filter_threshold are provided, filter out records that do not meet the threshold.
        if sort_by and filter_threshold is not None:
            # sort_by is expected in the form "metricName_percentile" e.g., "largest_contentful_paint_p75"
            def metric_value(item):
                try:
                    metric, percentile = sort_by.rsplit("_", 1)
                    value = item.get("metrics", {}).get(metric, {}).get("percentiles", {}).get(percentile)
                    return float(value) if value is not None else None
                except Exception:
                    return None
                    
            before_count = len(processed_data_list)
            processed_data_list = [
                item for item in processed_data_list 
                if (metric_value(item) is not None and metric_value(item) >= filter_threshold)
            ]
            logger.info(f"Filtered from {before_count} to {len(processed_data_list)} records based on threshold {filter_threshold} for {sort_by}")
        
        # Sorting: sort by the specified metric value if sort_by is provided
        if sort_by:
            def metric_value(item):
                try:
                    metric, percentile = sort_by.rsplit("_", 1)
                    value = item.get("metrics", {}).get(metric, {}).get("percentiles", {}).get(percentile)
                    return float(value) if value is not None else float('inf')
                except Exception:
                    return float('inf')
            
            reverse = sort_order == "desc"
            processed_data_list = sorted(processed_data_list, key=metric_value, reverse=reverse)
            logger.info(f"Sorted data by {sort_by} in {'descending' if reverse else 'ascending'} order")
        
        # Generate insights based on the processed data (across multiple URLs)
        insights = CruxService.calculate_insights(processed_data_list)
        
        response_data = {
            "url_data": processed_data_list,
            "statistics": statistics,
            "insights": insights
        }
        
        if error_urls:
            response_data["errors"] = error_urls
        
        return Response(response_data)

def health_check(request):
    return JsonResponse({'status': 'ok'})