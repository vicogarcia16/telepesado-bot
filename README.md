# 🎬 TelePesado Bot

Bot de Telegram que recomienda películas y series, y conversa de forma natural usando FastAPI y un modelo LLM vía OpenRouter. Enriquece las recomendaciones con tráilers de YouTube y pósters oficiales obtenidos a través de la API de TMDb. Utiliza una base de datos en Neon para guardar el contexto del usuario y tiene un endpoint `/ping` para monitoreo del servicio con herramientas como UptimeRobot.

## 🚀 Características

- **Webhook de Telegram**: Recibe y responde mensajes automáticamente.
- **Conversación Natural**: Interpreta preguntas del usuario y responde de manera fluida.
- **Recomendaciones Enriquecidas**: Sugiere películas y series con tráiler, póster, dónde verla y reparto.
- **IA con Respaldo**: Usa un LLM de OpenRouter y tiene un modelo de respaldo para garantizar la disponibilidad.
- **Base de Datos Persistente**: Almacena el historial de chat en PostgreSQL (Neon) para dar contexto a la IA.
- **Monitoreo**: Endpoint `/ping` para verificar el estado del servicio.
- **Manejo de Errores Robusto**: Sistema de recuperación que envía respuestas en texto plano si falla el formato HTML y gestiona errores de API (404/429) automáticamente.
- **Formato Enriquecido**: Utiliza HTML para dar formato a los mensajes en Telegram.

## 🛠️ Arquitectura

El bot funciona como una aplicación FastAPI desplegada en Render. Telegram envía actualizaciones a un webhook, la aplicación procesa el mensaje, interactúa con las APIs externas (OpenRouter, TMDb) y la base de datos, y finalmente devuelve una respuesta al usuario.

```mermaid
graph TD
    subgraph "Usuario"
        A[Usuario en Telegram]
    end

    subgraph "Infraestructura"
        B(FastAPI en Render)
    end

    subgraph "APIs Externas"
        C[API de Telegram]
        D[OpenRouter LLM]
        E[API de TMDb]
    end

    subgraph "Base de Datos"
        F[PostgreSQL en Neon]
    end

    A -- 1. Envía mensaje --> C
    C -- 2. Webhook --> B
    B -- 3. Valida y limpia --> B
    B -- 4. Pide historial --> F
    F -- 5. Devuelve historial --> B
    B -- 6. Envía prompt con contexto --> D
    D -- 7. Devuelve respuesta --> B
    B -- 8. Extrae títulos y busca en TMDb --> E
    E -- 9. Devuelve datos (póster, tráiler, etc.) --> B
    B -- 10. Guarda en historial --> F
    B -- 11. Envía respuesta enriquecida --> C
    C -- 12. Muestra en chat --> A
```

## 📁 Estructura del Proyecto

La estructura está organizada por módulos para separar responsabilidades, facilitando el mantenimiento y la escalabilidad.

```
app/
├── main.py           # App principal de FastAPI, webhook y endpoint /ping
├── bot/
│   └── telegram.py   # Lógica para interactuar con la API de Telegram
├── core/
│   ├── config.py     # Carga y gestión de variables de entorno
│   ├── exceptions.py # Excepciones personalizadas
│   └── utils.py      # Funciones auxiliares (validación, limpieza de texto)
├── data/
│   └── prompt.py     # Plantillas de prompts para el LLM
├── db/
│   ├── chat_history.py # Operaciones CRUD para el historial de chat
│   └── database.py     # Configuración de la sesión de base de datos
├── models/
│   └── chat_history.py # Modelo de datos SQLAlchemy para la tabla de historial
├── routes/
│   └── telegram.py     # Rutas de la API (webhook, historial)
├── schemas/
│   └── chat_history.py # Esquemas Pydantic para validación de datos
└── services/
    ├── llm_agent.py    # Orquesta la llamada al LLM y el formato de la respuesta
    └── tmdb_service.py # Lógica para interactuar con la API de TMDb
```

## 🔐 Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto. Puedes tener diferentes archivos (`.env.dev`, `.env.prod`) y renombrarlos a `.env` según el entorno en el que quieras trabajar.

El archivo `.env` debe contener las siguientes variables:

```env
# Token del bot de Telegram
TELEGRAM_TOKEN="tu_token_de_telegram"

# Clave de API de OpenRouter
OPENROUTER_API_KEY="tu_clave_de_openrouter"

# Modelo principal y de respaldo de OpenRouter
OPENROUTER_MODEL="google/gemini-pro-1.5"
OPENROUTER_FALLBACK_MODEL="anthropic/claude-3-haiku"

# Clave de API de The Movie Database (TMDb)
TMDB_API_KEY="tu_clave_de_tmdb"

# URL base de la API de Telegram
TELEGRAM_API_URL="https://api.telegram.org/bot"

# URL de despliegue (ej. la URL de Render)
BASE_URL="https://tu_app.onrender.com"

# URL de conexión a la base de datos PostgreSQL (Neon)
DATABASE_URL="postgresql+asyncpg://user:password@host:port/dbname"

# Versión de la API (utilizada en main.py)
API_VERSION="1"
```

## 🧪 Instalación y Ejecución Local

1.  **Instalar dependencias**:
    ```bash
    pipenv install --dev
    ```

2.  **Ejecutar el servidor**:
    ```bash
    pipenv run uvicorn app.main:app --reload
    ```

## ☁️ Despliegue

El proyecto está preparado para desplegarse en **Render**. El `Procfile` contiene el comando `gunicorn` necesario para producción. Render instalará las dependencias automáticamente desde `requirements.txt` y ejecutará la aplicación.

## 📜 Licencia

MIT © [vicogarcia16](https://github.com/vicogarcia16)
