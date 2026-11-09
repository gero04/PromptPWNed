/**
 * pdf_upload.js — Dedicated PDF upload handler for LAB-03 (Indirect Injection).
 * Enforces client-side validation (<= 100 KB, .pdf format) and transmits
 * multipart FormData to /api/chat/pdf, delegating UI rendering to lab.js.
 */

const MAX_PDF_SIZE_BYTES = 100 * 1024; // 100 KB
let selectedPdfFile = null;

function handlePdfSelect(event) {
    const file = event.target.files && event.target.files[0];
    const labelEl = document.getElementById('pdfFileName');

    if (!file) {
        selectedPdfFile = null;
        if (labelEl) labelEl.textContent = 'ADJUNTAR PDF (MÁX 100 KB)';
        return;
    }

    const isPdf = file.name.toLowerCase().endsWith('.pdf') || file.type === 'application/pdf';
    if (!isPdf) {
        showToast('ERROR: Solo se permiten archivos .pdf', 'error');
        event.target.value = '';
        selectedPdfFile = null;
        if (labelEl) labelEl.textContent = 'ADJUNTAR PDF (MÁX 100 KB)';
        return;
    }

    if (file.size > MAX_PDF_SIZE_BYTES) {
        showToast('ERROR: El PDF supera el límite de 100 KB', 'error');
        event.target.value = '';
        selectedPdfFile = null;
        if (labelEl) labelEl.textContent = 'ADJUNTAR PDF (MÁX 100 KB)';
        return;
    }

    selectedPdfFile = file;
    if (labelEl) {
        labelEl.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    }
}

async function sendPdfMessage() {
    if (isLoading || !currentLabId) return;

    if (!selectedPdfFile) {
        const fileInput = document.getElementById('pdfInput');
        if (fileInput) fileInput.click();
        showToast('Seleccioná un archivo PDF primero', 'error');
        return;
    }

    const model = document.getElementById('modelSelect').value;
    const fileName = selectedPdfFile.name;
    const fileSizeKb = (selectedPdfFile.size / 1024).toFixed(1);

    addMessage('user', `[PDF ADJUNTO] ${fileName} (${fileSizeKb} KB)`);

    const formData = new FormData();
    formData.append('file', selectedPdfFile);
    formData.append('laboratoryId', currentLabId);
    formData.append('aiCurrentModel', model);
    formData.append('chatHistory', JSON.stringify(chatHistory));

    isLoading = true;
    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn) sendBtn.disabled = true;
    showTyping();

    try {
        const res = await fetch(`${API_BASE}/api/chat/pdf`, {
            method: 'POST',
            body: formData
        });

        if (!res.ok) {
            let errMsg = 'Error del servidor';
            try {
                const err = await res.json();
                errMsg = err.detail || err.message || errMsg;
            } catch (_) { }
            throw new Error(errMsg);
        }

        const data = await res.json();
        if (data.message && !data.chatResponse) {
            throw new Error(data.message);
        }

        removeTyping();
        addMessage('assistant', data.chatResponse);
        chatHistory.push({ role: 'user', content: `[PDF ADJUNTO] ${fileName}` });
        chatHistory.push({ role: 'assistant', content: data.chatResponse });
        checkForSuccess(data.pwned);

        // Reset file input
        selectedPdfFile = null;
        const fileInput = document.getElementById('pdfInput');
        if (fileInput) fileInput.value = '';
        const labelEl = document.getElementById('pdfFileName');
        if (labelEl) labelEl.textContent = 'ADJUNTAR PDF (MÁX 100 KB)';

    } catch (err) {
        removeTyping();
        addSystemMessage('Error al procesar el archivo PDF. Verificá que el backend y Ollama estén activos.');
        showToast('ERROR: ' + err.message, 'error');
    } finally {
        isLoading = false;
        if (sendBtn) sendBtn.disabled = false;
    }
}
