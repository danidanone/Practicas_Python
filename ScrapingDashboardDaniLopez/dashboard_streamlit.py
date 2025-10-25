"""
Dashboard Interactivo de Libros con Streamlit
Visualiza y analiza datos de Books to Scrape
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import requests
from io import BytesIO

# Configuración de la página
st.set_page_config(
    page_title="📚 Dashboard de Libros",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #FF6B6B;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def cargar_datos():
    """Carga los datos desde los archivos CSV"""
    try:
        df_completo = pd.read_csv('libros_completo.csv')
        df_stats = pd.read_csv('estadisticas_categorias.csv')
        return df_completo, df_stats
    except FileNotFoundError:
        st.error("❌ No se encontraron los archivos CSV. Por favor, ejecuta primero 'scraping_libros.py'")
        st.stop()

def mostrar_imagen_libro(url):
    """Muestra la imagen del libro desde una URL"""
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        return img
    except:
        return None

def main():
    # Header principal
    st.markdown('<h1 class="main-header">📚 Dashboard de Análisis de Libros</h1>',
                unsafe_allow_html=True)
    st.markdown("### Explora la colección de Books to Scrape")

    # Cargar datos
    df, df_stats = cargar_datos()

    # Sidebar con filtros
    st.sidebar.title("🔍 Filtros de Búsqueda")
    st.sidebar.markdown("---")

    # Filtro por categoría
    categorias = ['Todas'] + sorted(df['categoria'].unique().tolist())
    categoria_seleccionada = st.sidebar.selectbox(
        "📖 Selecciona una categoría:",
        categorias
    )

    # Filtro por rango de precio
    precio_min = float(df['precio'].min())
    precio_max = float(df['precio'].max())
    rango_precio = st.sidebar.slider(
        "💰 Rango de precio (£):",
        precio_min, precio_max,
        (precio_min, precio_max)
    )

    # Filtro por rating
    rating_minimo = st.sidebar.select_slider(
        "⭐ Rating mínimo:",
        options=[1, 2, 3, 4, 5],
        value=1
    )

    # Filtro por disponibilidad
    mostrar_disponibles = st.sidebar.checkbox(
        "✅ Mostrar solo disponibles",
        value=False
    )

    # Aplicar filtros
    df_filtrado = df.copy()

    if categoria_seleccionada != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['categoria'] == categoria_seleccionada]

    df_filtrado = df_filtrado[
        (df_filtrado['precio'] >= rango_precio[0]) &
        (df_filtrado['precio'] <= rango_precio[1]) &
        (df_filtrado['rating'] >= rating_minimo)
    ]

    if mostrar_disponibles:
        df_filtrado = df_filtrado[df_filtrado['disponibilidad'].str.contains('In stock', na=False)]

    # Métricas principales
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📚 Total Libros",
            value=len(df_filtrado),
            delta=f"{len(df_filtrado) - len(df)} respecto al total"
        )

    with col2:
        st.metric(
            label="💰 Precio Promedio",
            value=f"£{df_filtrado['precio'].mean():.2f}"
        )

    with col3:
        st.metric(
            label="⭐ Rating Promedio",
            value=f"{df_filtrado['rating'].mean():.1f}/5"
        )

    with col4:
        st.metric(
            label="📂 Categorías",
            value=df_filtrado['categoria'].nunique()
        )

    # Pestañas para diferentes vistas
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Análisis", "📋 Catálogo", "🏆 Top Libros", "📈 Estadísticas"])

    with tab1:
        st.header("📊 Análisis Visual de Datos")

        col1, col2 = st.columns(2)

        with col1:
            # Gráfico de distribución de precios
            st.subheader("💰 Distribución de Precios")
            fig_precio = px.histogram(
                df_filtrado,
                x='precio',
                nbins=20,
                title='Distribución de Precios',
                labels={'precio': 'Precio (£)', 'count': 'Cantidad de Libros'},
                color_discrete_sequence=['#667eea']
            )
            st.plotly_chart(fig_precio, use_container_width=True)

        with col2:
            # Gráfico de ratings
            st.subheader("⭐ Distribución de Ratings")
            rating_counts = df_filtrado['rating'].value_counts().sort_index()
            fig_rating = px.bar(
                x=rating_counts.index,
                y=rating_counts.values,
                title='Cantidad de Libros por Rating',
                labels={'x': 'Rating', 'y': 'Cantidad'},
                color=rating_counts.values,
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig_rating, use_container_width=True)

        # Gráfico de categorías
        st.subheader("📚 Libros por Categoría")
        categoria_counts = df_filtrado['categoria'].value_counts().head(10)
        fig_categorias = px.bar(
            x=categoria_counts.values,
            y=categoria_counts.index,
            orientation='h',
            title='Top 10 Categorías con Más Libros',
            labels={'x': 'Cantidad', 'y': 'Categoría'},
            color=categoria_counts.values,
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_categorias, use_container_width=True)

        # Relación precio-rating
        st.subheader("💰⭐ Relación Precio vs Rating")
        fig_scatter = px.scatter(
            df_filtrado,
            x='precio',
            y='rating',
            color='categoria',
            size='precio',
            hover_data=['titulo'],
            title='Relación entre Precio y Rating',
            labels={'precio': 'Precio (£)', 'rating': 'Rating'}
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    with tab2:
        st.header("📋 Catálogo de Libros")

        # Selector de ordenamiento
        col1, col2 = st.columns([3, 1])
        with col1:
            orden = st.selectbox(
                "Ordenar por:",
                ["Título (A-Z)", "Precio (Mayor a Menor)", "Precio (Menor a Mayor)",
                 "Rating (Mayor a Menor)", "Rating (Menor a Mayor)"]
            )

        # Aplicar ordenamiento
        if orden == "Título (A-Z)":
            df_mostrar = df_filtrado.sort_values('titulo')
        elif orden == "Precio (Mayor a Menor)":
            df_mostrar = df_filtrado.sort_values('precio', ascending=False)
        elif orden == "Precio (Menor a Mayor)":
            df_mostrar = df_filtrado.sort_values('precio')
        elif orden == "Rating (Mayor a Menor)":
            df_mostrar = df_filtrado.sort_values('rating', ascending=False)
        else:
            df_mostrar = df_filtrado.sort_values('rating')

        # Mostrar libros en tarjetas
        for idx, libro in df_mostrar.iterrows():
            with st.container():
                col1, col2 = st.columns([1, 3])

                with col1:
                    img = mostrar_imagen_libro(libro['url_imagen'])
                    if img:
                        st.image(img, width=150)

                with col2:
                    st.markdown(f"### {libro['titulo']}")
                    st.markdown(f"**Categoría:** {libro['categoria']}")

                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.markdown(f"**💰 Precio:** £{libro['precio']:.2f}")
                    with col_b:
                        st.markdown(f"**⭐ Rating:** {'⭐' * libro['rating']}")
                    with col_c:
                        disponible = "✅ Disponible" if "In stock" in str(libro['disponibilidad']) else "❌ No disponible"
                        st.markdown(f"**{disponible}**")

                    with st.expander("📝 Ver descripción"):
                        st.write(libro['descripcion'])
                        st.markdown(f"[🔗 Ver en web]({libro['url_libro']})")

                st.markdown("---")

    with tab3:
        st.header("🏆 Top Libros")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("💎 Libros Mejor Valorados")
            top_rating = df_filtrado.nlargest(5, 'rating')[['titulo', 'rating', 'precio', 'categoria']]
            for idx, libro in top_rating.iterrows():
                st.markdown(f"""
                **{libro['titulo'][:50]}...**  
                ⭐ Rating: {libro['rating']}/5 | 💰 £{libro['precio']:.2f} | 📚 {libro['categoria']}
                """)
                st.markdown("---")

        with col2:
            st.subheader("💰 Libros Más Caros")
            top_precio = df_filtrado.nlargest(5, 'precio')[['titulo', 'precio', 'rating', 'categoria']]
            for idx, libro in top_precio.iterrows():
                st.markdown(f"""
                **{libro['titulo'][:50]}...**  
                💰 £{libro['precio']:.2f} | ⭐ Rating: {libro['rating']}/5 | 📚 {libro['categoria']}
                """)
                st.markdown("---")

    with tab4:
        st.header("📈 Estadísticas por Categoría")

        # Tabla de estadísticas
        st.dataframe(
            df_stats.style.highlight_max(axis=0, color='lightgreen'),
            use_container_width=True
        )

        # Gráfico de precio medio por categoría
        st.subheader("💰 Precio Medio por Categoría")
        fig_precio_cat = px.bar(
            df_stats.reset_index().sort_values('precio_medio', ascending=False).head(15),
            x='categoria',
            y='precio_medio',
            title='Top 15 Categorías por Precio Medio',
            labels={'precio_medio': 'Precio Medio (£)', 'categoria': 'Categoría'},
            color='precio_medio',
            color_continuous_scale='RdYlGn_r'
        )
        fig_precio_cat.update_xaxes(tickangle=-45)
        st.plotly_chart(fig_precio_cat, use_container_width=True)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray;'>
        <p>📚 Dashboard de Libros | Datos de Books to Scrape | Creado con Streamlit</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()