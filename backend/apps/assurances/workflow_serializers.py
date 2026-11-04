from rest_framework import serializers


class ReviewAssuranceSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["APPROVE", "REJECT", "REQUEST_REVISION", "REJECT_FINAL"])
    review_notes = serializers.CharField(required=False, allow_blank=True, default="", max_length=2000)

    def validate(self, attrs):
        if attrs["decision"] != "APPROVE" and not attrs["review_notes"].strip():
            raise serializers.ValidationError({
                "review_notes": "Review notes are required for rejection.",
            })
        return attrs


class InspectionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["START", "VERIFY", "NOTE", "REQUEST_REVISION"])
    section = serializers.ChoiceField(choices=["DATA", "DOCUMENTS", "GENERAL"])
    review_notes = serializers.CharField(required=False, allow_blank=True, default="", max_length=2000)

    def validate(self, attrs):
        if attrs["action"] in ("NOTE", "REQUEST_REVISION") and not attrs["review_notes"].strip():
            raise serializers.ValidationError({"review_notes": "Describe the part requiring review."})
        if attrs["action"] in ("START", "VERIFY") and attrs["section"] == "GENERAL":
            raise serializers.ValidationError({"section": "Choose DATA or DOCUMENTS."})
        return attrs
