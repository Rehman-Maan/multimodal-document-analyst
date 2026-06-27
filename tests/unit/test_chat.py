import pytest
import openai
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import override_settings
from django.urls import reverse

from apps.chat.models import ChatMessage, ChatSession, DocumentChunk
from apps.chat.views import build_chat_exchanges
from apps.documents.models import DocumentPage, UploadedDocument
from apps.extraction.models import ExtractedField, ExtractionRun
from apps.workspaces.models import Workspace, WorkspaceMembership
from services.retrieval import answers as answer_service
from services.retrieval.answers import answer_document_question
from services.retrieval.chunking import chunk_document_pages
from services.retrieval.embeddings import LOCAL_EMBEDDING_MODEL, embed_text
from services.retrieval.indexing import index_document
from services.retrieval.search import search_document


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def isolated_media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.OPENAI_API_KEY = ""


def make_workspace():
    user = get_user_model().objects.create_user(username="chat_user", password="pass")
    workspace = Workspace.objects.create(name="Chat Ops", created_by=user)
    WorkspaceMembership.objects.create(
        workspace=workspace,
        user=user,
        role=WorkspaceMembership.Role.OWNER,
    )
    return user, workspace


def make_document(user, workspace):
    document = UploadedDocument.objects.create(
        workspace=workspace,
        title="Policy",
        file_type="PDF",
        uploaded_by=user,
        file_size=11,
        status=UploadedDocument.Status.PROCESSED,
    )
    document.file.save("policy.pdf", ContentFile(b"hello world"), save=True)
    DocumentPage.objects.create(
        document=document,
        page_number=1,
        text_content=(
            "The refund policy allows customers to request a refund within 30 days. "
            "Receipts must include the invoice number and total amount."
        ),
    )
    DocumentPage.objects.create(
        document=document,
        page_number=2,
        text_content="Shipping documents include carrier name, tracking number, and delivery date.",
    )
    return document


def test_chunk_document_pages_preserves_page_citations():
    user, workspace = make_workspace()
    document = make_document(user, workspace)

    chunks = chunk_document_pages(document.pages.all(), max_words=8, overlap_words=2)

    assert chunks
    assert chunks[0].page_number == 1
    assert chunks[0].chunk_index == 0
    assert "refund policy" in chunks[0].text


@override_settings(OPENAI_API_KEY="")
def test_index_document_creates_embeddings_and_search_returns_relevant_chunk():
    user, workspace = make_workspace()
    document = make_document(user, workspace)

    count = index_document(document)
    results = search_document(document, "refund request invoice", limit=1)

    assert count == 2
    assert DocumentChunk.objects.filter(document=document).count() == 2
    assert results[0]["chunk"].page_number == 1
    assert results[0]["score"] > 0


@override_settings(OPENAI_API_KEY="")
def test_answer_document_question_stores_user_assistant_and_citations():
    user, workspace = make_workspace()
    document = make_document(user, workspace)
    index_document(document)
    session = ChatSession.objects.create(
        workspace=workspace,
        document=document,
        created_by=user,
    )

    answer = answer_document_question(session, "What is the refund window?")

    assert answer.role == ChatMessage.Role.ASSISTANT
    assert "30 days" in answer.content
    assert answer.citations
    assert answer.citations[0]["page_number"] == 1
    assert session.messages.count() == 2


@override_settings(OPENAI_API_KEY="")
def test_document_chat_api_indexes_and_returns_cited_answer(client):
    user, workspace = make_workspace()
    document = make_document(user, workspace)
    client.force_login(user)

    response = client.post(
        reverse("api-document-chat", kwargs={"pk": document.pk}),
        {"question": "What can customers request?"},
        content_type="application/json",
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["messages"][-1]["role"] == ChatMessage.Role.ASSISTANT
    assert payload["messages"][-1]["citations"]


@override_settings(OPENAI_API_KEY="")
def test_document_chat_view_handles_multiple_existing_sessions(client):
    user, workspace = make_workspace()
    document = make_document(user, workspace)
    ChatSession.objects.create(workspace=workspace, document=document, created_by=user, title="Old")
    latest = ChatSession.objects.create(
        workspace=workspace,
        document=document,
        created_by=user,
        title="Latest",
    )
    client.force_login(user)

    response = client.get(
        reverse(
            "document-chat",
            kwargs={"workspace_slug": workspace.slug, "document_pk": document.pk},
        )
    )

    assert response.status_code == 200
    assert response.context["session"] == latest


@override_settings(OPENAI_API_KEY="")
def test_document_chat_post_handles_multiple_existing_sessions(client):
    user, workspace = make_workspace()
    document = make_document(user, workspace)
    index_document(document)
    ChatSession.objects.create(workspace=workspace, document=document, created_by=user, title="Old")
    latest = ChatSession.objects.create(
        workspace=workspace,
        document=document,
        created_by=user,
        title="Latest",
    )
    client.force_login(user)

    response = client.post(
        reverse(
            "document-chat-ask",
            kwargs={"workspace_slug": workspace.slug, "document_pk": document.pk},
        ),
        {"question": "What is the refund window?"},
    )

    assert response.status_code == 302
    assert latest.messages.filter(role=ChatMessage.Role.ASSISTANT).exists()


@override_settings(OPENAI_API_KEY="")
def test_document_chat_ajax_returns_answer_payload(client):
    user, workspace = make_workspace()
    document = make_document(user, workspace)
    index_document(document)
    client.force_login(user)

    response = client.post(
        reverse(
            "document-chat-ask",
            kwargs={"workspace_slug": workspace.slug, "document_pk": document.pk},
        ),
        {"question": "What is the refund window?"},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["question"] == "What is the refund window?"
    assert "30 days" in payload["answer"]
    assert payload["citations"]


def test_build_chat_exchanges_returns_newest_pair_first():
    user, workspace = make_workspace()
    document = make_document(user, workspace)
    session = ChatSession.objects.create(workspace=workspace, document=document, created_by=user)
    old_user = ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.USER,
        content="Old question",
    )
    ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.ASSISTANT,
        content="Old answer",
    )
    ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.USER,
        content="Latest question",
    )
    latest_assistant = ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.ASSISTANT,
        content="Latest answer",
    )

    exchanges = build_chat_exchanges(session.messages.all())

    assert exchanges[0]["assistant"] == latest_assistant
    assert exchanges[-1]["user"] == old_user


@override_settings(OPENAI_API_KEY="sk-test")
def test_answer_falls_back_when_openai_response_fails(monkeypatch):
    user, workspace = make_workspace()
    document = make_document(user, workspace)
    index_document(document)
    session = ChatSession.objects.create(
        workspace=workspace,
        document=document,
        created_by=user,
    )

    class BrokenResponses:
        def create(self, **kwargs):
            raise RuntimeError("network down")

    class BrokenClient:
        responses = BrokenResponses()

    monkeypatch.setattr(openai, "OpenAI", lambda api_key: BrokenClient())

    answer = answer_document_question(session, "What is the refund window?")

    assert answer.role == ChatMessage.Role.ASSISTANT
    assert "30 days" in answer.content
    assert answer.citations


@override_settings(OPENAI_API_KEY="")
def test_resume_question_returns_direct_skill_answer():
    user, workspace = make_workspace()
    document = UploadedDocument.objects.create(
        workspace=workspace,
        title="Resume",
        file_type="PDF",
        uploaded_by=user,
        file_size=11,
        status=UploadedDocument.Status.PROCESSED,
    )
    document.file.save("resume.pdf", ContentFile(b"hello world"), save=True)
    DocumentPage.objects.create(
        document=document,
        page_number=1,
        text_content=(
            "Rao Abdul Rehman\n"
            "Professional Summary\n"
            "Odoo ERP Developer and Technical Consultant focused on custom module development.\n"
            "Technical Skills\n"
            "Odoo Development: Odoo 14, Odoo 16, Odoo 18, Odoo 19, Custom Modules, ORM, QWeb.\n"
        ),
    )
    index_document(document)
    session = ChatSession.objects.create(
        workspace=workspace,
        document=document,
        created_by=user,
    )

    answer = answer_document_question(session, "Does Rao Abdul Rehman know Odoo?")

    assert answer.content.startswith("Yes.")
    assert "Odoo" in answer.content
    assert "Technical Skills" in answer.content or "Odoo Development" in answer.content
    assert len(answer.citations) <= 2


@override_settings(OPENAI_API_KEY="")
def test_resume_qualification_question_returns_education_answer():
    user, workspace = make_workspace()
    document = UploadedDocument.objects.create(
        workspace=workspace,
        title="Resume",
        file_type="PDF",
        uploaded_by=user,
        file_size=11,
        status=UploadedDocument.Status.PROCESSED,
    )
    document.file.save("resume.pdf", ContentFile(b"hello world"), save=True)
    DocumentPage.objects.create(
        document=document,
        page_number=1,
        text_content=(
            "Projects\n"
            "AutoXcel automobile management system.\n"
            "Education\n"
            "Bachelor of Engineering in Computer and Information Systems Engineering, "
            "NED University of Engineering and Technology, Karachi, Pakistan "
            "Nov 2021 - Jun 2025 "
            "CGPA: 3.46/4.00 "
            "Intermediate in Pre-Engineering, Adamjee Government Science College"
        ),
    )
    index_document(document)
    session = ChatSession.objects.create(
        workspace=workspace,
        document=document,
        created_by=user,
    )

    answer = answer_document_question(session, "latest qualification of him")

    assert "Bachelor of Engineering" in answer.content
    assert "NED University" in answer.content
    assert "3.46/4.00" in answer.content
    assert "Bachelor" in answer.citations[0]["excerpt"]
    assert len(answer.citations) <= 2


@override_settings(OPENAI_API_KEY="sk-test", OPENAI_CHAT_MODEL="gpt-test")
def test_openai_prompt_interprets_finished_date_ranges_as_completed(monkeypatch):
    user, workspace = make_workspace()
    document = UploadedDocument.objects.create(
        workspace=workspace,
        title="Resume",
        file_type="PDF",
        uploaded_by=user,
        file_size=11,
        status=UploadedDocument.Status.PROCESSED,
    )
    document.file.save("resume.pdf", ContentFile(b"hello world"), save=True)
    run = ExtractionRun.objects.create(document=document, status=ExtractionRun.Status.COMPLETED)
    ExtractedField.objects.create(
        run=run,
        document=document,
        field_name="education",
        normalized_value=(
            "Bachelor of Engineering in Computer and Information Systems Engineering, "
            "NED University of Engineering and Technology, Karachi, Pakistan Nov 2021 - Jun 2025"
        ),
        confidence=0.9,
        source_page=2,
    )
    chunk = DocumentChunk.objects.create(
        workspace=workspace,
        document=document,
        page_number=2,
        chunk_index=0,
        text=(
            "Education Bachelor of Engineering in Computer and Information Systems Engineering, "
            "NED University of Engineering and Technology, Karachi, Pakistan Nov 2021 - Jun 2025"
        ),
    )
    session = ChatSession.objects.create(workspace=workspace, document=document, created_by=user)
    captured = {}

    class FakeResponses:
        def create(self, **kwargs):
            captured["input"] = kwargs["input"]

            class Response:
                output_text = "Yes, he has completed a Bachelor of Engineering."

            return Response()

    class FakeClient:
        responses = FakeResponses()

    monkeypatch.setattr(answer_service, "get_openai_client", lambda: FakeClient())

    answer, citations = answer_service._answer_with_openai(
        session,
        "is he an engineer?",
        [{"chunk": chunk, "score": 1.0}],
    )

    assert "Current date:" in captured["input"]
    assert "ended before the current date" in captured["input"]
    assert "not pursuing/current/ongoing" in captured["input"]
    assert "completed" in answer
    assert citations


@override_settings(OPENAI_API_KEY="")
def test_resume_current_employer_question_returns_job_title():
    user, workspace = make_workspace()
    document = UploadedDocument.objects.create(
        workspace=workspace,
        title="Resume",
        file_type="PDF",
        uploaded_by=user,
        file_size=11,
        status=UploadedDocument.Status.PROCESSED,
    )
    document.file.save("resume.pdf", ContentFile(b"hello world"), save=True)
    DocumentPage.objects.create(
        document=document,
        page_number=1,
        text_content=(
            "Professional Experience\n"
            "Odoo Technical Consultant, Odolution (Official Odoo Gold Partner), "
            "Karachi, Pakistan Sep 2024 - Present\n"
            "Built and customized Odoo modules, reports, and POS screens."
        ),
    )
    index_document(document)
    session = ChatSession.objects.create(
        workspace=workspace,
        document=document,
        created_by=user,
    )

    answer = answer_document_question(session, "current employer and job title")

    assert "Odoo Technical Consultant" in answer.content
    assert "Odolution" in answer.content
    assert "Sep 2024 - Present" in answer.content
    assert "Odolution" in answer.citations[0]["excerpt"]
    assert len(answer.citations) <= 2


@override_settings(OPENAI_API_KEY="")
def test_resume_employed_question_matches_experience_terms():
    user, workspace = make_workspace()
    document = UploadedDocument.objects.create(
        workspace=workspace,
        title="Resume",
        file_type="PDF",
        uploaded_by=user,
        file_size=11,
        status=UploadedDocument.Status.PROCESSED,
    )
    document.file.save("resume.pdf", ContentFile(b"hello world"), save=True)
    DocumentPage.objects.create(
        document=document,
        page_number=1,
        text_content=(
            "Professional Experience\n"
            "Odoo Technical Consultant, Odolution, Karachi, Pakistan Sep 2024 - Present"
        ),
    )
    run = ExtractionRun.objects.create(document=document, status=ExtractionRun.Status.COMPLETED)
    ExtractedField.objects.create(
        run=run,
        document=document,
        field_name="professional_experience",
        normalized_value="Odoo Technical Consultant, Odolution, Karachi, Pakistan Sep 2024 - Present",
        confidence=0.8,
        source_page=1,
    )
    index_document(document)
    session = ChatSession.objects.create(
        workspace=workspace,
        document=document,
        created_by=user,
    )

    answer = answer_document_question(session, "is he employed")

    assert "Odoo Technical Consultant" in answer.content
    assert "Odolution" in answer.content


@override_settings(OPENAI_API_KEY="")
def test_unsupported_yes_no_question_is_clear_not_broken():
    user, workspace = make_workspace()
    document = make_document(user, workspace)
    index_document(document)
    session = ChatSession.objects.create(
        workspace=workspace,
        document=document,
        created_by=user,
    )

    answer = answer_document_question(session, "is he a doctor?")

    assert answer.content == "I do not see evidence for that in the document."
    assert answer.citations == []


@override_settings(OPENAI_API_KEY="")
def test_chat_uses_extracted_fields_for_general_questions():
    user, workspace = make_workspace()
    document = UploadedDocument.objects.create(
        workspace=workspace,
        title="Resume",
        file_type="PDF",
        uploaded_by=user,
        file_size=11,
        status=UploadedDocument.Status.PROCESSED,
    )
    document.file.save("resume.pdf", ContentFile(b"hello world"), save=True)
    DocumentPage.objects.create(
        document=document,
        page_number=1,
        text_content="Rao Abdul Rehman rao789rehman@gmail.com Urdu English",
    )
    run = ExtractionRun.objects.create(document=document, status=ExtractionRun.Status.COMPLETED)
    ExtractedField.objects.create(
        run=run,
        document=document,
        field_name="email",
        normalized_value="rao789rehman@gmail.com",
        confidence=0.95,
        source_page=1,
        source_text="rao789rehman@gmail.com",
    )
    ExtractedField.objects.create(
        run=run,
        document=document,
        field_name="languages",
        normalized_value="Urdu: Native or Bilingual Proficiency; English: Professional Working Proficiency",
        confidence=0.8,
        source_page=1,
        source_text="Urdu and English",
    )
    index_document(document)
    session = ChatSession.objects.create(
        workspace=workspace,
        document=document,
        created_by=user,
    )

    answer = answer_document_question(session, "email address?")

    assert "rao789rehman@gmail.com" in answer.content
    assert answer.citations[0]["source"] == "field:email"
    assert len(answer.citations) <= 2


@override_settings(OPENAI_API_KEY="sk-test")
def test_embedding_falls_back_when_openai_embedding_fails(monkeypatch):
    class BrokenEmbeddings:
        def create(self, **kwargs):
            raise RuntimeError("network down")

    class BrokenClient:
        embeddings = BrokenEmbeddings()

    monkeypatch.setattr(openai, "OpenAI", lambda api_key: BrokenClient())

    _vector, model = embed_text("refund invoice total")

    assert model == LOCAL_EMBEDDING_MODEL
