"""
Script de Web Scraping para Books to Scrape
Extrae información de libros y la guarda en archivos CSV
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import urljoin


def obtener_rating_numerico(rating_clase):
    """Convierte el rating de texto a número"""
    ratings = {
        'One': 1,
        'Two': 2,
        'Three': 3,
        'Four': 4,
        'Five': 5
    }
    for key in ratings:
        if key in rating_clase:
            return ratings[key]
    return 0


def scrape_libro_detalle(url):
    """Extrae información detallada de un libro individual"""
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extraer categoría
        breadcrumb = soup.find('ul', class_='breadcrumb')
        categoria = breadcrumb.find_all('li')[2].text.strip() if breadcrumb else 'N/A'

        # Extraer descripción
        descripcion_tag = soup.find('article', class_='product_page')
        descripcion = ''
        if descripcion_tag:
            desc = descripcion_tag.find('p', recursive=False)
            descripcion = desc.text.strip() if desc else 'Sin descripción'

        # Extraer información de la tabla de producto
        tabla = soup.find('table', class_='table table-striped')
        upc = ''
        disponibilidad = ''

        if tabla:
            filas = tabla.find_all('tr')
            for fila in filas:
                header = fila.find('th').text.strip()
                if header == 'UPC':
                    upc = fila.find('td').text.strip()
                elif header == 'Availability':
                    disponibilidad = fila.find('td').text.strip()

        return categoria, descripcion, upc, disponibilidad
    except Exception as e:
        print(f"Error al obtener detalles: {e}")
        return 'N/A', 'Sin descripción', 'N/A', 'N/A'


def scrape_books_to_scrape(num_paginas=5):
    """
    Realiza scraping de libros de Books to Scrape
    Args:
        num_paginas: Número de páginas a scrapear (cada página tiene ~20 libros)
    """
    base_url = 'https://books.toscrape.com/catalogue/page-{}.html'
    todos_libros = []

    print(f"Iniciando scraping de {num_paginas} páginas...")

    for pagina in range(1, num_paginas + 1):
        print(f"\nProcesando página {pagina}/{num_paginas}...")
        url = base_url.format(pagina)

        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Encontrar todos los libros en la página
            libros = soup.find_all('article', class_='product_pod')

            for libro in libros:
                # Título
                titulo = libro.h3.a['title']

                # Precio
                precio_texto = libro.find('p', class_='price_color').text
                precio = float(precio_texto.replace('£', '').strip())

                # Rating
                rating_clase = libro.find('p', class_='star-rating')['class'][1]
                rating = obtener_rating_numerico(rating_clase)

                # URL de la imagen
                img_tag = libro.find('img')
                imagen_url = urljoin('https://books.toscrape.com/', img_tag['src'])

                # Disponibilidad (en la página principal)
                disponibilidad_tag = libro.find('p', class_='instock availability')
                disponibilidad = disponibilidad_tag.text.strip() if disponibilidad_tag else 'Unknown'

                # URL del libro para obtener más detalles
                libro_url = urljoin('https://books.toscrape.com/catalogue/',
                                    libro.h3.a['href'])

                # Obtener detalles adicionales del libro
                print(f"  - Procesando: {titulo[:50]}...")
                categoria, descripcion, upc, disponibilidad_detalle = scrape_libro_detalle(libro_url)

                # Crear diccionario con la información
                libro_info = {
                    'titulo': titulo,
                    'precio': precio,
                    'rating': rating,
                    'categoria': categoria,
                    'disponibilidad': disponibilidad_detalle,
                    'descripcion': descripcion[:200],  # Limitar descripción
                    'url_imagen': imagen_url,
                    'url_libro': libro_url,
                    'upc': upc
                }

                todos_libros.append(libro_info)

                # Pequeña pausa para no sobrecargar el servidor
                time.sleep(0.5)

            print(f"✓ Página {pagina} completada: {len(libros)} libros extraídos")

        except Exception as e:
            print(f"✗ Error en página {pagina}: {e}")
            continue

    return todos_libros


def guardar_datos(libros):
    """Guarda los datos en archivos CSV"""
    print("\n" + "=" * 60)
    print("GUARDANDO DATOS EN CSV...")
    print("=" * 60)

    # Crear DataFrame principal con todos los datos
    df_completo = pd.DataFrame(libros)
    df_completo.to_csv('libros_completo.csv', index=False, encoding='utf-8')
    print(f"✓ Archivo 'libros_completo.csv' creado con {len(df_completo)} libros")

    # Crear CSV separado con información básica
    df_basico = df_completo[['titulo', 'precio', 'rating', 'categoria']]
    df_basico.to_csv('libros_basico.csv', index=False, encoding='utf-8')
    print(f"✓ Archivo 'libros_basico.csv' creado")

    # Crear CSV con estadísticas por categoría
    stats_categoria = df_completo.groupby('categoria').agg({
        'precio': ['mean', 'min', 'max', 'count'],
        'rating': 'mean'
    }).round(2)
    stats_categoria.columns = ['precio_medio', 'precio_min', 'precio_max', 'num_libros', 'rating_medio']
    stats_categoria.to_csv('estadisticas_categorias.csv', encoding='utf-8')
    print(f"✓ Archivo 'estadisticas_categorias.csv' creado")

    return df_completo


def mostrar_resumen(df):
    """Muestra un resumen de los datos extraídos"""
    print("\n" + "=" * 60)
    print("RESUMEN DE DATOS EXTRAÍDOS")
    print("=" * 60)
    print(f"\nTotal de libros: {len(df)}")
    print(f"Rango de precios: £{df['precio'].min():.2f} - £{df['precio'].max():.2f}")
    print(f"Precio promedio: £{df['precio'].mean():.2f}")
    print(f"Rating promedio: {df['rating'].mean():.2f}/5")
    print(f"\nCategorías encontradas: {df['categoria'].nunique()}")
    print("\nTop 5 categorías con más libros:")
    print(df['categoria'].value_counts().head())
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("=" * 60)
    print("WEB SCRAPING - BOOKS TO SCRAPE")
    print("=" * 60)

    # Configurar número de páginas a scrapear
    # Cada página tiene aproximadamente 20 libros
    NUM_PAGINAS = 3  # Cambia este número según necesites

    print(f"\nConfiguración:")
    print(f"- Páginas a scrapear: {NUM_PAGINAS}")
    print(f"- Libros aproximados: ~{NUM_PAGINAS * 20}")

    # Realizar scraping
    libros = scrape_books_to_scrape(NUM_PAGINAS)

    if libros:
        # Guardar datos
        df = guardar_datos(libros)

        # Mostrar resumen
        mostrar_resumen(df)

        print("\n✓ ¡Scraping completado exitosamente!")
        print("Archivos generados:")
        print("  - libros_completo.csv")
        print("  - libros_basico.csv")
        print("  - estadisticas_categorias.csv")
    else:
        print("\n✗ No se pudieron extraer datos")