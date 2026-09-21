DEFAULT_TAXONOMY = [
    {
        "name": "Producto",
        "description": "Calidad, funcionalidad y experiencia con el producto.",
        "categories": [
            {"name": "Usabilidad", "description": "Facilidad de uso, navegación o aprendizaje."},
            {"name": "Funcionalidad", "description": "Funciones disponibles o comportamiento esperado."},
            {"name": "Errores", "description": "Fallos, bloqueos o comportamiento incorrecto."},
            {"name": "Integraciones", "description": "Conexiones con herramientas o servicios externos."},
        ],
    },
    {
        "name": "Atención",
        "description": "Interacciones con soporte o servicio al cliente.",
        "categories": [
            {"name": "Trato", "description": "Amabilidad, empatía o actitud del personal."},
            {"name": "Resolución", "description": "Calidad de la solución ofrecida."},
            {"name": "Tiempo de respuesta", "description": "Espera o rapidez de atención."},
        ],
    },
    {
        "name": "Facturación",
        "description": "Precios, cargos, facturas, planes y reembolsos.",
        "categories": [
            {"name": "Cobros", "description": "Cargos correctos, duplicados o inesperados."},
            {"name": "Reembolsos", "description": "Devoluciones de dinero o cancelaciones."},
            {"name": "Planes y precios", "description": "Precio, valor o cambios de plan."},
        ],
    },
    {
        "name": "Operaciones",
        "description": "Entrega, disponibilidad y ejecución del servicio.",
        "categories": [
            {"name": "Entrega", "description": "Envío, recepción o puntualidad."},
            {"name": "Disponibilidad", "description": "Stock, horarios o acceso al servicio."},
            {"name": "Proceso", "description": "Pasos operativos generales."},
        ],
    },
    {
        "name": "Otros",
        "description": "Comentarios que no corresponden claramente a otra área.",
        "categories": [{"name": "General", "description": "Comentario general o sin tema suficiente."}],
    },
]

TONE_CRITERIA = {
    "Positivo": "Satisfacción o aprobación clara, sin entusiasmo intenso.",
    "Feliz": "Alegría, entusiasmo, gratitud o recomendación explícita.",
    "Neutral": "Descripción factual sin emoción dominante.",
    "Confundido": "Incertidumbre, duda o dificultad para comprender algo.",
    "Decepcionado": "Expectativas incumplidas, desilusión o pesar.",
    "Frustrado": "Impotencia, impaciencia o molestia por una dificultad persistente.",
    "Agresivo": "Hostilidad, insultos, amenazas o lenguaje confrontacional.",
}
