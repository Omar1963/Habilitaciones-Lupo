# walkthrough-Nro 20260327

Fecha de creacion: 2026-03-27
Tema: Modulo documental, checklist con aprobacion condicionada y biblioteca futura para IA

## Objetivo
Definir el recorrido funcional y tecnico antes de modificar el sistema documental de empresas y vigiladores.

## Estado actual
Hoy el sistema ya tiene:

- `DocumentoTramite` y `DocumentoRequisito` para manejar checklist por tramite.
- Un campo `archivo_url` en cada requisito, pero no una biblioteca documental formal.
- Estados documentales como `Faltante`, `Subido`, `Aprobado`.
- Flujo de tramites para empresa y persona.

Hoy no tiene, al menos de forma completa:

- carga real de archivos PDF,
- guardado estructurado por `id` de empresa o vigilador,
- bloqueo de aprobacion si no hay documento adjunto,
- visor read-only del PDF,
- biblioteca documental y normativa separada,
- ficha visual tipo `DNI = F / OK` al iniciar o consultar tramites.

## Objetivo funcional
Queremos que cada documento:

- quede asociado a un ente concreto: empresa o persona,
- se cargue digitalizado desde la app,
- solo pueda aprobarse si el archivo fue adjuntado,
- pueda abrirse en modo lectura,
- y ademas alimentar una biblioteca documental futura para un agente de IA.

## Criterio de ejecucion
Este walkthrough se desarrollara por etapas.

Regla de trabajo:
- primero se presenta la etapa propuesta,
- luego el equipo revisa alcance, riesgos y entregables,
- y recien despues de recibir `OK del equipo` se ejecuta esa etapa.

## Estado de avance
- Etapa 1: ejecutada el 2026-03-27
- Etapa 2: ejecutada el 2026-03-27
- Etapa 3: ejecutada el 2026-03-27
- Etapa 4: ejecutada el 2026-03-27
- Etapa 5: ejecutada el 2026-03-27
- Etapa 6: ejecutada el 2026-03-30
- Etapa 7: ejecutada el 2026-03-30
- Etapa 8: ejecutada el 2026-03-30

## Etapas propuestas

### Etapa 1 - Modelo documental y trazabilidad
Objetivo:
- definir la estructura de datos que permita guardar cada documento con el `id` correcto de empresa o vigilador.

Alcance:
- crear la base conceptual para `DocumentoAdjunto`,
- mantener `DocumentoRequisito` como checklist,
- definir trazabilidad por `empresa_id` o `vigilador_id`,
- asociar adjunto con `tramite_id` y `requisito_id`,
- definir metadatos minimos del archivo.

Campos minimos sugeridos:
- `empresa_id` o `vigilador_id`,
- `tramite_id`,
- `requisito_id`,
- `tipo_documento`,
- `nombre_original`,
- `nombre_archivo`,
- `mime_type`,
- `ruta_archivo`,
- `fecha_carga`,
- `usuario_carga`.

Entregables:
- definicion tecnica del modelo,
- decision final sobre tabla nueva o extension del modelo actual,
- lista de migraciones a crear.

Punto de control:
- `OK del equipo para ejecutar Etapa 1`

### Etapa 2 - Estructura fisica de almacenamiento
Objetivo:
- definir y preparar la estructura de carpetas donde se guardaran los PDF.

Alcance:
- almacenamiento segregado por entidad,
- nombres fisicos seguros y unicos,
- estrategia de lectura controlada,
- validaciones de formato y tamano.

Estructura propuesta:
- `storage/empresas/{empresa_id}/`
- `storage/vigiladores/{vigilador_id}/`
- `storage/biblioteca/normas/`
- `storage/biblioteca/documentos/`

Reglas base:
- solo PDF en esta primera etapa,
- nombre saneado,
- bloqueo de extensiones no permitidas,
- apertura via endpoint controlado, no via ruta fisica libre.

Entregables:
- estructura de carpetas del proyecto,
- criterio de nombres de archivo,
- politica inicial de validacion.

Punto de control:
- `OK del equipo para ejecutar Etapa 2`

### Etapa 3 - Carga documental por entidad y por checklist
Objetivo:
- permitir adjuntar documentacion tanto a empresa como a vigilador, y tambien desde cada requisito del checklist.

Alcance:
- boton `Agregar documentacion` para empresa,
- boton `Agregar documentacion` para vigilador,
- carga documental desde la vista del requisito,
- asociacion automatica al ente correspondiente.

Entregables:
- flujo de carga definido para empresa,
- flujo de carga definido para vigilador,
- flujo de carga definido para requisito.

Punto de control:
- `OK del equipo para ejecutar Etapa 3`

### Etapa 4 - Aprobacion condicionada por adjunto
Objetivo:
- impedir que un requisito quede en `Aprobado` si no tiene documento adjunto valido.

Alcance:
- popup aclaratorio en frontend,
- bloqueo de aprobacion en backend,
- posibilidad de abrir modal de carga al intentar aprobar,
- mensajes claros para el usuario.

Regla principal:
- sin adjunto no se puede aprobar.

Entregables:
- validacion funcional en frontend,
- validacion obligatoria en backend,
- mensaje de error o popup normalizado.

Punto de control:
- `OK del equipo para ejecutar Etapa 4`

### Etapa 5 - Vista resumida de requisitos por tramite
Objetivo:
- mostrar al iniciar o abrir un tramite el nombre de la empresa o persona y el estado corto de cada documento.

Alcance:
- resumen tipo `DNI = F`,
- resumen tipo `DNI = OK`,
- mismo criterio para empresa y para persona,
- codificacion visual simple y rapida.

Convencion sugerida:
- `F` en rojo = faltante,
- `S` en ambar = subido pendiente de validar,
- `OK` en verde = aprobado.

Entregables:
- ficha visual de tramite de persona,
- ficha visual de tramite de empresa,
- criterio uniforme de colores y estados.

Punto de control:
- `OK del equipo para ejecutar Etapa 5`

### Etapa 6 - Apertura read-only de PDF
Estado:
- ejecutada el 2026-03-30

Objetivo:
- permitir abrir cada documento adjunto desde la aplicacion en modo solo lectura.

Alcance:
- click sobre el documento,
- apertura en nueva pestaña o visor,
- control de acceso,
- sin edicion desde la app.

Entregables:
- endpoint de visualizacion,
- vinculacion UI-documento,
- lectura controlada del PDF.

Punto de control:
- `OK del equipo para ejecutar Etapa 6`

### Etapa 7 - Biblioteca documental y normativa
Estado:
- ejecutada el 2026-03-30

Objetivo:
- crear una biblioteca separada del checklist operativo para almacenar normas y documentos generales.

Alcance:
- modulo `Normativa`,
- modulo `Biblioteca documental`,
- categorias y tags,
- relacion opcional con empresa, persona o jurisdiccion.

Metadata sugerida:
- titulo,
- categoria,
- jurisdiccion,
- organismo,
- tema,
- fecha,
- vigencia,
- observaciones.

Entregables:
- modelo base de biblioteca,
- estructura de almacenamiento,
- criterio de clasificacion documental.

Punto de control:
- `OK del equipo para ejecutar Etapa 7`

### Etapa 8 - Preparacion para futuro agente de IA
Estado:
- ejecutada el 2026-03-30

Objetivo:
- dejar la biblioteca y los adjuntos listos para futura explotacion por un agente de IA.

Alcance:
- metadata compatible con recuperacion posterior,
- campo para OCR o texto extraido futuro,
- etiquetas tematicas,
- estado de vigencia,
- referencias cruzadas por entidad y jurisdiccion.

Entregables:
- especificacion de metadata extendida,
- criterio de indexacion futura,
- separacion clara entre legajo operativo y biblioteca de conocimiento.

Punto de control:
- `OK del equipo para ejecutar Etapa 8`

## Decisiones sugeridas
- Crear tabla nueva `DocumentoAdjunto`.
- Mantener `DocumentoRequisito` como checklist y no como archivo.
- Guardar PDFs por carpetas separadas de empresa y vigilador.
- Aprobar solo si existe adjunto.
- Abrir documentos mediante endpoint controlado, no por path directo del disco.
- Crear biblioteca documental como modulo separado del tramite operativo.

## Riesgos a contemplar
- Si todo queda solo en `archivo_url`, luego se complica la biblioteca y la IA.
- Si no se valida en backend, alguien podria aprobar sin adjuntar.
- Si no se separa biblioteca de legajo operativo, se mezclan usos distintos.
- Si el archivo se guarda solo por nombre y no por ID, se pierde trazabilidad.

## Secuencia recomendada
1. Etapa 1
2. Etapa 2
3. Etapa 3
4. Etapa 4
5. Etapa 5
6. Etapa 6
7. Etapa 7
8. Etapa 8

## Proxima accion sugerida
Presentar primero la `Etapa 1 - Modelo documental y trazabilidad` al equipo de trabajo.

Frase de aprobacion sugerida:
- `OK del equipo para ejecutar Etapa 1`
