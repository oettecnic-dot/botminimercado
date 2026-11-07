import os
import unittest
import gspread
from google.oauth2.service_account import Credentials

class TestBotMinimercado(unittest.TestCase):
    
    def setUp(self):
        """Configuración inicial para las pruebas utilizando variables de entorno."""
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        
        client_email = os.environ.get("GCP_CLIENT_EMAIL")
        private_key = os.environ.get("GCP_PRIVATE_KEY")
        
        # Verificar que las credenciales existan antes de conectar
        if not client_email or not private_key:
            raise ValueError("Faltan las variables de entorno de Google Credentials en el entorno de pruebas.")

        # Formatear correctamente los saltos de línea de la clave privada
        formatted_private_key = private_key.replace("\\n", "\n")

        credentials = Credentials.from_service_account_info({
            "client_email": client_email,
            "private_key": formatted_private_key,
            "token_uri": "https://oauth2.googleapis.com/token",
        }, scopes=scopes)

        self.gc = gspread.authorize(credentials)

    def test_conexion_google_sheets(self):
        """Prueba básica para verificar la autenticación y conexión con gspread."""
        self.assertIsNotNone(self.gc, "La autorización de gspread falló.")

if __name__ == "__main__":
    unittest.main()
