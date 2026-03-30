# Sistema de Gestion - Gestiones Lupo

Este proyecto es una aplicacion de gestion basada en el flujo de datos de una consultora que tramita habilitaciones de empresas de seguridad y del personal asignado a ellas.

## Tecnologias Principales
- Python (backend / API).
- Power Platform (frontend, integracion y automatizacion).
- DAX y Power BI (analisis de datos y reportes).

## Flujo Documental
El sistema administra dos circuitos documentales conectados:

1. La habilitacion de la empresa en cada jurisdiccion o tipo de tramite.
2. La habilitacion del personal de esa empresa, segun su rol y la misma jurisdiccion.

### 1. Catalogos maestros
Antes de operar, el sistema necesita definir:

- `roles`: perfiles operativos como Vigilador, Operador o Tecnico.
- `tipos_tramites`: jurisdicciones o entes como PBA, CABA, ANMAC, etc.
- `requisitos_plantilla`: listado base de documentos exigidos para cada combinacion de rol y tipo de tramite.

Estas plantillas son la fuente del checklist documental. Cuando se inicia un tramite, el backend genera automaticamente los requisitos concretos a partir de ellas.

### 2. Alta de entidades operativas
El flujo parte de dos entidades centrales:

- `Empresa`: sujeto juridico que debe obtener su habilitacion propia.
- `Vigilador`: persona que luego puede ser vinculada a una o mas empresas.

Cada empresa guarda datos administrativos, jurisdicciones y vigencias. Cada vigilador conserva identidad, legajo, contacto y vencimiento de habilitacion personal.

### 3. Vinculacion empresa-personal
Una vez creadas ambas entidades, se genera una `Asignacion` entre empresa y vigilador. Esa asignacion representa la relacion operativa vigente entre ambas partes.

Sobre esa asignacion se agregan uno o varios roles mediante `AsignacionRol`. Esta capa permite que una misma persona tenga distintos requisitos segun la funcion que cumple dentro de una empresa.

### 4. Apertura del tramite documental
La entidad principal del circuito es `DocumentoTramite`, que puede existir en dos contextos:

- Tramite de empresa: asociado a `empresa_id`.
- Tramite de personal: asociado a `asignacion_rol_id`.

Reglas de negocio vigentes:

- No se duplica un tramite activo con el mismo contexto y tipo.
- Si se intenta iniciar un tramite de personal, la empresa debe tener iniciado primero su tramite para esa misma jurisdiccion.

Esto respeta la secuencia real del negocio: primero se habilita la empresa y luego se habilita al personal que depende de ella.

### 5. Generacion del checklist documental
Al crear un tramite, el backend genera automaticamente los `documento_requisitos` asociados:

- Si el tramite es de empresa, usa plantillas con `es_para_empresa = True`.
- Si el tramite es de personal, usa plantillas del rol asignado y del tipo de tramite correspondiente.

Cada requisito nace con estado `Faltante` y luego puede pasar a:

- `Subido`: el documento fue cargado o informado.
- `Aprobado`: el documento fue validado.

Adicionalmente, cada requisito puede registrar:

- `archivo_url`: referencia al archivo digital o repositorio documental.
- `fecha_vencimiento`: fecha de expiracion del documento, si aplica.

### 6. Seguimiento operativo
El control diario se apoya en tres niveles:

- Estado del `documento_tramite`: permite saber si el expediente sigue pendiente o completo.
- Estado de cada `documento_requisito`: permite identificar faltantes concretos.
- Estado de vigencia de empresa o vigilador: permite detectar habilitaciones vigentes, vencidas o proximas a vencer.

Este diseno permite que el frontend muestre tableros de avance, alertas y pendientes sin reconstruir manualmente las reglas en cada pantalla.

### 7. Informe consolidado
El endpoint de informe por empresa concentra la vista operativa:

- datos base de la empresa,
- personal asignado y estado de habilitacion de cada vigilador,
- roles que cumple cada persona,
- tramites iniciados por jurisdiccion,
- cantidad de requisitos aprobados y pendientes.

La intencion es que una sola consulta permita responder:

- que jurisdicciones estan cubiertas,
- que documentacion falta,
- que personal esta habilitado,
- y donde existen riesgos por vencimiento o por falta de inicio de tramite.

## Flujo de Datos que guia el desarrollo
La secuencia funcional objetivo del sistema es:

1. Configurar catalogos maestros (`roles`, `tipos_tramites`, `requisitos_plantilla`).
2. Dar de alta `empresas`.
3. Dar de alta `vigiladores`.
4. Crear `asignaciones` entre empresa y vigilador.
5. Asociar `roles` a cada asignacion.
6. Iniciar `tramites` de empresa por jurisdiccion.
7. Iniciar `tramites` de personal por rol y jurisdiccion.
8. Generar y actualizar `requisitos` documentales.
9. Consultar informes, vencimientos y pendientes.

## Modelo conceptual resumido
- `Empresa` 1:N `Asignacion`
- `Vigilador` 1:N `Asignacion`
- `Asignacion` 1:N `AsignacionRol`
- `AsignacionRol` 1:N `DocumentoTramite`
- `Empresa` 1:N `DocumentoTramite` propios
- `TipoTramite` 1:N `DocumentoTramite`
- `DocumentoTramite` 1:N `DocumentoRequisito`
- `RequisitoPlantilla` 1:N `DocumentoRequisito`

## Criterio para las siguientes etapas
Este flujo define la prioridad del desarrollo:

- primero consolidar integridad del modelo y reglas de negocio,
- luego facilitar la carga documental y el seguimiento operativo,
- y finalmente exponer datos listos para automatizacion, reportes y dashboards en Power Platform y Power BI.
