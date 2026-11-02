from rest_framework import serializers


class ReviewAssuranceSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["APPROVE", "REJECT"])
    review_notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if attrs["decision"] == "REJECT" and not attrs["review_notes"].strip():
            raise serializers.ValidationError({
                "review_notes": "Review notes are required for rejection.",
            })
        return attrs
