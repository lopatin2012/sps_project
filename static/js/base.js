// Автоматически добавляем CSRF-токен ко всем исходящим запросам HTMX
document.body.addEventListener('htmx:configRequest', function(evt) {
    const token = document.querySelector('meta[name="csrf-token"]')?.content;
    if (token) {
        evt.detail.headers['X-CSRFToken'] = token;
    }
});

// Вспомогательная функция: декодирует Base64 → UTF-8 строку
function decodeBase64UTF8(base64) {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    return new TextDecoder('utf-8').decode(bytes);
}

document.body.addEventListener('htmx:afterRequest', function(evt) {
    // 1. Закрываем модалку
    if (evt.detail.xhr.getResponseHeader('HX-Trigger') === 'nodeSaved') {
        const modal = document.getElementById('modal-overlay');
        if (modal) {
            modal.style.opacity = '0';
            modal.style.transition = 'opacity 0.15s ease';
            setTimeout(() => modal.remove(), 150);
        }
    }

    // 2. Показываем тост с правильным декодированием
    const encodedMsg = evt.detail.xhr.getResponseHeader('HX-Toast-Message');
    if (encodedMsg) {
        try {
            const message = decodeBase64UTF8(encodedMsg);
            showToast(message);
        } catch (e) {
            console.error('Toast decode error:', e);
        }
    }
});

function showToast(message) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.style.cssText = `
        pointer-events: auto;
        background: #10b981;
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        font-size: 0.875rem;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        opacity: 0;
        transform: translateY(10px);
        transition: all 0.3s ease;
    `;
    toast.textContent = message;
    container.appendChild(toast);

    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
    });

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-10px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
