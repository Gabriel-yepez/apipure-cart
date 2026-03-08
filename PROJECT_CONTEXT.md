# 📖 Contexto Completo del Proyecto: ApiPure Cart

Este documento sirve como la **fuente única de verdad (Single Source of Truth)** para cualquier agente de Inteligencia Artificial o desarrollador que se integre al proyecto. Contiene información detallada sobre la arquitectura, el stack tecnológico, las decisiones de diseño actuales, convenciones de código y la hoja de ruta (roadmap) para el futuro del proyecto.

---

## 🏗️ 1. Descripción General del Proyecto

**ApiPure Cart** es el backend robusto y escalable para una plataforma moderna de comercio electrónico (e-commerce). Su objetivo principal es proveer una API RESTful rápida y segura que gestione usuarios, catálogos de productos, carritos de compras y, eventualmente, procesamiento de pagos. 

El sistema está diseñado pensando en la extensibilidad, preparando el terreno para un futuro panel de administración (Backoffice) y la integración de servicios de terceros para pagos y autenticación.

---

## 🛠️ 2. Stack Tecnológico Principal

El proyecto utiliza tecnologías modernas y eficientes para garantizar un alto rendimiento y una excelente experiencia de desarrollo:

### Backend & API
- **Lenguaje**: Python (>= 3.12) - Aprovechando tipado estático y nuevas características del lenguaje.
- **Framework Web**: FastAPI (>= 0.115.0) - Seleccionado por su alto rendimiento, validación automática de datos y generación nativa de documentación OpenAPI (Swagger/ReDoc).
- **Servidor ASGI**: Uvicorn (`uvicorn[standard]`) - Para servir la aplicación FastAPI de manera concurrente.

### Base de Datos & BaaS (Backend as a Service)
- **Proveedor**: Supabase - Actúa como nuestra base de datos relacional (PostgreSQL) y plataforma BaaS.
- **Cliente**: `supabase` (Cliente oficial de Python para interactuar con la API REST de Supabase).
- **Esquema Relacional**: Se utilizan scripts de migración SQL para definir tablas y políticas en Supabase.

### Seguridad y Autenticación
- **JWT (JSON Web Tokens)**: Uso de `python-jose[cryptography]` para la emisión y validación de tokens de sesión.
- **Hashing de Contraseñas**: `passlib[bcrypt]` y `bcrypt`. (Nota: Se implementó un fix específico para manejar el límite de 72 bytes de Bcrypt).
- **Validación de Datos**: `pydantic` y `pydantic-settings` para la validación estricta de payloads y variables de entorno.
- **Validación de Emails**: `email-validator` para formateo estricto de correos en el registro.

### Infraestructura y Herramientas de Desarrollo
- **Gestor de Paquetes**: `uv` - Gestor ultrarrápido escrito en Rust para manejar las dependencias en lugar de pip o poetry.
- **Contenerización**: Docker y Docker Compose para asegurar que los entornos de desarrollo local y de producción sean idénticos.
- **Testing**: `pytest` y `pytest-asyncio` para pruebas unitarias y de integración.
- **Peticiones HTTP Internas**: `httpx` (Cliente HTTP asíncrono para comunicarse entre servicios o con APIs externas).

---

## 📐 3. Convenciones de Código y Estado Actual

Es **ESTRICTAMENTE OBLIGATORIO** que todo nuevo código o refactorización respete las siguientes convenciones y patrones ya implementados en el proyecto:

### 3.1. Estructura de Respuesta de API (Estandarizada)
**TODOS** los endpoints deben retornar una estructura JSON uniforme. Esto facilita la integración con el frontend. La estructura obligatoria es:

```json
{
  "ok": true,          // Booleano: indica si la operación fue exitosa (true) o falló (false).
  "data": { ... },     // Objeto/Array: contiene los datos solicitados. Puede ser null o estar vacío si no aplica.
  "messages": "..."    // String: Un mensaje claro y descriptivo del resultado de la operación (ej. "Usuario creado con éxito", "No se encontró el producto").
}
```

### 3.2. Sistema de Logs y Trazabilidad
Se ha implementado un sistema robusto de logging para monitorear solicitudes y depurar errores eficientemente.
- **Uso de `logger`**: Se debe utilizar el logger configurado en la aplicación, **no** `print()`.
- **Niveles de Log**: 
  - Usar `logger.info` para flujos normales (ej. "Iniciando proceso de checkout").
  - Usar `logger.error` para atrapar excepciones específicas, incluyendo la **traza completa (trace)** del error para facilitar el debugging (especialmente fallas de conexión a Supabase, validaciones, etc.).

### 3.3. Gestión de Usuarios y Roles
La base de la autenticación ya soporta múltiples tipos de cuentas:
- **Roles actuales**: Se maneja el registro tanto para cuentas de cliente (`customer`) como para administradores (`admin`) u otros roles, preparando la lógica para un futuro panel Backoffice.
- Las variables de entorno (`.env`) están estrictamente ignoradas en `.gitignore` para no exponer secretos de JWT ni claves de API de Supabase.

---

## 🚀 4. Roadmap y Futuras Implementaciones

Las siguientes características son fundamentales para el ciclo de vida del proyecto. Al interactuar con el código, los agentes de IA deben prever que estos sistemas se acoplarán a la arquitectura actual.

### 4.1. Pasarela de Pagos (Stripe Integration)
- **Objetivo**: Permitir a los usuarios procesar pagos de forma segura sin que la aplicación almacene datos sensibles de tarjetas de crédito.
- **Funcionalidades a desarrollar**:
  - Integración del SDK o API REST de Stripe.
  - Creación de `PaymentIntents` y manejo de `Checkout Sessions`.
  - Construcción de un endpoint para manejar **Webhooks** de Stripe (eventos de éxito, fallo, fraude).
  - Almacenamiento del historial de transacciones (identificador de Stripe, montos, estado del pago) vinculadas a la tabla de `Pedidos/Orders` en Supabase.

### 4.2. Inicio de Sesión Social (OAuth / SSO)
- **Objetivo**: Reducir la fricción en el registro y mejorar la tasa de conversión en el e-commerce.
- **Proveedores**: 
  - Google (Google Sign-In)
  - Facebook Login
- **Implementación técnica**:
  - Se espera delegar la configuración principal a **Supabase Auth** para gestionar los proveedores de OAuth, o bien manejar el flujo de intercambio de tokens directamente desde FastAPI si los requisitos de negocio lo exigen.
  - El sistema deberá reconciliar correos electrónicos existentes con nuevas cuentas sociales (Account Linking).

### 4.3. Catálogo de Productos y Carrito
Aunque la base es sólida, el motor del e-commerce requerirá la expansión de la base de datos para manejar:
- **Gestión de Inventario**: Productos, Unidades en Stock (SKU), Categorías y Variantes (Tallas, Colores).
- **Listados Especiales**: Algoritmos/Consultas para extraer listas de "Más Vendidos" (Bestsellers) e implementación de un sistema de "Favoritos / Wishlist" por usuario.
- **Motor de Descuentos**: Lógica para manejar cupones de descuento o rebajas de precio por tiempo limitado.
- **Carrito de Compras**: Lógica efímera (cargada en Redis o manejada en base de datos) para rastrear el abandono del carrito antes de completar la orden.

---

## 🤖 5. Instrucciones Finales para AI Agents

1. **Contexto Antes de Código**: Siempre revisa la arquitectura en `app/` (controladores, modelos, utilidades) antes de sugerir refactorizaciones grandes.
2. **Consistencia en Respuestas**: Si creas un nuevo endpoint en un enrutador (router), asegúrate de que el valor de retorno encaje en la interfaz `{ok, data, messages}` mencionada en la sección 3.1.
3. **Manejo de Errores Limpio**: Cualquier excepción o error imprevisto debe ser capturado ("try-except") y debe retornar un estado HTTP adecuado (ej. 400, 404, 500) junto con la respuesta estandarizada donde `"ok": false` y `"messages"` explica el problema, todo acompañado de su respectivo `logger.error` con la traza.
