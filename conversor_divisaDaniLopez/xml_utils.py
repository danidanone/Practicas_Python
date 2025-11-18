import requests
import xml.etree.ElementTree as ET


def cargar_datos_bce():
    url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"

    try:
        respuesta = requests.get(url)
        if respuesta.status_code != 200:
            print("No se pudo obtener el XML")
            return None, {}

        xml = respuesta.content
        arbol = ET.fromstring(xml)

        # El namespace del BCE
        ns = {"gesmes": "http://www.gesmes.org/xml/2002-08-01",
              "def": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref"}

        # Se busca el nodo Cube con la fecha
        nodo_fecha = arbol.find(".//def:Cube/def:Cube", ns)
        fecha = nodo_fecha.get("time")

        # Diccionario de tasas
        tasas = {"EUR": 1.0}  # El euro base
        for c in nodo_fecha.findall("def:Cube", ns):
            moneda = c.get("currency")
            rate = float(c.get("rate"))
            tasas[moneda] = rate

        return fecha, tasas

    except Exception as e:
        print("Error:", e)
        return None, {}
