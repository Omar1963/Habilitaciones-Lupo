# walkthrough-Nro 20260317

Fecha de creacion: 2026-03-17
Origen importado: `C:\Users\Admin\.gemini\antigravity\brain\bde87caa-41e8-45f0-991d-c4396bda8cee\walkthrough.md`
Tema: Flujo base del sistema y modelo relacional inicial

## Contenido importado
Este walkthrough documenta el flujo principal de carga de personal y tramites, y fija la base conceptual del sistema:

- Seleccionar empresa.
- Ingresar DNI.
- Crear o reutilizar vigilador.
- Crear o reutilizar asignacion vigilador-empresa.
- Gestionar roles sobre la asignacion.
- Crear o reutilizar tramite por rol y tipo.
- Generar checklist documental desde plantilla.
- Completar requisitos y cerrar el circuito operativo.

## Modelo conceptual definido en ese registro
- `Empresa`
- `Vigilador`
- `Asignacion`
- `Rol`
- `AsignacionRol`
- `TipoTramite`
- `DocumentoTramite`
- `RequisitoPlantilla`
- `DocumentoRequisito`

## Valor historico
Este registro es la base del diseno relacional del proyecto y explica el flujo operativo sobre el que despues se construyeron las mejoras de interfaz, seguridad y documentacion.
