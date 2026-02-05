import os
import uuid
from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services.pdf_extract import extract_pages, chunk_text
from .services.rag_store import upsert_doc_chunks, query_doc
from .services.rag_answer import build_context, answer_from_context


class HealthView(APIView):
    def get(self, request):
        return Response({"ok": True})


class UploadPdfView(APIView):
    def post(self, request):
        if "file" not in request.FILES:
            return Response({"error": "No file uploaded (field name must be 'file')."}, status=400)

        file = request.FILES["file"]
        if not file.name.lower().endswith(".pdf"):
            return Response({"error": "Only PDF files are supported."}, status=400)

        doc_id = str(uuid.uuid4())

        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        saved_path = default_storage.save(f"{doc_id}_{file.name}", file)
        full_path = os.path.join(settings.MEDIA_ROOT, saved_path)

        # Extract pages
        pages = extract_pages(full_path)
        if not pages:
            return Response({"error": "Could not extract text from this PDF."}, status=400)

        # Chunk and store
        chunks_with_meta = []
        for p in pages:
            page_num = p["page"]
            chunks = chunk_text(p["text"], chunk_size=1200, overlap=200)
            for ch in chunks:
                chunks_with_meta.append({"text": ch, "page": page_num})

        upsert_doc_chunks(doc_id, chunks_with_meta)

        return Response({"doc_id": doc_id, "chunks": len(chunks_with_meta)})


class AskPdfView(APIView):
    def post(self, request):
        doc_id = request.data.get("doc_id")
        question = request.data.get("question")

        if not doc_id or not question:
            return Response({"error": "doc_id and question are required."}, status=400)

        try:
            results = query_doc(doc_id, question, top_k=6)
            items = build_context(results)
            answer, sources = answer_from_context(question, items)
        except Exception as e:
            # NEVER crash the server
            return Response({"error": str(e)}, status=400)

        return Response(
            {
                "answer": answer,
                "sources": sources,
            },
            status=status.HTTP_200_OK
        )
