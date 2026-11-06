import unittest
import os
import gspread
from google.oauth2.service_account import Credentials
import app  # Importa tu archivo app.py para validar su lógica

class TestBotMinimercado(unittest.TestCase):
    
    def test_normalizacion_texto(self):
        # Valida que la función de normalización quite tildes y mayúsculas correctamente
        resultado = app.normalizar_texto("  FíDeOs  ")
        self.assertEqual(resultado, "fideos")

    def test_limpieza_texto(self):
        # Valida que la limpieza de caracteres especiales funcione bien para Twilio
        resultado = app.limpiar_texto("Pan & Leche <Fresca>")
        self.assertEqual(resultado, "Pan y Leche Fresca")

    def test_conexion_google_sheets(self):
        # Verifica la existencia de las credenciales inyectadas por GitHub Actions o entorno local
        cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        
        if not cred_path or not os.path.exists(cred_path):
            self.skipTest("No se encontró el archivo credentials.json, omitiendo prueba de Sheets en entorno local.")

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = Credentials.from_service_account_file(cred_path, scopes=scopes)
        gc = gspread.authorize(credentials)
        
        # Confirma que la autenticación con la cuenta de servicio se realizó con éxito
        self.assertIsNotNone(gc)

if __name__ == '__main__':
    unittest.main()
