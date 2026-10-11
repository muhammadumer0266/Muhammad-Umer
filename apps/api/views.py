from rest_framework import viewsets
from rest_framework.generics import RetrieveAPIView

from apps.portfolio.models import Entry, Profile, Tag
from apps.portfolio.selectors import published_certifications

from .permissions import ReadOnly
from .serializers import (
    CertificationSerializer,
    EntrySerializer,
    ProfileSerializer,
    TagSerializer,
)


class EntryViewSet(viewsets.ReadOnlyModelViewSet):
    """Published, non-sample entries only -- never exposes drafts or samples."""

    serializer_class = EntrySerializer
    permission_classes = [ReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        qs = Entry.objects.filter(is_published=True, is_sample=False).prefetch_related("tags")
        kind = self.request.query_params.get("kind")
        if kind:
            qs = qs.filter(kind=kind)
        tag = self.request.query_params.get("tag")
        if tag:
            qs = qs.filter(tags__slug=tag)
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs.distinct()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [ReadOnly]
    lookup_field = "slug"
    pagination_class = None


class ProfileView(RetrieveAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [ReadOnly]

    def get_object(self) -> Profile:
        return Profile.get_solo()


class CertificationViewSet(viewsets.ReadOnlyModelViewSet):
    """Published certifications only."""

    serializer_class = CertificationSerializer
    permission_classes = [ReadOnly]
    pagination_class = None

    def get_queryset(self):
        return published_certifications()
