"""Listas de referência usadas pelo gerador."""

COUNTRIES = ["BR", "MX", "CO", "CL", "AR"]
COUNTRY_W = [62, 18, 9, 7, 4]
TZ_OFFSET = {"BR": -3, "MX": -6, "CO": -5, "CL": -3, "AR": -3}
FX = {"BR": 1.0, "MX": 3.4, "CO": 780.0, "CL": 165.0, "AR": 190.0}
CURRENCY = {"BR": "BRL", "MX": "MXN", "CO": "COP", "CL": "CLP", "AR": "ARS"}

FIRST_NAMES = [
    "João", "Maria", "Ana", "Pedro", "Lucas", "Juliana", "Carlos", "Fernanda", "Rafael",
    "Camila", "Gabriel", "Beatriz", "Diego", "Valentina", "Sofía", "Mateo", "Camilo",
    "Andrés", "Isabella", "Javier", "Daniela", "Santiago", "Luciana", "Tomás", "Paula",
]
LAST_NAMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Pereira", "Costa", "Rodrigues", "Almeida",
    "García", "Hernández", "López", "Martínez", "Gómez", "Rojas", "Pérez", "Fernández",
    "Ramírez", "Torres", "Vargas", "Mendoza", "Lima", "Barbosa", "Ribeiro", "Carvalho",
]
EMAIL_DOMAINS = ["gmail.com", "hotmail.com", "outlook.com", "yahoo.com", "uol.com.br"]

CITIES = {
    "BR": [("São Paulo", "SP"), ("Rio de Janeiro", "RJ"), ("Belo Horizonte", "MG"),
           ("Curitiba", "PR"), ("Campinas", "SP"), ("Salvador", "BA"), ("Recife", "PE")],
    "MX": [("Ciudad de México", "CDMX"), ("Guadalajara", "JAL"), ("Monterrey", "NL")],
    "CO": [("Bogotá", "DC"), ("Medellín", "ANT"), ("Cali", "VAC")],
    "CL": [("Santiago", "RM"), ("Valparaíso", "VS")],
    "AR": [("Buenos Aires", "BA"), ("Córdoba", "CB")],
}

CATEGORIES = {
    "Eletrônicos": ["Celulares", "Notebooks", "TVs", "Áudio", "Acessórios"],
    "Casa": ["Móveis", "Cozinha", "Decoração", "Cama e Banho"],
    "Moda": ["Camisetas", "Calçados", "Jeans", "Esporte"],
    "Supermercado": ["Mercearia", "Bebidas", "Limpeza", "Higiene"],
    "Brinquedos": ["Jogos", "Bonecos", "Educativos"],
}
BRANDS = ["NovaTech", "Casalar", "UrbanWear", "Sonora", "Brilhante", "Vitta", "Ecomax", "Prime"]
PRODUCT_WORDS = ["Pro", "Max", "Lite", "Plus", "Smart", "Ultra", "Classic", "Eco", "Home", "Sport"]

CHANNELS = ["ecommerce", "app", "marketplace", "store"]
CHANNEL_W = [38, 27, 13, 22]
PAYMENT_METHODS = ["CREDIT_CARD", "DEBIT_CARD", "PIX", "BOLETO", "WALLET", "VOUCHER"]
CARRIERS = ["TransNova", "RapidoLog", "EntregaFacil", "MercoExpress"]
CAMPAIGN_CHANNELS = ["EMAIL", "SOCIAL", "SEARCH", "DISPLAY", "PUSH"]
CTR = {"EMAIL": 0.12, "SOCIAL": 0.06, "SEARCH": 0.10, "DISPLAY": 0.02, "PUSH": 0.15}
PLACEMENTS = ["home_banner", "search_top", "feed", "newsletter", "product_page"]

TICKET_CATEGORIES = [
    "DELIVERY_DELAY", "PRODUCT_DEFECT", "PAYMENT_ISSUE", "REFUND", "ACCOUNT", "OTHER",
]
TICKET_MESSAGES = [
    "Meu pedido ainda não chegou, já passou do prazo.",
    "O produto veio com defeito, quero a troca.",
    "Fui cobrado duas vezes no cartão.",
    "No consigo acessar minha conta no aplicativo.",
    "Preciso do reembolso do pedido cancelado.",
    "El producto llegó dañado, necesito ayuda.",
    "¿Cuándo llega mi pedido? Ya pasó la fecha prometida.",
]
