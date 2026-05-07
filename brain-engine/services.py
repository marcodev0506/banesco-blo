import httpx
from bs4 import BeautifulSoup
import urllib3

# Desactivamos los logs de advertencia de certificados inseguros (típico del BCV)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RateProvider:
    @staticmethod
    async def get_best_rate():
        url = "https://www.bcv.org.ve/"
        
        # Simulamos ser un navegador real para que el BCV no nos bloquee
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        }

        try:
            # verify=False es vital porque los certificados del BCV suelen dar error en Linux/Docker
            async with httpx.AsyncClient(verify=False, headers=headers, timeout=20.0) as client:
                print("Consultando tasa real en la web del BCV...")
                response = await client.get(url)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    # El BCV coloca la tasa en un div con id 'dolar'
                    # Estructura: <div id="dolar"> ... <strong> 45,1234 </strong> </div>
                    contenedor_dolar = soup.find("div", {"id": "dolar"})
                    
                    if contenedor_dolar:
                        precio_texto = contenedor_dolar.find("strong").text.strip()
                        # Limpiamos el formato: de "45,1234" a 45.1234
                        tasa_limpia = float(precio_texto.replace(",", "."))
                        print(f"¡Éxito! Tasa BCV detectada: {tasa_limpia}")
                        return tasa_limpia
                
                print(f"BCV respondió con status {response.status_code}")
                return 48.50 # Fallback si la página carga pero el formato cambió
                
        except Exception as e:
            print(f"Error en el scraping real: {e}")
            return 48.50 # Fallback por timeout o caída del sitio