from rest_framework import serializers

from apps.portfolio.models import Certification, Entry, Profile, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["name", "slug"]


class EntrySerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Entry
        fields = [
            "slug",
            "title",
            "kind",
            "status",
            "date",
            "summary",
            "tags",
            "metrics",
            "live_url",
            "repo_url",
            "writeup_url",
            "featured",
        ]


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "full_name",
            "alternate_names",
            "headline",
            "bio_short",
            "available_for_work",
            "location_display",
        ]


class CertificationSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    certificate_url = serializers.SerializerMethodField()
    badge_url = serializers.SerializerMethodField()

    class Meta:
        model = Certification
        fields = [
            "title",
            "issuer",
            "issue_date",
            "expiry_date",
            "credential_id",
            "credential_url",
            "description",
            "tags",
            "badge_url",
            "certificate_url",
        ]

    def _file_url(self, file) -> str | None:
        if not file:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(file.url) if request else file.url

    def get_certificate_url(self, obj: Certification) -> str | None:
        return self._file_url(obj.certificate_file)

    def get_badge_url(self, obj: Certification) -> str | None:
        return self._file_url(obj.badge_image)
