import unittest
# Importamos las funciones y diccionarios de control desde tu app principal
from app import procesar_logica_minimercado, carritos_clientes, pagos_clientes

class TestBotMinimercadoSDD(unittest.TestCase):
    
    def setUp(self):
        """Se ejecuta antes de cada test para asegurar un entorno limpio por cada cliente de prueba."""
        self.test_user = "whatsapp:+5491188888888"
        carritos_clientes[self.test_user] = []
        pagos_clientes[self.test_user] = "ninguno"

    def test_saludo_inicial_y_categorias(self):
        """Valida que el saludo inicial despliegue correctamente las categorías según el spec.md."""
        respuesta = procesar_logica_minimercado(self.test_user, "Hola")
        self.assertIn("Minimercado", respuesta)
        self.assertIn("Categorías disponibles", respuesta)

    def test_consulta_carrito_vacio(self):
        """Valida que el sistema informe correctamente cuando el carrito no tiene productos."""
        respuesta = procesar_logica_minimercado(self.test_user, "total")
        self.assertIn("vacío", respuesta.lower())

    def test_validacion_opcion_pago_invalida(self):
        """Valida que el estado de pago pendiente rechace opciones fuera del contrato (1, 2, 3)."""
        pagos_clientes[self.test_user] = "pendiente"
        respuesta = procesar_logica_minimercado(self.test_user, "5")
        # El bot debe rechazar el número y solicitar una opción válida
        self.assertTrue("inválida" in respuesta.lower() or "válido" in respuesta.lower())

    def test_vaciar_carrito(self):
        """Valida la regla de negocio de limpiar el carrito de compras a petición del usuario."""
        carritos_clientes[self.test_user] = [{'nombre': 'Test Producto', 'precio': 1000, 'cantidad': 1, 'subtotal': 1000}]
        respuesta = procesar_logica_minimercado(self.test_user, "vaciar")
        self.assertIn("vaciado", respuesta.lower())
        self.assertEqual(len(carritos_clientes[self.test_user]), 0)

if __name__ == "__main__":
    unittest.main()
