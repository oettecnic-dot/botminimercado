# 📄 Especificación Técnica y Funcional: botminimercado-2026

## 1. Propósito del Sistema
Automatizar la atención comercial, el procesamiento de carritos de compras y la gestión de inventario en tiempo real para un minimercado a través de canales conversacionales (WhatsApp y Chat Web), utilizando **Google Sheets** como base de datos dinámica de lectura y escritura.

---

## 2. Contrato de Datos (Google Sheets — Solapa 0)
La fuente de datos externa debe cumplir estrictamente con el siguiente esquema de columnas (cabeceras en la Fila 1):

| Columna | Nombre de Campo | Tipo de Dato | Descripción / Restricción |
| :--- | :--- | :--- | :--- |
| **A** | `codigo` | Alfanumérico / String | Identificador único del producto (ej: `A101`, `COCA15`). |
| **B** | `categoria` | Texto / String | Sección principal (ej: `Pizzas`, `Bebidas`, `Almacén`). |
| **C** | `subcategoria` | Texto / String | Subdivisión opcional (puede estar vacía). |
| **D** | `nombre` | Texto / String | Nombre comercial del producto. |
| **E** | `descripcion` | Texto / String | Ingredientes, tamaño o detalles adicionales. |
| **F** | `precio` | Numérico / Float | Valor unitario en pesos (ej: `8500`). |
| **G** | `stock` | Numérico / Integer | Unidades físicas disponibles en el local (ej: `15`, `0`). **Es actualizado automáticamente por el bot.** |

---

## 3. Máquina de Estados de la Conversación (FSM)
Cada usuario (identificado por su número de teléfono o ID de sesión web) posee un estado activo dentro del ciclo de compra:

- **ESTADO_INICIAL / MENU:** El usuario recibe el saludo, las categorías o busca productos por texto.
- **ESTADO_ESPERANDO_CANTIDAD:** Tras ingresar un código válido, el bot verifica el stock y solicita la cantidad numérica deseada ($\text{Cantidad} \le \text{Stock}$).
- **ESTADO_PAGO_PENDIENTE:** El usuario confirma su pedido y selecciona un método de pago (`1`: Efectivo, `2`: Transferencia, `3`: Mercado Pago).
- **ESTADO_FINALIZADO:** Se descuenta automáticamente el stock en Google Sheets, se vacía el carrito y se emite el comprobante final.

---

## 4. Reglas de Negocio y Transacciones
1. **Caché TTL (300 segundos):** Optimiza las consultas masivas a Google Sheets protegiendo la API de bloqueos por exceso de peticiones.
2. **Validación de Stock por Cantidad:** Impide que un cliente cargue al carrito más unidades de las que físicamente hay en el local.
3. **Descuento Atómico en Tiempo Real:** Modifica directamente la celda de stock en Google Sheets en el momento exacto en que el cliente confirma su pago.
