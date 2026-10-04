from rest_framework import serializers

from apps.portfolio.models import Entry, Profile, Tag


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
