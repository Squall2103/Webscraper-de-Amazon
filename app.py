import os # Importar os para manejar archivos
import re # Importar re para expresiones regulares
from datetime import datetime # Importar datetime para manejar fechas
import pandas as pd # Importar pandas para manejar datos
import requests # Importar requests para hacer solicitudes HTTP
from bs4 import BeautifulSoup # Importar BeautifulSoup para analizar HTML
import streamlit as st # Importar Streamlit para crear la aplicación web
import time # Importar time para manejar tiempos
import random # Importar random para generar números aleatorios

# ==================== CONFIGURACIÓN MEJORADA ====================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36", # user agent de Chrome
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0", # user agent de Firefox
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux i686; rv:125.0) Gecko/20100101 Firefox/125.0",

    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15", # user agent de Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0", # user agent de Edge
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 OPR/89.0.4447.83", # user agent de Opera
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Brave/1.62.153", # user agent de Brave
]

def get_random_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br', 
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
    }

def random_delay():
    """Retraso más seguro para evitar bloqueos"""
    time.sleep(random.uniform(2, 5))  # Entre 2 y 5 segundos

# ==================== FUNCIONES PRINCIPALES ====================
def get_product_info(url):
    session = requests.Session()  # Usar sesión para mantener cookies
    session.headers.update(get_random_headers())
    
    try:
        random_delay()  # Retraso antes de cada producto
        response = session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

        # Obtener título
        title = soup.find('span', {'id': 'productTitle'})
        title = title.get_text(strip=True) if title else "N/A"

        # Obtener precio
        price = None
        price_selectors = [
            'span.a-price span.a-offscreen',
            'span.a-price-whole',
            'span.a-offscreen',
            'span.priceToPay span.a-price-whole',
        ]
        
        for selector in price_selectors:
            price_element = soup.select_one(selector)
            if price_element:
                price_text = price_element.get_text(strip=True)
                price_match = re.search(r'(\d+[\.,]?\d*[\.,]?\d*)', price_text.replace(',', ''))
                if price_match:
                    price_str = price_match.group(1).replace(',', '.')
                    price = float(price_str)
                    if price.is_integer() and 'a-price-whole' in selector:
                        fraction = soup.select_one('span.a-price-fraction')
                        if fraction:
                            fraction_text = fraction.get_text(strip=True)
                            fraction_match = re.search(r'(\d+)', fraction_text)
                            if fraction_match:
                                price += float(fraction_match.group(1)) / 100
                    break
        
        if price is None:
            price = 0.0

        return title, price

    except Exception as e:
        st.error(f"Error al obtener información del producto: {str(e)}")
        return "N/A", 0.0

def get_search_results(query):
    session = requests.Session()
    session.headers.update(get_random_headers())
    
    try:
        random_delay()  # Retraso antes de la búsqueda
        url = f"https://www.amazon.com/s?k={query.replace(' ', '+')}"
        response = session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

        product_links = []
        links = soup.find_all('a', {'class': 'a-link-normal s-no-outline'})
        
        for link in links:
            href = link.get('href', '')
            if href and '/dp/' in href:
                full_url = "https://www.amazon.com" + href.split('?')[0]
                product_links.append(full_url)

        return list(set(product_links))[:10]

    except Exception as e:
        st.error(f"Error en la búsqueda: {str(e)}")
        return []
    
# ==================== FUNCIÓN PARA GUARDAR EN EXCEL ====================
def save_to_excel(data):
    """Guarda los datos en un archivo Excel."""
    df = pd.DataFrame(data)
    df_to_save = df.drop(columns=['Precio Numérico'], errors='ignore')  # Elimina columna numérica
    
    file_name = "busquedas.xlsx"
    
    if os.path.exists(file_name):
        existing_df = pd.read_excel(file_name)
        df_to_save = pd.concat([existing_df, df_to_save], ignore_index=True)
    
    df_to_save.to_excel(file_name, index=False)
    return file_name

# ==================== STREAMLIT APP  ====================
st.title("Producto Scraper de Amazon")

if 'last_search_data' in st.session_state and 'last_search_query' in st.session_state:
    all_data_sorted = st.session_state['last_search_data']
    search_query = st.session_state['last_search_query']
    
    df_display = pd.DataFrame(all_data_sorted)
    df_display = df_display.drop(columns=['Precio Numérico'])
    
    st.write(f"Mostrando resultados anteriores para: {search_query}")
    df_display['Acción'] = df_display['URL Producto'].apply(
        lambda url: f'<a href="{url}" target="_blank"><button style="background-color:#FF9900;color:white;border:none;padding:5px 10px;border-radius:3px;">Ver</button></a>'
    )
    df_display = df_display.reset_index(drop=True).rename_axis('N°').reset_index()
    df_display['N°'] = df_display['N°'] + 1
    st.write(df_display.drop(columns=['URL Producto']).to_html(index=False, escape=False), unsafe_allow_html=True)
    
    file_name = f"busquedas.xlsx"
    with open(file_name, "rb") as f:
        st.download_button(
            label="Descargar Excel",
            data=f,
            file_name=file_name,
            mime="application/vnd.ms-excel",
            key='download_button_2'
        )

search_query = st.text_input("Introduce tu búsqueda en Amazon:")

if st.button("Buscar") and search_query:
    with st.spinner('Buscando productos...'):
        random_delay()  # Retraso adicional al inicio de la búsqueda
        product_urls = get_search_results(search_query)

        if not product_urls:
            st.error("No se encontraron resultados o Amazon está bloqueando las solicitudes.")
            st.info("Intenta con una conexión diferente o usa proxies si esto persiste.")
        else:
            st.write(f"Encontrados {len(product_urls)} productos para: {search_query}")
            
            all_data = []
            progress_bar = st.progress(0)
            
            for i, url in enumerate(product_urls):
                random_delay()  # Retraso mejorado entre productos
                title, price = get_product_info(url)
                
                if title != "N/A":
                    data = {
                        'Fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'Título': title,
                        'Precio (USD)': f"${price:,.2f}".replace('.', 'temp').replace(',', '.').replace('temp', ','),
                        'Precio Numérico': price,
                        'URL Producto': url,
                    }
                    all_data.append(data)
                
                progress_bar.progress((i + 1) / len(product_urls))

            if all_data:
                all_data_sorted = sorted(all_data, key=lambda x: x['Precio Numérico'])
                df_display = pd.DataFrame(all_data_sorted).drop(columns=['Precio Numérico'])
                
                st.write("### Información de los Productos")
                df_display['Acción'] = df_display['URL Producto'].apply(
                    lambda url: f'<a href="{url}" target="_blank"><button style="background-color:#FF9900;color:white;border:none;padding:5px 10px;border-radius:3px;">Ver</button></a>'
                )
                df_display = df_display.reset_index(drop=True).rename_axis('N°').reset_index()
                df_display['N°'] = df_display['N°'] + 1
                st.write(df_display.drop(columns=['URL Producto']).to_html(index=False, escape=False), unsafe_allow_html=True)
                
                file_name = save_to_excel(all_data_sorted)
                st.success(f"Datos guardados en {file_name}")
                
                st.session_state['last_search_data'] = all_data_sorted
                st.session_state['last_search_query'] = search_query
                
                with open(file_name, "rb") as f:
                    st.download_button(
                        label="Descargar Excel",
                        data=f,
                        file_name=file_name,
                        mime="application/vnd.ms-excel",
                        key='download_button'
                    )
            else:
                st.error("No se pudo obtener información de ningún producto.")