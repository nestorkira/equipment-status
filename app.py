import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import base64

def load_image_base64(image_path):
    with open(image_path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()
    
logo_owm = load_image_base64("assets/logo_owm.png")
logo_mmg = load_image_base64("assets/logo_mmg.png")

st.set_page_config(page_title="Gantt por Equipo", layout="wide")

st.markdown("""
<style>
/* Fondo general */
.main, .stApp {
    background-color: #FFFFFF !important;
            
}

/* Fondo de los contenedores */
.block-container {
    background-color: #FFFFFF !important;
}

/* Ocultar la barra superior e inferior de Streamlit */
header {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:black;'>Gantt Operacional por Equipo</h1>", unsafe_allow_html=True)
st.write("Sube tu archivo Excel")

file = st.file_uploader(" ", type=["xlsx"])

def convertir_hora(x):
    if isinstance(x, datetime.time):
        return datetime.datetime.combine(datetime.date.today(), x)
    try:
        return pd.to_datetime(x)
    except:
        return None
    
# =====================================================
# FORMULAS DE METRAJE
# =====================================================
FORMULAS_METRAJE = {
    "TD011": {"a": 23.67, "b": 9.71},
    "TD012": {"a": 25.18, "b": 6.81},
    "TD030": {"a": 30.28, "b": 1.59},
    "TD031": {"a": 29.96, "b": -0.31},
    "TD072": {"a": 29.73, "b": 1.19},
    "TD073": {"a": 30.22, "b": 1.93},
    "TD074": {"a": 28.35, "b": 2.24},
    "TD076": {"a": 26.86, "b": 3.30},
    "TD077": {"a": 30.03, "b": 8.14},
    "TD078": {"a": 26.06, "b": 5.49},
    "TD079": {"a": 32.05, "b": 1.07},
    "TD091": {"a": 22.45, "b": 31.79},
    "TD092": {"a": 23.92, "b": 20.37},
}

if file:
    df = pd.read_excel(file)

    columnas = ["Equipo", "Hora Inicio", "Hora Fin", "Descripcion", "Estado"]
    if not all(col in df.columns for col in columnas):
        st.error("El archivo debe contener: Equipo, Hora Inicio, Hora Fin, Descripcion, Estado")
        st.stop()

    df["Hora Inicio"] = df["Hora Inicio"].apply(convertir_hora)
    df["Hora Fin"] = df["Hora Fin"].apply(convertir_hora)
    df["Duracion"] = df["Hora Fin"] - df["Hora Inicio"]

    df["DuracionTexto"] = df["Duracion"].apply(
        lambda x: (
            f"{int(x.total_seconds()//3600):02d}:{int((x.total_seconds()%3600)//60):02d}"
            if x.total_seconds() >= 1800 else ""   # ← solo mostrar si es >= 30 min
        )
    )

    # Ordenar por equipo y hora inicio para evitar desalineos en el texto
    df = df.sort_values(["Equipo", "Hora Inicio"]).reset_index(drop=True)

    hora_inicio_global = datetime.datetime.combine(datetime.date.today(), datetime.time(6, 30))
    hora_fin_global = datetime.datetime.combine(datetime.date.today(), datetime.time(18, 30))

    colores_estado = {
        "Operativo": "#00B050",
        "Demora": "#FFC000",
        "Stand By": "#00B0F0",
        "Inoperativo":"#FF0000",
    }

    df["Color"] = df["Estado"].apply(lambda x: colores_estado.get(str(x), "#95a5a6"))

    # Usar text="DuracionTexto" para que cada segmento reciba su propio texto
    fig = px.timeline(
        df,
        x_start="Hora Inicio",
        x_end="Hora Fin",
        y="Equipo",
        color="Estado",
        text="DuracionTexto",
        color_discrete_map=colores_estado,
        custom_data=["Descripcion", "DuracionTexto"]
    )

    fig.update_yaxes(
        title="",
        tickfont=dict(size=13),
        type="category",
        categoryorder="array",
        categoryarray=df["Equipo"].tolist(),
        autorange="reversed"
    )
    fig.update_xaxes(
        range=[
            hora_inicio_global,
            hora_fin_global + datetime.timedelta(minutes=10)
        ],
        dtick=1800000
    )

    fig.update_layout(
        height=800,

        title=dict(
            text="<b style='color:black; font-size:30px'>ESTADO DE EQUIPOS - OPERACIÓN</b>",
            x=0.5,
            xanchor="center",
            y=0.95
        ),

        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        bargap=0,
        bargroupgap=0.55,
        font=dict(size=13, color="black"),

        margin=dict(t=160),

        images=[
            dict(
                source=logo_owm,
                xref="paper",
                yref="paper",
                x=-0.025,
                y=1.20,
                sizex=0.15,
                sizey=0.15,
                xanchor="left",
                yanchor="top"
            ),
            dict(
                source=logo_mmg,
                xref="paper",
                yref="paper",
                x=0.99,
                y=1.20,
                sizex=0.15,
                sizey=0.15,
                xanchor="right",
                yanchor="top"
            )
        ],

        legend=dict(
            orientation="h",
            yanchor="top",
            y=1.15,
            xanchor="center",
            x=0.475,
            title=dict(text=""),
            font=dict(color="black", size=20)
        )
    )

    fig.update_traces(
        marker_line_color='black',
        marker_line_width=0.5,
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="black", size=11),
    )

    for i, row in df.iterrows():
        desc = row["Descripcion"]

        if isinstance(desc, float) and pd.isna(desc):
            continue
        if str(desc).strip() == "":
            continue

        desc_str = str(desc).strip()

        palabras = desc_str.split()
        if len(palabras) >= 2:
            mitad = len(palabras) // 2
            desc_str = " ".join(palabras[:mitad]) + "<br>" + " ".join(palabras[mitad:])

        fig.add_annotation(
            x=row["Hora Inicio"] + (row["Hora Fin"] - row["Hora Inicio"]) / 2,
            y=row["Equipo"],
            text=desc_str,
            showarrow=False,
            yshift=22,
            font=dict(size=10, color="black")
        )

    fig.update_xaxes(title_font=dict(color="black"), tickfont=dict(color="black"))
    fig.update_yaxes(title_font=dict(color="black"), tickfont=dict(color="black"))

    fig.update_xaxes(dtick=1800000)

    hora_actual = hora_inicio_global
    equipos_unicos = len(df["Equipo"].unique())

    while hora_actual <= hora_fin_global:
        fig.add_shape(
            type="line",
            x0=hora_actual, x1=hora_actual,
            y0=-0.5, y1=equipos_unicos - 0.5,
            line=dict(color="lightgray", width=1, dash="dot"),
            layer="below"
        )
        hora_actual += datetime.timedelta(hours=0.5)

    st.plotly_chart(fig, use_container_width=True)

    # =====================================================
    # METRAJE ACUMULADO
    # =====================================================
    st.markdown(
        "<div style='margin-top:-20px; margin-bottom:-120px;'>"
        "<h2 style='text-align:center; color:black; font-weight:700;'>"
        "AVANCE"
        "</h2>"
        "</div>",
        unsafe_allow_html=True
    )

    df_op = df[df["Estado"] == "Operativo"].copy()
    df_op["Horas"] = df_op["Duracion"].dt.total_seconds() / 3600

    horas_por_equipo = df_op.groupby("Equipo")["Horas"].sum().reset_index()

    def calcular_metraje(row):
        eq = row["Equipo"]
        h = row["Horas"]
        if eq in FORMULAS_METRAJE:
            a = FORMULAS_METRAJE[eq]["a"]
            b = FORMULAS_METRAJE[eq]["b"]
            return a * h + b
        return 0

    horas_por_equipo["Metraje acumulado (m)"] = horas_por_equipo.apply(calcular_metraje, axis=1)

    # =====================================================
    # ACUMULADOS TOTALES DE METRAJE
    # =====================================================

    # Separar DTH y RTR
    df_dth = horas_por_equipo[
        ~horas_por_equipo["Equipo"].isin(["TD091", "TD092"])
    ]

    df_rtr = horas_por_equipo[
        horas_por_equipo["Equipo"].isin(["TD091", "TD092"])
    ]

    # Calcular acumulados
    x_metros_dth = df_dth["Metraje acumulado (m)"].sum()
    y_metros_rtr = df_rtr["Metraje acumulado (m)"].sum()

    # =====================================================
    # MOSTRAR RESULTADOS EN GRANDE
    # =====================================================
    st.markdown("<hr>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"""
            <div style="text-align:center;">
                <h1 style="
                    font-size:60px;
                    color:black;
                    margin-bottom:-20px;
                    margin-top:-60px;
                ">
            {x_metros_dth:,.0f}</h1>
                <h3 style="color:black;">METROS PERFORADOS DTH</h3>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div style="text-align:center;">
                <h1 style="
                    font-size:60px;
                    color:black;
                    margin-bottom:-20px;
                    margin-top:-60px;
                ">
                {y_metros_rtr:,.0f}</h1>
                <h3 style="color:black;">METROS PERFORADOS RTR</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
    # =====================================================
    # OPERATIVIDAD Y PROYECCIÓN POR EQUIPO (CORRECTO)
    # =====================================================

    HORAS_TURNO = 12

    # Duraciones por equipo
    df_eq = (
        df.groupby(["Equipo", "Estado"])["Duracion"]
        .sum()
        .reset_index()
    )

    df_eq["Horas"] = df_eq["Duracion"].dt.total_seconds() / 3600

    # Total y operativo por equipo
    df_total = (
        df_eq.groupby("Equipo")["Horas"]
        .sum()
        .reset_index(name="Horas_totales")
    )

    df_op = (
        df_eq[df_eq["Estado"] == "Operativo"]
        .groupby("Equipo")["Horas"]
        .sum()
        .reset_index(name="Horas_operativas")
    )

    # Unir
    df_proj = df_total.merge(df_op, on="Equipo", how="left")
    df_proj["Horas_operativas"] = df_proj["Horas_operativas"].fillna(0)

    # % operatividad por equipo
    df_proj["Operatividad"] = df_proj["Horas_operativas"] / df_proj["Horas_totales"]

    # =====================================================
    # % OPERATIVIDAD DE TODA LA FLOTA
    # =====================================================

    horas_totales_flota = df_proj["Horas_totales"].sum()
    horas_operativas_flota = df_proj["Horas_operativas"].sum()

    porc_operatividad_flota = (
        horas_operativas_flota / horas_totales_flota
        if horas_totales_flota > 0 else 0
    )

    # Como el criterio es mantener la misma operatividad al cierre
    porc_operatividad_proyectada = porc_operatividad_flota

    df_proj["Operatividad Flota (%)"] = porc_operatividad_flota * 100

    # Horas operativas proyectadas al cierre
    df_proj["Horas_proj"] = df_proj["Operatividad"] * HORAS_TURNO

    # Metraje proyectado por equipo
    def metraje_proyectado(row):
        eq = row["Equipo"]
        h = row["Horas_proj"]

        # Si no hay operatividad proyectada → 0 metros
        if h <= 0:
            return 0

        if eq in FORMULAS_METRAJE:
            a = FORMULAS_METRAJE[eq]["a"]
            b = FORMULAS_METRAJE[eq]["b"]
            return a * h + b

        return 0

    df_proj["Metraje_proyectado (m)"] = df_proj.apply(metraje_proyectado, axis=1)

    # =====================================================
    # ACUMULADOS DTH / RTR
    # =====================================================

    metraje_dth_proj = df_proj[
        ~df_proj["Equipo"].isin(["TD091", "TD092"])
    ]["Metraje_proyectado (m)"].sum()

    metraje_rtr_proj = df_proj[
        df_proj["Equipo"].isin(["TD091", "TD092"])
    ]["Metraje_proyectado (m)"].sum()

    # =====================================================
    # VISUAL EJECUTIVO
    # =====================================================

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        "<div style='margin-top:-40px; margin-bottom:-80px;'>"
        "<h2 style='text-align:center; color:black; font-weight:700;'>"
        "PROYECCIÓN"
        "</h2>",
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div style="text-align:center;">
                <h1 style="
                    font-size:60px;
                    color:#1F4ED8;
                    font-weight:700;
                ">
                    {metraje_dth_proj:,.0f}
                </h1>
                <h3 style="color:black;">
                    METROS PROYECTADOS DTH
                </h3>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div style="text-align:center;">
                <h2 style="
                    color:#21C063;
                    font-size:60px;
                    font-weight:700;
                    margin-bottom:0px;
                ">
                    {porc_operatividad_proyectada*100:.1f}%
                </h2>
                <h3 style="color:black;">
                    OPERATIVIDAD
                </h3>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div style="text-align:center;">
                <h1 style="
                    font-size:60px;
                    color:#1F4ED8;
                    font-weight:700;
                ">
                    {metraje_rtr_proj:,.0f}</h1>
                <h3 style="color:black;">
                    METROS PROYECTADOS RTR
                </h3>
            </div>
            """,
            unsafe_allow_html=True
        )

    col1, col2 = st.columns(2)
    with col1:
        # Filtrar solo filas con demoras
        df_demora = df[df["Estado"] == "Demora"].copy()

        # Convertir duración a minutos directamente desde timedelta
        df_demora["Duracion_min"] = df_demora["Duracion"].dt.total_seconds() / 60

        # Agrupar por descripcion y sumar duración
        df_pie = df_demora.groupby("Descripcion")["Duracion_min"].sum().reset_index()

        # Calcular porcentaje
        df_pie["Porcentaje"] = (df_pie["Duracion_min"] / df_pie["Duracion_min"].sum()) * 100

        # Crear gráfico de pastel
        fig_pie = px.pie(
            df_pie,
            names="Descripcion",
            values="Duracion_min",
            hover_data=["Duracion_min", "Porcentaje"],
            labels={"Duracion_min":"Minutos", "Descripcion":"Tipo de demora"}
        )

        fig_pie.update_traces(
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Tiempo acumulado: %{value:.0f} min<br>Porcentaje: %{percent}"
        )
        fig_pie.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(color="black"),
            legend=dict(
                font=dict(color="black"),
                bgcolor="rgba(0,0,0,0)",
                borderwidth=0
            )
        )

        st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown(
            "<h3 style='text-align:center; font-weight:700; color:black;'>"
            "DISTRIBUCIÓN POR DEMORA"
            "</h3>",
            unsafe_allow_html=True
        )

    with col2:
        # --- Pie chart por Estado con HH:MM y porcentaje dentro ---
        df_estado = df.copy()
        df_estado["Duracion_min"] = df_estado["Duracion"].dt.total_seconds() / 60  # convertir a minutos

        # Agrupar por Estado y sumar duración
        df_pie_estado = df_estado.groupby("Estado")["Duracion_min"].sum().reset_index()

        # Función para convertir minutos a HH:MM
        def min_a_hhmm(minutos):
            h = int(minutos // 60)
            m = int(minutos % 60)
            return f"{h:02d}:{m:02d}"

        df_pie_estado["Duracion_HHMM"] = df_pie_estado["Duracion_min"].apply(min_a_hhmm)

        # Calcular porcentaje
        df_pie_estado["Porcentaje"] = (df_pie_estado["Duracion_min"] / df_pie_estado["Duracion_min"].sum()) * 100

        # Crear gráfico de pastel
        fig_pie_estado = px.pie(
            df_pie_estado,
            names="Estado",
            values="Duracion_min",
            color="Estado",
            color_discrete_map=colores_estado,
        )

        fig_pie_estado.update_traces(
            customdata=df_pie_estado[["Duracion_HHMM", "Porcentaje"]],
            texttemplate="%{label}<br>%{customdata[0]}<br>%{percent}",  # <-- incluir %{label}
            textposition="inside",
            textfont=dict(color="black", size=14),
            hovertemplate="<b>%{label}</b><br>Tiempo acumulado: %{customdata[0]}<br>Porcentaje: %{customdata[1]:.1f}%"
        )

        fig_pie_estado.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(color="black"),
            legend=dict(
                font=dict(color="black"),
                bgcolor="rgba(0,0,0,0)",
                borderwidth=0
            )
        )

        st.plotly_chart(fig_pie_estado, use_container_width=True)
        
        st.markdown(
            "<h3 style='text-align:center; font-weight:700; color:black;'>"
            "DISTRIBUCIÓN POR ESTADO"
            "</h3>",
            unsafe_allow_html=True
        )