import unittest1
from app import procesar_logica_minimercado, carritos_clientes, pagos_clientes

class TestBotMinimercado(unittest.TestCase):
    
    def setUp(self):
        """Se ejecuta antes de cada test para limpiar la memoria de los clientes de prueba."""
        self.test_user = "whatsapp:+5491199999999"
        carritos_clientes[self.test_user] = []
        pagos_clientes[self.test_user] = "ninguno"

    def test_saludo_inicial(self):
        """Verifica que el bot responda al saludo inicial según las reglas del spec.md."""
        respuesta = procesar_logica_minimercado(self.test_user, "Hola")
        self.assertIn("Minimercado", respuesta)
        self.assertIn("Categorías disponibles", respuesta)

    def test_carrito_vacio(self):
        """Verifica el comportamiento al consultar un carrito vacío."""
        respuesta = procesar_logica_minimercado(self.test_user, "total")
        self.assertIn("vacío", respuesta.lower())

    def test_flujo_pago_invalido(self):
        """Verifica que el bot rechace opciones de pago fuera de rango (1, 2, 3)."""
        pagos_clientes[self.test_user] = "pendiente"
        respuesta = procesar_logica_minimercado(self.test_user, "9")
        self.assertIn("válido", respuesta.lower()) or self.assertIn("inválida", respuesta.lower())

if __name__ == "__main__":
    unittest.main()
