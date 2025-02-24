const baseUrl = window.location.origin;
const endpointUrl = `${baseUrl}/sparql`;
const endpointElement = document.getElementById('endpoint-url');

endpointElement.textContent = endpointUrl;
endpointElement.title = `Click to copy: ${endpointUrl}`;

// Prevenir la navegación y añadir funcionalidad de copiado
endpointElement.addEventListener('click', async (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    try {
        await navigator.clipboard.writeText(endpointUrl);
        const originalText = endpointElement.textContent;
        const originalWidth = endpointElement.offsetWidth;
        endpointElement.style.width = `${originalWidth}px`;
        endpointElement.innerHTML = `<img src="/img/copy-success.svg" alt="Copiado" class="copy-icon">`;
        
        setTimeout(() => {
            endpointElement.style.width = '';
            endpointElement.textContent = originalText;
        }, 1500);
    } catch (err) {
        console.error('Error al copiar:', err);
    }
});