from rest_framework import viewsets
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny

from apps.portfolio.models import Entry, Profile, Tag

from .serializers import EntrySerializer, ProfileSerializer, TagSerializer


class EntryViewSet(viewsets.ReadOnlyModelViewSet):
    """Published, non-sample entries only -- never exposes drafts or samples."""

    serializer_class = EntrySerializer
    permission_classes = [AllowAny]
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
    permission_classes = [AllowAny]
    lookup_field = "slug"
    pagination_class = None


class ProfileView(RetrieveAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [AllowAny]

    def get_object(self) -> Profile:
        return Profile.get_solo()
