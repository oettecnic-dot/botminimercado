import unittest
import app  # Importa tu archivo app.py para probar su lógica interna

class TestBotMinimercado(unittest.TestCase):
    
    def test_normalizacion_texto(self):
        # Valida que la función de normalización quite tildes y mayúsculas correctamente
        resultado = app.normalizar_texto("  FíDeOs  ")
        self.assertEqual(resultado, "fideos")

    def test_limpiar_texto(self):
        # Valida que la limpieza de caracteres especiales funcione bien para Twilio
        resultado = app.limpiar_texto("Pan & Leche <Fresca>")
        self.assertEqual(resultado, "Pan y Leche Fresca")

if __name__ == '__main__':
    unittest.main()
