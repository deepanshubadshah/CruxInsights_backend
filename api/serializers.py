from rest_framework import serializers

class SingleUrlSerializer(serializers.Serializer):
    """Serializer for single URL input"""
    url = serializers.URLField(required=True)

class MultiUrlSerializer(serializers.Serializer):
    """Serializer for multiple URL input"""
    urls = serializers.ListField(
        child=serializers.URLField(required=True),
        required=True,
        min_length=1
    )

# Extended serializer for filtering and sorting options
class MultiUrlExtendedSerializer(MultiUrlSerializer):
    sort_by = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Metric to sort by (e.g., 'largest_contentful_paint_p75')"
    )
    sort_order = serializers.ChoiceField(
        choices=["asc", "desc"],
        required=False,
        default="asc",
        help_text="Sort order (ascending or descending)"
    )
    filter_threshold = serializers.FloatField(
        required=False,
        help_text="Only include records where the sort_by metric is greater than or equal to this threshold"
    )
