import streamlit as st
import pandas as pd
import csv
import io
import sqlite3 # Para el ejemplo de base de datos

# --- Plantilla del Prompt Profesional (Modificada para usar f-strings de Python) ---
PROMPT_TEMPLATE = """
**Rol:** Actúa como un experto investigador y analista tecnológico con acceso a una vasta base de conocimientos técnicos, científicos y de mercado. Tu objetivo es realizar una investigación exhaustiva sobre el tema especificado y presentar los hallazgos de manera estructurada y precisa.

**Tarea Principal:** Realizar una investigación profunda sobre **`{tema_principal}`**. Identificar y detallar diversas tecnologías o servicios relevantes.

**Objetivo Específico de la Investigación:**
El objetivo es identificar, describir y categorizar tecnologías y servicios que aborden el problema de **`{problema_especifico}`**. La investigación debe enfocarse en soluciones que sean **`{criterios_clave}`**{aplicabilidad_contexto}.

**Alcance de la Investigación:**
La investigación debe cubrir, como mínimo, los siguientes tipos de tecnologías/servicios:
{alcance_dinamico}

**Formato de Entrega Obligatorio:**
La información para CADA tecnología o servicio identificado debe ser presentada en **formato CSV de texto plano**, utilizando comillas dobles para encerrar cada campo y una coma como delimitador. La estructura de las columnas debe ser exactamente la siguiente:

`"nombre","tipo","caracteristicas","detalles","imagen","web_link","categoria","descripcion"`

**Definición de las Columnas para el CSV:**

* **`nombre`**: Nombre común o comercial de la tecnología/servicio (Ej: "Geomembranas Poliméricas (HDPE, LLDPE)").
* **`tipo`**: Subcategoría o tipo específico de la tecnología/servicio, según el alcance definido arriba (Ej: "Sistemas Avanzados de Impermeabilización", "Métodos de Tratamiento In-Situ", "Muestreo y Análisis Avanzado de Aguas Subterráneas"). Este campo debe reflejar la clasificación más granular de la tecnología dentro del alcance de la investigación.
* **`caracteristicas`**: Descripción concisa de las principales características técnicas, principios de funcionamiento, ventajas clave y limitaciones. Incluir datos cuantitativos si es posible (Ej: rangos de eficiencia, materiales, permeabilidad, vida útil). Citar fuentes o referencias si es relevante usando un formato simple como `[Número]`.
* **`detalles`**: Información más elaborada sobre la aplicabilidad, consideraciones de diseño, casos de uso, ejemplos de productos comerciales o proveedores líderes (si aplica), sinergias con otras tecnologías, y aspectos relevantes no cubiertos en 'caracteristicas'. Profundizar en aspectos prácticos y consideraciones de implementación. Citar fuentes o referencias si es relevante usando un formato simple como `[Número]`.
* **`imagen`**: Descripción breve del tipo de imagen que sería representativa de la tecnología o servicio (Ej: "Rollos de geomembrana HDPE y sección de TSF con revestimiento.", "Diagrama de PRB (zanja continua o funnel-and-gate)."). (Nota: La IA no generará la imagen en sí, solo la descripción).
* **`web_link`**: Lista de 3 a 5 URLs relevantes de fabricantes, instituciones de investigación, artículos técnicos o guías de referencia que proporcionen información detallada sobre la tecnología. Formato: `[dominio1.com](https://www.dominio1.com), [dominio2.org](https://www.dominio2.org)`
* **`categoria`**: Categoría general a la que pertenece la tecnología dentro del problema abordado (Ej: "Prevención y Control en la Fuente", "Contención e Intercepción", "Remediación In-Situ", "Monitoreo Ambiental"). Este campo debe reflejar la clasificación más amplia de la tecnología.
* **`descripcion`**: Resumen breve (1-2 frases) del propósito fundamental de la tecnología o servicio en el contexto del problema.

**Requisitos Adicionales:**

* **Profundidad:** La investigación debe ser exhaustiva, buscando información técnica detallada, estudios de caso, comparativas (si existen), y desarrollos recientes.
* **Precisión:** Toda la información debe ser precisa y basada en fuentes confiables. Si es posible, priorizar fuentes académicas, gubernamentales, de asociaciones industriales reconocidas y de fabricantes líderes.
* **Actualidad:** Priorizar información de los últimos 5-10 años, a menos que se trate de tecnologías fundamentales bien establecidas.
* **Neutralidad:** Presentar la información de manera objetiva, destacando tanto ventajas como limitaciones.
* **Claridad:** El lenguaje debe ser técnico pero comprensible.
* **Formato CSV Estricto:** Es crucial que el resultado final sea un bloque de texto plano que pueda ser copiado y pegado directamente para crear un archivo .csv válido. Asegúrate de que cada registro (tecnología) esté en una nueva línea y que los campos estén correctamente entrecomillados y separados por comas. **No incluir encabezados de columna en la salida CSV, solo los datos.**

**Ejemplo de una línea de salida esperada (solo como referencia de formato, el contenido variará):**

`"Geomembranas Poliméricas (HDPE, LLDPE)","Sistemas Avanzados de Impermeabilización","Revestimientos sintéticos de muy baja permeabilidad (ej. <1x10^-12 cm/s), alta resistencia química a lixiviados de relaves (pH 1-13), resistencia UV mejorada con negro de humo (mín. 2%), durabilidad proyectada >50 años. Espesores comunes: 1.5 mm, 2.0 mm, 2.5 mm. Texturizadas para ángulos de fricción >30° en taludes. Cumplen estándares GRI-GM13. [1, 2]","La selección se basa en pruebas de compatibilidad química (EPA 9090), análisis de esfuerzos y deformaciones. La instalación por termofusión requiere personal certificado y QA/QC riguroso (pruebas no destructivas y destructivas de soldaduras). Considerar punzonamiento, expansión/contracción térmica. Marcas líderes: Solmax, Agru, Atarfil. Su uso en sistemas compuestos con GCLs es la mejor práctica para TSFs de alto riesgo. [3, 4, 5]","Rollos de geomembrana HDPE instalándose en un TSF y diagrama de un sistema de revestimiento compuesto.","[solmax.com](https://www.solmax.com), [geosyntheticsinstitute.org](https://www.geosyntheticsinstitute.org), [ineris.fr/sites/default/files/prevrisk/pdf/liner_durability.pdf](https://www.ineris.fr/sites/default/files/prevrisk/pdf/liner_durability.pdf)","Prevención y Control en la Fuente","Barreras poliméricas de baja permeabilidad diseñadas para prevenir la migración de contaminantes desde depósitos de relaves hacia el subsuelo."`
Agrega en el plan de investigación que el formato de salida debe ser un csv plano.
**Comenzar Investigación.**
"""

# --- Columnas esperadas del CSV (y para la base de datos) ---
CSV_EXPECTED_COLUMNS = ["nombre", "tipo", "caracteristicas", "detalles", "imagen", "web_link", "categoria", "descripcion"]

# --- Aplicación Streamlit ---
st.set_page_config(layout="wide", page_title="Generador de Prompts y Cargador de Datos")

st.title("🤖🔬📑 Generador de Prompts y Cargador de Datos")
st.markdown("**Paso 1-3:** Genera un prompt detallado. **Paso 4:** Procesa la respuesta CSV de la IA y (opcionalmente) cárgala a una BD.")
st.markdown("---")

# --- Inicialización del estado de sesión ---
if 'alcance_items' not in st.session_state:
    st.session_state.alcance_items = [{"tipo_principal": "", "subtipos": [""]}]
if 'prompt_generated_success' not in st.session_state:
    st.session_state.prompt_generated_success = False
if 'parsed_dataframe' not in st.session_state:
    st.session_state.parsed_dataframe = None
if 'csv_input_text_value' not in st.session_state: # Para mantener el texto del área de CSV
    st.session_state.csv_input_text_value = ""


# --- Columnas para la entrada de datos ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Información General de la Investigación")
    tema_principal = st.text_input(
        "Tema Principal de la Investigación:",
        placeholder="Ej: Tecnologías para la solución de infiltraciones de relaves en napas subterráneas"
    )
    problema_especifico = st.text_input(
        "Problema Específico que se Busca Resolver:",
        placeholder="Ej: La contaminación de aguas subterráneas por infiltración de relaves mineros"
    )
    criterios_clave = st.text_area(
        "Criterios Clave de las Soluciones Deseadas:",
        placeholder="Ej: Innovadoras, costo-efectivas, probadas en campo, sostenibles, baja huella de carbono, etc."
    )
    industria_region = st.text_input(
        "Industria/Región Específica (Opcional):",
        placeholder="Ej: Minería de cobre en Chile, Agricultura en zonas áridas"
    )

with col2:
    st.subheader("2. Alcance Detallado de la Investigación")
    st.markdown("Define los Tipos y Subtipos de tecnologías/servicios a investigar. Estos se usarán para la columna 'tipo' en el CSV.")

    def add_tipo_principal():
        st.session_state.alcance_items.append({"tipo_principal": "", "subtipos": [""]})
        st.session_state.prompt_generated_success = False # Resetear si se modifica el alcance
        st.session_state.parsed_dataframe = None

    def add_subtipo(index_principal):
        st.session_state.alcance_items[index_principal]["subtipos"].append("")
        st.session_state.prompt_generated_success = False
        st.session_state.parsed_dataframe = None

    def remove_tipo_principal(index_principal):
        if len(st.session_state.alcance_items) > 1:
            st.session_state.alcance_items.pop(index_principal)
            st.session_state.prompt_generated_success = False
            st.session_state.parsed_dataframe = None

    def remove_subtipo(index_principal, index_subtipo):
         if len(st.session_state.alcance_items[index_principal]["subtipos"]) > 1:
            st.session_state.alcance_items[index_principal]["subtipos"].pop(index_subtipo)
            st.session_state.prompt_generated_success = False
            st.session_state.parsed_dataframe = None


    for i, item_principal in enumerate(st.session_state.alcance_items):
        expander_title = item_principal['tipo_principal'].strip() if item_principal['tipo_principal'].strip() else "(Vacío)"
        with st.expander(f"Tipo Principal de Tecnología/Servicio {i+1}: {expander_title}", expanded=True):
            col_tipo, col_btn_remove_tipo = st.columns([0.85, 0.15])
            with col_tipo:
                item_principal["tipo_principal"] = st.text_input(
                    f"Nombre del Tipo Principal {i+1}",
                    value=item_principal["tipo_principal"],
                    placeholder=f"Ej: Prevención y Control en la Fuente",
                    key=f"tipo_principal_{i}"
                )
            with col_btn_remove_tipo:
                if len(st.session_state.alcance_items) > 1 :
                    st.button("🗑️ Tipo", key=f"remove_tipo_principal_{i}", on_click=remove_tipo_principal, args=(i,), help="Eliminar este Tipo Principal", use_container_width=True)
                else:
                    st.markdown("") # Placeholder to keep layout consistent


            st.markdown("Subtipos (para la columna 'tipo' del CSV):")
            for j, subtipo_val in enumerate(item_principal["subtipos"]):
                col_sub, col_btn_remove_sub = st.columns([0.85, 0.15])
                with col_sub:
                    item_principal["subtipos"][j] = st.text_input(
                        f"Subtipo {j+1}",
                        value=subtipo_val,
                        placeholder=f"Ej: Sistemas Avanzados de Impermeabilización",
                        key=f"subtipo_{i}_{j}"
                    )
                with col_btn_remove_sub:
                    if len(item_principal["subtipos"]) > 1:
                        st.button("🗑️ Subtipo", key=f"remove_subtipo_{i}_{j}", on_click=remove_subtipo, args=(i,j), help="Eliminar este Subtipo", use_container_width=True)
                    else:
                        st.markdown("") # Placeholder

            st.button(f"➕ Agregar Subtipo a '{item_principal['tipo_principal'].strip() or 'este Tipo Principal'}'", key=f"add_subtipo_{i}", on_click=add_subtipo, args=(i,))
        # st.markdown("---") # Removed for cleaner look between expanders

    st.button("➕ Agregar Tipo Principal de Tecnología/Servicio", on_click=add_tipo_principal)


st.markdown("---")
st.subheader("3. Generar Prompt")

if st.button("🚀 Generar Prompt para Deep Search", type="primary", use_container_width=True):
    st.session_state.prompt_generated_success = False # Resetear estado
    st.session_state.parsed_dataframe = None

    alcance_dinamico_str_list = []
    all_valid = True
    for i, item_principal in enumerate(st.session_state.alcance_items):
        current_tipo_principal = item_principal["tipo_principal"].strip()
        if not current_tipo_principal:
            st.error(f"El Nombre del Tipo Principal {i+1} no puede estar vacío.")
            all_valid = False
            continue
        alcance_dinamico_str_list.append(f"{i+1}.  **`{current_tipo_principal}`**")
        for j, subtipo in enumerate(item_principal["subtipos"]):
            current_subtipo = subtipo.strip()
            if not current_subtipo:
                st.error(f"El Subtipo {j+1} del Tipo Principal '{current_tipo_principal}' no puede estar vacío.")
                all_valid = False
                continue
            alcance_dinamico_str_list.append(f"    * **`{current_subtipo}`**")

    if not tema_principal.strip() or not problema_especifico.strip() or not criterios_clave.strip():
        st.error("Los campos 'Tema Principal', 'Problema Específico' y 'Criterios Clave' no pueden estar vacíos.")
        all_valid = False

    if all_valid:
        aplicabilidad_contexto_str = f", aplicables en el contexto de {industria_region.strip()}" if industria_region.strip() else ""
        final_prompt = PROMPT_TEMPLATE.format(
            tema_principal=tema_principal.strip(),
            problema_especifico=problema_especifico.strip(),
            criterios_clave=criterios_clave.strip(),
            aplicabilidad_contexto=aplicabilidad_contexto_str,
            alcance_dinamico="\n".join(alcance_dinamico_str_list)
        )

        st.markdown("### ✅ ¡Prompt Generado Exitosamente!")
        st.code(final_prompt, language="markdown")
        st.download_button(
            label="📥 Descargar Prompt como .txt",
            data=final_prompt,
            file_name=f"prompt_investigacion_{tema_principal.replace(' ', '_')[:20]}.txt",
            mime="text/plain"
        )
        st.success("Copia el texto de arriba o descarga el archivo .txt y pégalo en tu interfaz de IA.")
        st.session_state.prompt_generated_success = True # Marcar que el prompt se generó
    else:
        st.warning("Por favor, completa todos los campos marcados como obligatorios en el formulario (especialmente en 'Alcance Detallado') antes de generar el prompt.")

# --- Sección 4: Cargar y Procesar Respuesta CSV (Aparece después de generar el prompt) ---
if st.session_state.get('prompt_generated_success', False):
    st.markdown("---")
    st.header("4. Procesar Respuesta CSV de la IA y Cargar a Base de Datos")
    st.markdown("Una vez que la IA haya procesado el prompt y te haya devuelto los datos en formato CSV (sin encabezados), cópialos y pégalos aquí.")

    csv_input_text = st.text_area(
        "Pega aquí el contenido CSV (datos crudos, sin encabezados):",
        value=st.session_state.csv_input_text_value, # Mantener valor
        height=200,
        key="csv_paste_area_input",
        help="Cada línea debe ser una fila de datos, con campos entre comillas y separados por comas."
    )
    st.session_state.csv_input_text_value = csv_input_text # Actualizar valor en session state

    if st.button("📄 Procesar y Previsualizar CSV Pegado", key="process_csv_button"):
        st.session_state.parsed_dataframe = None # Resetear previsualización anterior
        if csv_input_text:
            try:
                # Usar io.StringIO para tratar el string como un archivo
                csv_file_like_object = io.StringIO(csv_input_text)
                
                # Leer el CSV
                # El prompt pide no incluir encabezados, por lo que los nombres de columna se asignan directamente.
                reader = csv.reader(csv_file_like_object, quotechar='"', delimiter=',', skipinitialspace=True)
                data = list(reader)
                
                if not data:
                    st.warning("No se encontraron datos en el CSV pegado.")
                else:
                    # Verificar que cada fila tenga el número correcto de columnas
                    num_expected_cols = len(CSV_EXPECTED_COLUMNS)
                    valid_data = True
                    for i, row in enumerate(data):
                        if len(row) != num_expected_cols:
                            st.error(f"Error en la fila {i+1}: Se esperaban {num_expected_cols} columnas, pero se encontraron {len(row)}. Fila: {row}")
                            valid_data = False
                            break
                    
                    if valid_data:
                        df = pd.DataFrame(data, columns=CSV_EXPECTED_COLUMNS)
                        st.session_state.parsed_dataframe = df
                        st.success(f"CSV procesado exitosamente. Se encontraron {len(df)} filas.")
                    else:
                        st.session_state.parsed_dataframe = None

            except Exception as e:
                st.error(f"Error al procesar el CSV: {e}")
                st.session_state.parsed_dataframe = None
        else:
            st.warning("El área de texto CSV está vacía.")

    if st.session_state.parsed_dataframe is not None and not st.session_state.parsed_dataframe.empty:
        st.markdown("### Previsualización de Datos Procesados:")
        st.dataframe(st.session_state.parsed_dataframe)

        st.markdown("---")
        st.subheader("Inserción en Base de Datos")
        st.markdown("Este es un ejemplo básico. Para bases de datos de producción, considera aspectos de seguridad, ORMs, y gestión de errores más robusta.")

        db_filename_default = f"investigacion_{tema_principal.replace(' ', '_')[:20] if tema_principal else 'tech'}.db"
        db_filename = st.text_input("Nombre del archivo de Base de Datos:", db_filename_default)
        table_name_db = st.text_input("Nombre de la Tabla en la BD:", "tech_servicios")

        if st.button(f"➕ Insertar {len(st.session_state.parsed_dataframe) if st.session_state.parsed_dataframe is not None else 0} filas en '{table_name_db}'", key="insert_db_button"):
            if st.session_state.parsed_dataframe is not None and not st.session_state.parsed_dataframe.empty:
                conn = None # Inicializar conn
                try:
                    conn = sqlite3.connect(db_filename)
                    cursor = conn.cursor()

                    # Crear tabla si no existe
                    # Las columnas deben coincidir con CSV_EXPECTED_COLUMNS
                    # Es importante usar TEXT para todas por simplicidad en este ejemplo,
                    # pero en un caso real deberías definir tipos más específicos.
                    cols_for_sql = ", ".join([f'"{col}" TEXT' for col in CSV_EXPECTED_COLUMNS])
                    cursor.execute(f"CREATE TABLE IF NOT EXISTS \"{table_name_db}\" ({cols_for_sql})")
                    
                    # Insertar datos
                    # Usar placeholders (?) para prevenir inyección SQL
                    placeholders = ", ".join(["?"] * len(CSV_EXPECTED_COLUMNS))
                    insert_sql = f"INSERT INTO \"{table_name_db}\" ({', '.join([f'"{col}"' for col in CSV_EXPECTED_COLUMNS])}) VALUES ({placeholders})"
                    
                    insert_count = 0
                    for _, row in st.session_state.parsed_dataframe.iterrows():
                        try:
                            cursor.execute(insert_sql, tuple(row))
                            insert_count += 1
                        except sqlite3.Error as e_row:
                            st.warning(f"Error al insertar fila {list(row)}: {e_row}. Se omite esta fila.")
                    
                    conn.commit()
                    st.success(f"{insert_count} filas insertadas/actualizadas exitosamente en la tabla '{table_name_db}' del archivo '{db_filename}'.")

                except sqlite3.Error as e:
                    st.error(f"Error con la base de datos : {e}")
                finally:
                    if conn:
                        conn.close()
            else:
                st.warning("No hay datos procesados para insertar en la base de datos.")

st.markdown("---")
st.caption("Desarrollado como una herramienta de apoyo para la generación de prompts y carga de datos.")