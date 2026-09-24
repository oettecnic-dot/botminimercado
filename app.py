import os
import urllib.parse
import logging
import time
from functools import wraps
import pandas as pd
from flask import Flask, request, render_template_string, jsonify
from twilio.twiml.messaging_response import MessagingResponse

# Configuración profesional de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

app = Flask(__name__)

# ID de Google Sheets obtenido de forma segura desde las Variables de Entorno de Render
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "1GB6AVyHP4N63i4FrKXw6I1DR087Mm5F0xEGYnF_0_Fk")

# Memoria temporal para los carritos y estados de pago
carritos_clientes = {}
pagos_clientes = {}

# --- DECORADOR DE CACHÉ TTL (Expira cada 5 minutos / 300 segundos) ---
def ttl_cache(ttl_seconds=300):
    def decorator(func):
        cache = {}
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            key = str(args) + str(kwargs)
            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < ttl_seconds:
                    logging.info("⚡ Usando datos en caché de Google Sheets (sin llamadas externas).")
                    return result
            
            logging.info("🔄 Descargando datos frescos desde Google Sheets...")
            result = func(*args, **kwargs)
            cache[key] = (result, now)
            return result
        return wrapper
    return decorator

# Función auxiliar para leer los datos del Minimercado (Pestaña "Productos")
@ttl_cache(ttl_seconds=300)
def obtener_datos_minimercado():
    try:
        sheet_name = urllib.parse.quote("Productos")
        url_productos = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        
        # Leemos el CSV limitándolo estrictamente a las primeras 7 columnas (0 a 6)
        df = pd.read_csv(url_productos, usecols=[0, 1, 2, 3, 4, 5, 6])
        # Estandarizamos los nombres de las columnas internas para evitar errores
        df.columns = ['codigo', 'categoria', 'subcategoria', 'nombre', 'descripcion', 'precio', 'stock']
        return df
    except Exception as e:
        logging.error(f"Error al leer Google Sheets: {e}")
        return None

# Función reforzada para limpiar caracteres especiales que rompen el XML de WhatsApp/Twilio
def limpiar_texto(texto):
    if pd.isna(texto):
        return ""
    return str(texto).replace('&', 'y').replace('<', '').replace('>', '').replace('"', '').replace("'", "")

# --- LÓGICA CENTRAL DEL BOT DE MINIMERCADO ---
def procesar_logica_minimercado(remitente, incoming_msg, profile_name=None):
    msg_lower = incoming_msg.strip().lower()
    logging.info(f"Mensaje recibido de [{remitente}] ({profile_name}): {incoming_msg}")

    if remitente not in carritos_clientes:
        carritos_clientes[remitente] = []
    if remitente not in pagos_clientes:
        pagos_clientes[remitente] = "ninguno"

    respuesta_texto = ""
    df_menu = obtener_datos_minimercado()

    if df_menu is None:
        return "⚠️ No se pudo conectar con la base de datos de productos en este momento."

    # 0. PRIORIDAD: Selección de método de pago
    if pagos_clientes[remitente] == "pendiente":
        if msg_lower in ["1", "2", "3"]:
            carrito = carritos_clientes.get(remitente, [])
            total_apagar = sum(item['precio'] for item in carrito)
            nombre_cliente = profile_name or "Cliente"
            
            if msg_lower == "1":
                metodo = "Efectivo (contra entrega)"
                instrucciones = "Tené en cuenta el monto exacto si es posible."
            elif msg_lower == "2":
                metodo = "Transferencia Bancaria"
                instrucciones = "Alias para transferir: *minimercado.mp*\n(Envíanos el comprobante)."
            else:
                metodo = "Mercado Pago"
                instrucciones = "Podés abonar con dinero en cuenta al recibir."

            respuesta_texto = (
                f"✅ ¡Pedido confirmado con éxito, {nombre_cliente}!\n\n"
                f"🛒 Total a Pagar: ${total_apagar}\n"
                f"💳 Método de pago: {metodo}\n\n"
                f"ℹ️ {instrucciones}\n\n"
                "En breve coordinamos la entrega. ¡Muchas gracias por elegirnos! 🛒"
            )
            carritos_clientes[remitente] = []
            pagos_clientes[remitente] = "finalizado"
        else:
            respuesta_texto = "⚠️ Por favor, respondé con un número válido:\n1️⃣ Efectivo\n2️⃣ Transferencia\n3️⃣ Mercado Pago"

    # 1. Saludo inicial
    elif any(word in msg_lower for word in ["hola", "buenas", "catalogo", "empezar", "comenzar"]):
        pagos_clientes[remitente] = "ninguno"
        categorias_disponibles = df_menu['categoria'].dropna().unique()
        
        respuesta_texto = (
            "¡Hola! Te damos la bienvenida a nuestro *Minimercado* 🛒✨\n\n"
            "¿Qué estás buscando hoy? Podés escribir el nombre de un producto (ej: *fideos*, *coca*, *aceite*) o elegir una categoría:\n\n"
        )
        for cat in categorias_disponibles:
            respuesta_texto += f"🔸 *{str(cat).upper()}*\n"
        respuesta_texto += "\n*(Escribí el nombre de una categoría o producto para buscar).* "

    # 2. Ver total / carrito
    elif msg_lower in ["total", "carrito", "pedido"]:
        carrito = carritos_clientes[remitente]
        if not carrito:
            respuesta_texto = "🛒 *Tu carrito está vacío.*\n\nEscribí el nombre de un producto para empezar a sumar."
        else:
            detalle = "🛒 *Resumen de tu Pedido:*\n\n"
            total_apagar = 0
            for item in carrito:
                detalle += f"• {item['nombre']} — ${item['precio']}\n"
                total_apagar += item['precio']
            detalle += f"\n💰 *Total a Pagar: ${total_apagar}*\n\n¿Deseás confirmar tu pedido? Escribí *'confirmar'*."
            respuesta_texto = detalle

    # 3. Vaciar carrito
    elif msg_lower in ["vaciar", "limpiar"]:
        carritos_clientes[remitente] = []
        pagos_clientes[remitente] = "ninguno"
        respuesta_texto = "🗑️ Has vaciado tu carrito."

    # 4. Confirmar pedido
    elif msg_lower in ["confirmar", "finalizar"]:
        carrito = carritos_clientes[remitente]
        if not carrito:
            respuesta_texto = "Tu carrito está vacío, no hay nada que confirmar."
        else:
            pagos_clientes[remitente] = "pendiente"
            respuesta_texto = (
                "💳 *Seleccioná tu forma de pago:*\n\n"
                "1️⃣ Efectivo\n"
                "2️⃣ Transferencia Bancaria\n"
                "3️⃣ Mercado Pago\n\n"
                "Respondé con el número de la opción elegida (1, 2 o 3)."
            )

    else:
        # Búsqueda 1: ¿Escribió el nombre exacto de una Categoría?
        categorias_disponibles = df_menu['categoria'].dropna().unique()
        categoria_encontrada = next((cat for cat in categorias_disponibles if str(cat).strip().lower() == msg_lower), None)

        if categoria_encontrada:
            grupo = df_menu[df_menu['categoria'] == categoria_encontrada]
            respuesta_texto = f"📋 *Categoría: {str(categoria_encontrada).upper()}* 🛒\n\n"
            
            for _, row in grupo.head(10).iterrows():
                codigo = limpiar_texto(row['codigo'])
                nombre = limpiar_texto(row['nombre'])
                desc = limpiar_texto(row['descripcion'])
                precio = row['precio']
                stock = str(row['stock']).upper()
                
                estado_stock = "✅ Stock" if stock == "SI" else "❌ Sin Stock"
                respuesta_texto += f"• `{codigo}` - *{nombre}* ({desc})\n  Precio: ${precio} | {estado_stock}\n\n"
                
            respuesta_texto += "*(Escribí el código del producto para sumarlo a tu carrito).* "

        else:
            # Búsqueda 2: ¿Escribió un código exacto de producto?
            match_codigo = df_menu[df_menu['codigo'].astype(str).str.lower() == msg_lower]
            
            if not match_codigo.empty:
                match = match_codigo.iloc[0]
                stock_disponible = str(match['stock']).strip().upper()
                
                if stock_disponible != "SI":
                    respuesta_texto = f"❌ Lo sentimos, el producto *{match['nombre']}* se encuentra sin stock por el momento."
                else:
                    producto_encontrado = {
                        'nombre': f"{limpiar_texto(match['nombre'])} ({limpiar_texto(match['descripcion'])})",
                        'precio': float(match['precio'])
                    }
                    carritos_clientes[remitente].append(producto_encontrado)
                    total_parcial = sum(item['precio'] for item in carritos_clientes[remitente])
                    respuesta_texto = (
                        f"✅ ¡Agregado a tu pedido!\n"
                        f"• *{producto_encontrado['nombre']}* (${producto_encontrado['precio']})\n\n"
                        f"🛒 Subtotal parcial: *${total_parcial}*\n"
                        f"*(Escribí 'total' para ver tu carrito o seguí buscando).* "
                    )
            else:
                # Búsqueda 3: Búsqueda flexible por palabras clave (nombre o descripción)
                resultados = df_menu[
                    df_menu['nombre'].astype(str).str.lower().str.contains(msg_lower, na=False) |
                    df_menu['descripcion'].astype(str).str.lower().str.contains(msg_lower, na=False)
                ]

                if not resultados.empty:
                    respuesta_texto = f"🔍 *Resultados para \"{incoming_msg}\":*\n\n"
                    for _, row in resultados.head(5).iterrows():
                        codigo = limpiar_texto(row['codigo'])
                        nombre = limpiar_texto(row['nombre'])
                        desc = limpiar_texto(row['descripcion'])
                        precio = row['precio']
                        stock = str(row['stock']).upper()
                        
                        estado_stock = "✅" if stock == "SI" else "❌ Sin stock"
                        respuesta_texto += f"• `{codigo}` - *{nombre}* {desc}\n  Precio: ${precio} {estado_stock}\n\n"
                        
                    respuesta_texto += "*(Enviá el código del producto para sumarlo a tu pedido).* "
                else:
                    respuesta_texto = (
                        f"No encontramos productos con el término \"{incoming_msg}\".\n"
                        "💡 Probá escribiendo otra palabra clave o el nombre de una categoría."
                    )

    return respuesta_texto

# --- RUTA WEB INTERACTIVA (Chat en la URL) ---
@app.route("/", methods=["GET"])
def home():
    html_template = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bot Minimercado - Asistente Virtual 🛒</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #e5ddd5; margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; }
            .chat-container { width: 100%; max-width: 450px; height: 90vh; background: #ffffff; display: flex; flex-direction: column; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); overflow: hidden; }
            .chat-header { background: #128c7e; color: white; padding: 15px; text-align: center; font-size: 18px; font-weight: bold; }
            .chat-messages { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background: #efeae2; }
            .message { max-width: 75%; padding: 10px 14px; border-radius: 8px; font-size: 14px; line-height: 1.4; white-space: pre-wrap; }
            .message.user { background: #dcf8c6; align-self: flex-end; border-bottom-right-radius: 0; }
            .message.bot { background: #ffffff; align-self: flex-start; border-bottom-left-radius: 0; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
            .chat-input-area { display: flex; padding: 10px; background: #f0f0f0; border-top: 1px solid #ddd; }
            .chat-input-area input { flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 20px; outline: none; font-size: 14px; }
            .chat-input-area button { background: #128c7e; color: white; border: none; padding: 10px 20px; margin-left: 8px; border-radius: 20px; cursor: pointer; font-weight: bold; }
            .chat-input-area button:hover { background: #075e54; }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div class="chat-header">🛒 Bot Minimercado - Asistente Virtual</div>
            <div class="chat-messages" id="chatMessages">
                <div class="message bot">¡Hola! Escribí **"Hola"** para comenzar tus compras en línea. 👋</div>
            </div>
            <div class="chat-input-area">
                <input type="text" id="userInput" placeholder="Escribí un mensaje..." onkeypress="handleKeyPress(event)">
                <button onclick="sendMessage()">Enviar</button>
            </div>
        </div>

        <script>
            let sessionId = localStorage.getItem("web_session_id");
            if (!sessionId) {
                sessionId = "web_" + Math.random().toString(36).substring(2, 9);
                localStorage.setItem("web_session_id", sessionId);
            }

            function handleKeyPress(event) {
                if (event.key === "Enter") {
                    sendMessage();
                }
            }

            async function sendMessage() {
                const input = document.getElementById("userInput");
                const text = input.value.trim();
                if (!text) return;

                appendMessage(text, "user");
                input.value = "";

                try {
                    const response = await fetch("/chat-api", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ message: text, session_id: sessionId })
                    });
                    const data = await response.json();
                    appendMessage(data.reply, "bot");
                } catch (error) {
                    appendMessage("⚠️ Error de conexión con el servidor.", "bot");
                }
            }

            function appendMessage(text, sender) {
                const messagesContainer = document.getElementById("chatMessages");
                const msgDiv = document.createElement("div");
                msgDiv.className = `message ${sender}`;
                msgDiv.innerText = text;
                messagesContainer.appendChild(msgDiv);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)

# --- API PARA CHAT WEB ---
@app.route("/chat-api", methods=["POST"])
def chat_api():
    data = request.get_json()
    incoming_msg = data.get("message", "")
    session_id = data.get("session_id", "web_default")
    
    respuesta = procesar_logica_minimercado(session_id, incoming_msg)
    return jsonify({"reply": respuesta})

# --- WEBHOOK DE WHATSAPP ---
@app.route("/bot", methods=["POST"])
def bot_whatsapp():
    remitente = request.values.get('From', '')
    incoming_msg = request.values.get('Body', '').strip()
    profile_name = request.values.get('ProfileName', 'Cliente')
    
    resp = MessagingResponse()
    respuesta = procesar_logica_minimercado(remitente, incoming_msg, profile_name)
    
    resp.message(respuesta)
    return str(resp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False) 
