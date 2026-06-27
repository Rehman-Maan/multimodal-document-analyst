from django.urls import path

from apps.chat.api_views import DocumentChatAskAPIView, DocumentIndexAPIView


urlpatterns = [
    path("documents/<int:pk>/chat/", DocumentChatAskAPIView.as_view(), name="api-document-chat"),
    path("documents/<int:pk>/index/", DocumentIndexAPIView.as_view(), name="api-document-index"),
]
