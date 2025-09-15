"""
Configuration centralisée pour l'application TEIF
Version 2.0 - Support complet SQL Server et structures TEIF 1.8.8
Optimisée pour les tests et la production
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import quote_plus
from dotenv import load_dotenv
import logging

# Charger les variables d'environnement
load_dotenv()

# Chemins de base
BASE_DIR = Path(__file__).parent.parent.parent
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"
CERTS_DIR = BASE_DIR / "certs"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
TEMP_DIR = BASE_DIR / "temp"
BACKUP_DIR = BASE_DIR / "backup"
TESTS_DIR = BASE_DIR / "tests"
DOCS_DIR = BASE_DIR / "docs"

# Créer les répertoires s'ils n'existent pas
for directory in [DATA_DIR, CERTS_DIR, OUTPUT_DIR, LOGS_DIR, TEMP_DIR, BACKUP_DIR, TESTS_DIR, DOCS_DIR]:
    directory.mkdir(exist_ok=True, parents=True)

def get_environment() -> str:
    """Retourne l'environnement actuel"""
    return os.getenv('ENVIRONMENT', 'development').lower()

def is_development() -> bool:
    """Vérifie si on est en mode développement"""
    return get_environment() == 'development'

def is_production() -> bool:
    """Vérifie si on est en mode production"""
    return get_environment() == 'production'

def is_testing() -> bool:
    """Vérifie si on est en mode test"""
    return get_environment() == 'testing' or 'pytest' in sys.modules

def get_database_config() -> Dict[str, Any]:
    """
    Configuration de base de données avec priorité SQL Server
    Support multi-environnements avec fallback intelligent
    """
    db_type = os.getenv('DATABASE_TYPE', 'sqlserver').lower()
    
    if db_type == 'sqlserver':
        # Configuration SQL Server
        server = os.getenv('SQLSERVER_HOST', 'localhost')
        port = os.getenv('SQLSERVER_PORT', '1433')
        database = os.getenv('SQLSERVER_DATABASE', 'TEIF_Complete_DB')
        driver = 'ODBC Driver 17 for SQL Server'
        
        # Print debug info
        print(f"\n=== Database Connection Debug ===")
        print(f"Server: {server}")
        print(f"Port: {port}")
        print(f"Database: {database}")
        print(f"Driver: {driver}")
        
        # Use Windows Authentication with default instance
        connection_string = (
            f"mssql+pyodbc://{server}/{database}?"
            f"driver={quote_plus(driver)}&"
            "trusted_connection=yes&"
            "TrustServerCertificate=yes&"
            "Encrypt=yes&"
            "Connection+Timeout=30"
        )
        
        print(f"\nConnection String: {connection_string}\n")
        
        return {
            'type': 'sqlserver',
            'url': connection_string,
            'server': server,
            'port': int(port),
            'database': database,
            'username': None,  # Not used with Windows Auth
            'driver': driver,
            'pool_size': int(os.getenv('SQLSERVER_POOL_SIZE', '15')),
            'max_overflow': int(os.getenv('SQLSERVER_MAX_OVERFLOW', '25')),
            'pool_timeout': int(os.getenv('SQLSERVER_POOL_TIMEOUT', '30')),
            'pool_recycle': int(os.getenv('SQLSERVER_POOL_RECYCLE', '3600')),
            'echo': True  # Enable SQL echo for debugging
        }
    
    elif db_type == 'postgresql':
        # Configuration PostgreSQL
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = os.getenv('POSTGRES_PORT', '5432')
        database = os.getenv('POSTGRES_DATABASE', 'teif_complete')
        username = os.getenv('POSTGRES_USER', 'postgres')
        password = os.getenv('POSTGRES_PASSWORD', 'password')
        
        connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
        
        return {
            'type': 'postgresql',
            'url': connection_string,
            'host': host,
            'port': int(port),
            'database': database,
            'username': username,
            'pool_size': int(os.getenv('POSTGRES_POOL_SIZE', '10')),
            'max_overflow': int(os.getenv('POSTGRES_MAX_OVERFLOW', '20')),
            'echo': is_development()
        }
    
    elif db_type == 'sqlite':
        # Configuration SQLite (fallback et tests)
        if is_testing():
            db_path = TEMP_DIR / "test_teif.db"
        else:
            db_path = DATA_DIR / os.getenv('SQLITE_DATABASE', 'teif_complete.db')
        
        return {
            'type': 'sqlite',
            'url': f'sqlite:///{db_path}',
            'path': str(db_path),
            'echo': is_development()
        }
    
    else:
        raise ValueError(f"Type de base de données non supporté: {db_type}")

def get_teif_config() -> Dict[str, Any]:
    """
    Configuration TEIF selon les spécifications 1.8.8
    Paramètres complets pour la génération et validation
    """
    return {
        # Version et agence
        'version': os.getenv('TEIF_VERSION', '1.8.8'),
        'controlling_agency': os.getenv('TEIF_CONTROLLING_AGENCY', 'TTN'),
        'specification_version': '1.8.8',
        'implementation_version': '2.0.0',
        
        # Paramètres par défaut
        'default_currency': os.getenv('TEIF_DEFAULT_CURRENCY', 'TND'),
        'default_country': os.getenv('TEIF_DEFAULT_COUNTRY', 'TN'),
        'default_language': os.getenv('TEIF_DEFAULT_LANGUAGE', 'fr'),
        'default_timezone': os.getenv('TEIF_DEFAULT_TIMEZONE', 'Africa/Tunis'),
        
        # Taux de TVA Tunisie
        'tax_rates': {
            'standard': float(os.getenv('TAX_RATE_STANDARD', '19.0')),
            'reduced': float(os.getenv('TAX_RATE_REDUCED', '13.0')),
            'zero': float(os.getenv('TAX_RATE_ZERO', '0.0')),
            'exempt': float(os.getenv('TAX_RATE_EXEMPT', '0.0'))
        },
        
        # Codes TEIF obligatoires selon spécification 1.8.8
        'mandatory_codes': [
            'I-01',   # Matricule Fiscal Tunisien
            'I-11',   # Facture
            'I-31',   # Date d'émission
            'I-32',   # Date limite de paiement
            'I-61',   # Acheteur
            'I-62',   # Fournisseur
            'I-815',  # Registre de commerce
            'I-88',   # Référence TTN
            'I-93',   # Contact Commercial
            'I-101',  # Téléphone
            'I-103',  # Email
            'I-1602', # TVA
            'I-176',  # Montant total HT facture
            'I-180',  # Montant Total TTC facture
        ],
        
        # Codes optionnels mais recommandés
        'recommended_codes': [
            'I-12',   # Facture proforma
            'I-13',   # Avoir
            'I-33',   # Date de livraison
            'I-63',   # Transporteur
            'I-64',   # Destinataire
            'I-102',  # Fax
            'I-104',  # Site web
            'I-177',  # Montant total TVA
            'I-178',  # Montant total remise
        ],
        
        # Validation
        'validation': {
            'strict_mode': os.getenv('TEIF_VALIDATION_STRICT', 'true').lower() == 'true',
            'check_mandatory_codes': True,
            'validate_amounts': True,
            'validate_dates': True,
            'validate_references': True,
            'validate_tax_calculations': True
        },
        
        # Formats
        'formats': {
            'date_format': '%Y-%m-%d',
            'datetime_format': '%Y-%m-%dT%H:%M:%S',
            'decimal_places': 3,
            'amount_precision': 2
        }
    }

def get_signature_config() -> Dict[str, Any]:
    """
    Configuration pour les signatures électroniques XAdES
    Support complet des certificats X.509
    """
    return {
        # Méthodes de signature
        'default_signature_method': os.getenv('SIGNATURE_METHOD', 'RSA-SHA256'),
        'supported_methods': ['RSA-SHA256', 'RSA-SHA512', 'ECDSA-SHA256'],
        
        # Formats XAdES
        'signature_format': os.getenv('SIGNATURE_FORMAT', 'XAdES-BES'),
        'supported_formats': ['XAdES-BES', 'XAdES-EPES', 'XAdES-T', 'XAdES-LT'],
        
        # Chemins des certificats
        'certificate_path': CERTS_DIR / os.getenv('CERTIFICATE_FILENAME', 'teif_cert.pem'),
        'private_key_path': CERTS_DIR / os.getenv('PRIVATE_KEY_FILENAME', 'teif_key.pem'),
        'ca_certificate_path': CERTS_DIR / os.getenv('CA_CERT_FILENAME', 'ca_cert.pem'),
        'certificate_store_path': CERTS_DIR,
        
        # Validation des certificats
        'validate_certificates': os.getenv('VALIDATE_CERTIFICATES', 'true').lower() == 'true',
        'check_certificate_expiry': True,
        'check_certificate_chain': True,
        'allow_self_signed': is_development(),
        
        # Serveur de timestamp
        'timestamp_server': os.getenv('TIMESTAMP_SERVER', ''),
        'timestamp_timeout': int(os.getenv('TIMESTAMP_TIMEOUT', '30')),
        
        # Paramètres de génération
        'key_size': int(os.getenv('RSA_KEY_SIZE', '2048')),
        'certificate_validity_days': int(os.getenv('CERT_VALIDITY_DAYS', '365')),
        
        # Cache des certificats
        'cache_certificates': True,
        'cache_duration': int(os.getenv('CERT_CACHE_DURATION', '3600')),
    }

def get_output_config() -> Dict[str, Any]:
    """
    Configuration pour les fichiers de sortie
    Gestion des formats et encodages
    """
    return {
        # Répertoires
        'output_directory': OUTPUT_DIR,
        'backup_directory': BACKUP_DIR,
        'temp_directory': TEMP_DIR,
        
        # Formats XML
        'xml_encoding': os.getenv('XML_ENCODING', 'utf-8'),
        'xml_pretty_print': os.getenv('XML_PRETTY_PRINT', 'true').lower() == 'true',
        'xml_declaration': True,
        'xml_namespace_prefix': os.getenv('XML_NAMESPACE_PREFIX', 'teif'),
        
        # Sauvegarde
        'backup_enabled': os.getenv('BACKUP_ENABLED', 'true').lower() == 'true',
        'backup_retention_days': int(os.getenv('BACKUP_RETENTION_DAYS', '30')),
        'compress_backups': os.getenv('COMPRESS_BACKUPS', 'true').lower() == 'true',
        
        # Nommage des fichiers
        'filename_pattern': os.getenv('FILENAME_PATTERN', 'TEIF_{invoice_number}_{timestamp}.xml'),
        'timestamp_format': '%Y%m%d_%H%M%S',
        
        # Validation de sortie
        'validate_output': True,
        'schema_validation': os.getenv('SCHEMA_VALIDATION', 'true').lower() == 'true',
    }

def get_logging_config() -> Dict[str, Any]:
    """
    Configuration de logging avancée
    Support multi-handlers et rotation
    """
    # Niveau selon l'environnement
    if is_development():
        default_level = 'DEBUG'
    elif is_testing():
        default_level = 'WARNING'
    else:
        default_level = 'INFO'
    
    return {
        'level': os.getenv('LOG_LEVEL', default_level),
        'format': os.getenv('LOG_FORMAT', 
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        ),
        
        # Fichiers de log
        'file_enabled': os.getenv('LOG_FILE_ENABLED', 'true').lower() == 'true',
        'file_path': LOGS_DIR / os.getenv('LOG_FILENAME', 'teif.log'),
        'error_file_path': LOGS_DIR / 'teif_errors.log',
        
        # Rotation des logs
        'max_file_size': int(os.getenv('LOG_MAX_FILE_SIZE', '10485760')),  # 10MB
        'backup_count': int(os.getenv('LOG_BACKUP_COUNT', '5')),
        'rotate_when': os.getenv('LOG_ROTATE_WHEN', 'midnight'),
        
        # Handlers spécialisés
        'console_enabled': os.getenv('LOG_CONSOLE_ENABLED', 'true').lower() == 'true',
        'database_logging': os.getenv('LOG_DATABASE_ENABLED', 'false').lower() == 'true',
        'email_alerts': os.getenv('LOG_EMAIL_ALERTS', 'false').lower() == 'true',
        
        # Filtres
        'exclude_modules': ['urllib3', 'requests', 'sqlalchemy.engine'],
        'sensitive_fields': ['password', 'token', 'key', 'secret'],
    }

def get_performance_config() -> Dict[str, Any]:
    """
    Configuration de performance et optimisation
    """
    return {
        # Cache
        'cache_enabled': os.getenv('CACHE_ENABLED', 'true').lower() == 'true',
        'cache_type': os.getenv('CACHE_TYPE', 'memory'),  # memory, redis, file
        'cache_ttl': int(os.getenv('CACHE_TTL', '3600')),
        'cache_max_size': int(os.getenv('CACHE_MAX_SIZE', '1000')),
        
        # Traitement par batch
        'batch_size': int(os.getenv('BATCH_SIZE', '100')),
        'max_workers': int(os.getenv('MAX_WORKERS', '4')),
        'chunk_size': int(os.getenv('CHUNK_SIZE', '1000')),
        
        # Timeouts
        'request_timeout': int(os.getenv('REQUEST_TIMEOUT', '30')),
        'database_timeout': int(os.getenv('DATABASE_TIMEOUT', '60')),
        'signature_timeout': int(os.getenv('SIGNATURE_TIMEOUT', '120')),
        
        # Limites
        'max_file_size': int(os.getenv('MAX_FILE_SIZE', '52428800')),  # 50MB
        'max_invoice_lines': int(os.getenv('MAX_INVOICE_LINES', '1000')),
        'max_concurrent_requests': int(os.getenv('MAX_CONCURRENT_REQUESTS', '10')),
    }

def get_security_config() -> Dict[str, Any]:
    """
    Configuration de sécurité
    """
    return {
        # Chiffrement
        'encryption_key': os.getenv('ENCRYPTION_KEY', ''),
        'hash_algorithm': os.getenv('HASH_ALGORITHM', 'SHA256'),
        
        # Validation
        'input_validation': True,
        'sanitize_inputs': True,
        'max_input_length': int(os.getenv('MAX_INPUT_LENGTH', '10000')),
        
        # Audit
        'audit_enabled': os.getenv('AUDIT_ENABLED', 'true').lower() == 'true',
        'audit_sensitive_operations': True,
        'audit_retention_days': int(os.getenv('AUDIT_RETENTION_DAYS', '90')),
        
        # Accès
        'rate_limiting': os.getenv('RATE_LIMITING', 'false').lower() == 'true',
        'max_requests_per_minute': int(os.getenv('MAX_REQUESTS_PER_MINUTE', '60')),
    }

def get_test_config() -> Dict[str, Any]:
    """
    Configuration spécifique aux tests
    Compatible avec test_teif_generator_complete_new.py
    """
    return {
        # Base de données de test
        'use_test_database': is_testing(),
        'test_database_url': f'sqlite:///{TEMP_DIR}/test_teif.db',
        'reset_database_on_test': True,
        
        # Données de test
        'generate_test_data': True,
        'test_companies_count': int(os.getenv('TEST_COMPANIES_COUNT', '5')),
        'test_invoices_count': int(os.getenv('TEST_INVOICES_COUNT', '20')),
        
        # Certificats de test
        'use_test_certificates': True,
        'generate_test_certificates': True,
        'test_cert_validity_days': 30,
        
        # Validation en mode test
        'skip_external_validation': True,
        'mock_timestamp_server': True,
        'allow_invalid_certificates': True,
        
        # Performance en test
        'fast_mode': True,
        'skip_heavy_operations': True,
        'reduced_batch_size': 10,
    }

def get_app_config() -> Dict[str, Any]:
    """
    Configuration générale de l'application
    """
    return {
        'app_name': 'TEIF Validator & Generator',
        'version': '2.0.0',
        'description': 'Générateur et validateur de factures électroniques TEIF 1.8.8',
        'author': 'TEIF Development Team',
        
        # Environnement
        'environment': get_environment(),
        'debug': is_development(),
        'testing': is_testing(),
        
        # Répertoires
        'base_dir': BASE_DIR,
        'data_dir': DATA_DIR,
        'output_dir': OUTPUT_DIR,
        'temp_dir': TEMP_DIR,
        'logs_dir': LOGS_DIR,
        
        # Fonctionnalités
        'signature_enabled': os.getenv('SIGNATURE_ENABLED', 'true').lower() == 'true',
        'validation_enabled': os.getenv('VALIDATION_ENABLED', 'true').lower() == 'true',
        'database_enabled': os.getenv('DATABASE_ENABLED', 'true').lower() == 'true',
        'web_interface_enabled': os.getenv('WEB_INTERFACE_ENABLED', 'false').lower() == 'true',
    }

# Configuration globale consolidée
def get_config() -> Dict[str, Any]:
    """
    Retourne la configuration complète de l'application
    """
    return {
        'app': get_app_config(),
        'database': get_database_config(),
        'teif': get_teif_config(),
        'signature': get_signature_config(),
        'output': get_output_config(),
        'logging': get_logging_config(),
        'performance': get_performance_config(),
        'security': get_security_config(),
        'test': get_test_config() if is_testing() else {}
    }

# Fonctions utilitaires
def get_database_url() -> str:
    """Raccourci pour obtenir l'URL de connexion à la base de données"""
    return get_database_config()['url']

def get_sqlserver_connection_string() -> str:
    """
    Retourne la chaîne de connexion SQL Server formatée
    Utilisée pour les outils externes (SSMS, Azure Data Studio, etc.)
    """
    config = get_database_config()
    if config['type'] != 'sqlserver':
        raise ValueError("Configuration SQL Server requise")
    
    server = config['server']
    database = config['database']
    username = config.get('username')
    
    if username and username != 'sa':
        return f"Server={server};Database={database};User Id={username};Password=***;TrustServerCertificate=true;"
    elif username == 'sa':
        return f"Server={server};Database={database};User Id={username};Password=***;TrustServerCertificate=true;"
    else:
        return f"Server={server};Database={database};Integrated Security=true;TrustServerCertificate=true;"

def validate_config() -> List[str]:
    """
    Valide la configuration et retourne la liste des erreurs
    """
    errors = []
    
    try:
        # Validation base de données
        db_config = get_database_config()
        if not db_config.get('url'):
            errors.append("URL de base de données manquante")
        
        # Validation TEIF
        teif_config = get_teif_config()
        if not teif_config.get('version'):
            errors.append("Version TEIF manquante")
        
        # Validation signature si activée
        app_config = get_app_config()
        if app_config.get('signature_enabled'):
            sig_config = get_signature_config()
            cert_path = sig_config.get('certificate_path')
            if cert_path and not Path(cert_path).exists():
                if not is_testing():  # En test, on peut générer les certificats
                    errors.append(f"Certificat non trouvé: {cert_path}")
        
        # Validation répertoires
        for dir_name, dir_path in [
            ('data', DATA_DIR),
            ('output', OUTPUT_DIR),
            ('logs', LOGS_DIR)
        ]:
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Impossible de créer le répertoire {dir_name}: {e}")
        
    except Exception as e:
        errors.append(f"Erreur de validation de configuration: {e}")
    
    return errors

def setup_logging():
    """
    Configure le système de logging selon la configuration
    """
    log_config = get_logging_config()
    
    # Configuration de base
    logging.basicConfig(
        level=getattr(logging, log_config['level'].upper()),
        format=log_config['format'],
        handlers=[]
    )
    
    logger = logging.getLogger()
    logger.handlers.clear()
    
    # Handler console
    if log_config['console_enabled']:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_config['format']))
        logger.addHandler(console_handler)
    
    # Handler fichier avec rotation
    if log_config['file_enabled']:
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler(
            log_config['file_path'],
            maxBytes=log_config['max_file_size'],
            backupCount=log_config['backup_count']
        )
        file_handler.setFormatter(logging.Formatter(log_config['format']))
        logger.addHandler(file_handler)
        
        # Handler séparé pour les erreurs
        error_handler = RotatingFileHandler(
            log_config['error_file_path'],
            maxBytes=log_config['max_file_size'],
            backupCount=log_config['backup_count']
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(log_config['format']))
        logger.addHandler(error_handler)

# Initialisation automatique du logging
if not is_testing():
    setup_logging()

# Export de la configuration principale
CONFIG = get_config()

# Validation au démarrage (sauf en test)
if not is_testing():
    config_errors = validate_config()
    if config_errors:
        logger = logging.getLogger(__name__)
        logger.warning("Erreurs de configuration détectées:")
        for error in config_errors:
            logger.warning(f"  - {error}")

# Create a settings object that exposes all configurations
class Settings:
    def __init__(self):
        self.database = get_database_config()
        self.teif = get_teif_config()
        self.signature = get_signature_config()
        self.output = get_output_config()
        self.performance = get_performance_config()
        self.security = get_security_config()
        self.test = get_test_config()
        self.app = get_app_config()
        self.database_url = get_database_url()
        self.sqlserver_connection_string = get_sqlserver_connection_string()

# Create a singleton instance
settings = Settings()

# Export settings as the default export
__all__ = ['settings']
