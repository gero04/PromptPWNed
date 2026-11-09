import io
from fastapi import HTTPException, UploadFile
import pypdf

MAX_PDF_SIZE_BYTES = 100 * 1024  # 100 KB


async def extract_text_from_pdf(upload_file: UploadFile) -> str:
    """Validate and extract plain text from an uploaded PDF file."""
    filename = upload_file.filename or ""
    content_type = (upload_file.content_type or "").lower()

    if not filename.lower().endswith(".pdf") or content_type not in ("application/pdf", "application/x-pdf"):
        raise HTTPException(
            status_code=400,
            detail="Solo se permiten archivos en formato PDF (.pdf)."
        )

    pdf_bytes = await upload_file.read()

    if len(pdf_bytes) == 0:
        raise HTTPException(
            status_code=400,
            detail="El archivo PDF está vacío."
        )

    if len(pdf_bytes) > MAX_PDF_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail="El archivo PDF supera el límite máximo permitido de 100 KB."
        )

    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        extracted_text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Error al procesar el archivo PDF: el archivo está dañado o no es válido."
        )

    if not extracted_text:
        raise HTTPException(
            status_code=400,
            detail="El archivo PDF no contiene texto plano extraíble."
        )

    return extracted_text
