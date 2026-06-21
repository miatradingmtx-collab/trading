document.addEventListener("DOMContentLoaded", () => {
    // Verificar si ya tenemos el script configurado
    const savedConfigUrl = localStorage.getItem("bp_config_url");

    if (savedConfigUrl) {
        initBotpress(savedConfigUrl);
    } else {
        showSetupUI();
    }
});

function showSetupUI() {
    const main = document.getElementById("chat-container");
    main.innerHTML = `
        <div class="setup-overlay">
            <div class="setup-card">
                <h2>Configuración de Mia</h2>
                <p>Pega aquí la URL de Shareable Link de Botpress</p>
                <input type="text" id="configUrlInput" class="setup-input" placeholder="https://cdn.botpress.cloud/webchat/.../shareable.html?configUrl=...">
                <button class="setup-button" onclick="saveConfig()">Conectar a Mia</button>
            </div>
        </div>
    `;
}

window.saveConfig = function() {
    let input = document.getElementById("configUrlInput").value.trim();
    if (!input) return alert("Por favor pega la URL");
    
    // Extraer el JSON URL si pegó toda la URL del shareable link
    let finalUrl = input;
    if (input.includes("configUrl=")) {
        finalUrl = input.split("configUrl=")[1];
    }

    localStorage.setItem("bp_config_url", finalUrl);
    
    // Limpiar UI y cargar
    document.getElementById("chat-container").innerHTML = "";
    initBotpress(finalUrl);
}

async function initBotpress(configUrl) {
    try {
        // Obtenemos los IDs reales desde el archivo JSON de configuración
        const response = await fetch(configUrl);
        const data = await response.json();
        const clientId = data.clientId || data.botId;

        // Inicializar el Webchat
        window.botpressWebChat.init({
            "composerPlaceholder": "Habla con Mia...",
            "botConversationDescription": "Sistema Algorítmico y Prompt Admin",
            "clientId": clientId,
            "hostUrl": "https://cdn.botpress.cloud/webchat/v2.2",
            "messagingUrl": "https://messaging.botpress.cloud",
            "lazySocket": true,
            "themeName": "prism",
            "frontendVersion": "v2.2",
            "useSessionStorage": true,
            "enableConversationDeletion": true,
            "showPoweredBy": false,
            "className": "mia-webchat",
            "containerWidth": "100%",
            "layoutWidth": "100%",
            "hideWidget": true,
            "disableAnimations": false,
            "theme": "prism",
            "themeColor": "#00f2fe"
        });

        // Evento para forzar que el chat se abra siempre
        window.botpressWebChat.onEvent(function (event) {
            if (event.type === 'LIFECYCLE.LOADED') {
                window.botpressWebChat.sendEvent({ type: 'show' });
            }
        }, ['LIFECYCLE.LOADED']);

    } catch (err) {
        console.error(err);
        alert("Error cargando la configuración de Botpress. Verifica la URL.");
        localStorage.removeItem("bp_config_url");
        showSetupUI();
    }
}
