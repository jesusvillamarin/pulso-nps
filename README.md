# Pulso

Pulso es una plataforma open source para importar encuestas NPS desde CSV o XLSX, clasificarlas por área, categoría y tono, revisar resultados y exportarlos nuevamente.

El repositorio es autocontenido y no depende de cuentas pertenecientes a sus mantenedores. Cada instalación utiliza sus propias credenciales de TypeSafe o puede funcionar en modo simulado.

## Funcionalidades

- Importación de CSV y XLSX de hasta 25 MB o 10.000 filas.
- Selección de hoja, fila de encabezados y columnas de puntaje y comentario.
- Vista previa de los primeros 20 registros.
- Taxonomía editable de áreas y categorías.
- Clasificación jerárquica con TypeSafe: área, categoría y tono.
- Cálculo de promotores, pasivos, detractores y NPS.
- Progreso del análisis, filtros, revisión manual y conservación de la predicción original.
- Exportación de resultados en CSV y XLSX.
- Modo simulado para desarrollo y evaluación sin credenciales externas.

## Inicio rápido sin credenciales

Requiere Docker con Docker Compose.

```bash
TYPESAFE_MOCK=1 docker compose up --build
```

Abre [http://localhost:3000](http://localhost:3000) y selecciona **Usar archivo de ejemplo**. La documentación interactiva de la API queda en [http://localhost:8000/docs](http://localhost:8000/docs).

Detén los servicios con:

```bash
docker compose down
```

## Usar TypeSafe real

Cada instalación debe proporcionar su propia clave. El navegador nunca recibe esta credencial.

```bash
cp .env.example .env
```

Completa `TYPESAFE_API_KEY` en `.env` y ejecuta:

```bash
docker compose up --build
```

No publiques el archivo `.env`. Está excluido del repositorio mediante `.gitignore`.

## Configuración

| Variable | Valor predeterminado | Descripción |
|---|---|---|
| `TYPESAFE_API_KEY` | vacío | Credencial propia de TypeSafe. |
| `TYPESAFE_MOCK` | `0` | Usa clasificación local determinista cuando vale `1`. |
| `TYPESAFE_BATCH_SIZE` | `10` | Comentarios enviados en cada lote. |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | URL pública de la API utilizada por el navegador. |
| `CORS_ORIGINS` | URLs locales | Orígenes autorizados, separados por comas. |

## Arquitectura

- `frontend/`: Next.js, TypeScript, Tailwind CSS y HeroUI.
- `backend/`: FastAPI, SDK de TypeSafe, pandas y openpyxl.
- `compose.yaml`: ejecución local de ambos servicios.
- SQLite y un volumen Docker: persistencia del prototipo.

Esta arquitectura está orientada a validación y despliegues pequeños. No garantiza recuperación de trabajos activos tras reinicios ni procesamiento distribuido.

## Desarrollo sin Docker

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
TYPESAFE_MOCK=1 uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Pruebas

```bash
cd backend && pytest
cd ../frontend && npm run lint && npm run typecheck && npm run build
```

Consulta [CONTRIBUTING.md](CONTRIBUTING.md) antes de proponer cambios.

## Seguridad y privacidad

Los archivos pueden contener información sensible. En el prototipo se almacenan en un volumen local y los comentarios se envían a TypeSafe cuando el modo simulado está desactivado. Antes de un despliegue público, configura controles de acceso, límites de carga, políticas de retención y credenciales independientes.

Nunca abras un issue adjuntando claves, bases de datos o archivos reales de clientes.

## Licencia

Pulso se distribuye bajo la [licencia MIT](LICENSE).
