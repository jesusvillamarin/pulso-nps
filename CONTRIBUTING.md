# Contribuir a Pulso

Gracias por mejorar Pulso. El proyecto busca mantener una instalación local sencilla, contratos claros y ausencia de dependencias con cuentas de sus mantenedores.

## Preparar el entorno

La forma más rápida de trabajar es con Docker:

```bash
TYPESAFE_MOCK=1 docker compose up --build
```

La aplicación queda disponible en `http://localhost:3000` y la documentación de la API en `http://localhost:8000/docs`.

## Antes de enviar un cambio

Ejecuta las verificaciones del backend:

```bash
cd backend
pytest
```

Y las del frontend:

```bash
cd frontend
npm run lint
npm run typecheck
npm run build
```

No incluyas archivos `.env`, claves de API, archivos NPS reales, bases de datos ni exportaciones generadas. Los cambios deben conservar el modo simulado para que cualquier persona pueda evaluar el proyecto sin consumir servicios externos.

## Alcance de las contribuciones

- Abre un issue antes de introducir una dependencia de infraestructura obligatoria.
- Mantén la interfaz en español y el procesamiento compatible con comentarios multilingües.
- Añade pruebas para cambios en importación, clasificación, cálculo NPS o exportación.
- Documenta cualquier variable de entorno nueva en `.env.example`.
