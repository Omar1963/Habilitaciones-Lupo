# walkthrough-Nro 20260326

Fecha de creacion: 2026-03-26
Origen importado: `C:\Users\Admin\.gemini\antigravity\brain\5acd1443-d3e2-4019-b440-9e0b72fc1240\walkthrough.md`
Tema: Resultados de pruebas de acceso, roles y hallazgos de seguridad

## Contenido importado
Este walkthrough registra verificaciones funcionales sobre autenticacion y permisos:

- login exitoso para `admin`,
- login exitoso para `Jose`,
- acceso permitido de `admin` al endpoint restringido `/users/`,
- acceso denegado de `Jose` al mismo endpoint,
- y revision del frontend en modo solo lectura para usuario consultor.

## Hallazgo clave
El registro detecta una vulnerabilidad importante:

- aunque el frontend ocultaba acciones de escritura para usuarios no administradores,
- varios endpoints de backend no tenian proteccion suficiente,
- por lo que era posible ejecutar operaciones directas contra la API.

## Valor historico
Este documento es relevante porque deja trazada la diferencia entre restriccion visual en frontend y seguridad real en backend, y justifica futuras mejoras de autorizacion.
