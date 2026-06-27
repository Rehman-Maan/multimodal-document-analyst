from apps.chat.models import ChatSession


def get_or_create_active_session(workspace, document, user) -> ChatSession:
    session = (
        ChatSession.objects.filter(
            workspace=workspace,
            document=document,
            created_by=user,
        )
        .order_by("-updated_at", "-created_at", "-pk")
        .first()
    )
    if session:
        return session
    return ChatSession.objects.create(
        workspace=workspace,
        document=document,
        created_by=user,
        title=f"Chat: {document.title}",
    )
