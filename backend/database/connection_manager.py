"""
Database Connection Manager with Automatic Fallback
Tries to connect to new LMS database first, falls back to old EDU database if it fails.
"""

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import logging
import time
from typing import Optional, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """
    Manages database connections with automatic fallback.
    
    Attempts to connect to new LMS database first.
    If connection fails, automatically falls back to old EDU database.
    Periodically retries connection to primary database.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the connection manager.
        
        Args:
            config: Optional configuration dictionary with database settings
        """
        self.config = config or {}
        
        # Primary database (new LMS)
        self.primary_config = {
            'database': self.config.get('primary_database', 'lms'),
            'user': self.config.get('user', 'postgres'),
            'password': self.config.get('password', '1111'),
            'host': self.config.get('host', 'localhost'),
            'port': self.config.get('port', 5432),
        }
        
        # Fallback database (old EDU)
        self.fallback_config = {
            'database': self.config.get('fallback_database', 'edu'),
            'user': self.config.get('user', 'postgres'),
            'password': self.config.get('password', '1111'),
            'host': self.config.get('host', 'localhost'),
            'port': self.config.get('port', 5432),
        }
        
        # Connection pools
        self.primary_pool: Optional[pool.SimpleConnectionPool] = None
        self.fallback_pool: Optional[pool.SimpleConnectionPool] = None
        
        # Status tracking
        self.using_fallback = False
        self.last_primary_attempt = 0
        self.retry_interval = 60  # Retry primary every 60 seconds
        self.max_retries = 3
        
        # Initialize pools
        self._initialize_pools()
    
    def _initialize_pools(self):
        """Initialize connection pools for both databases."""
        try:
            # Try to create primary pool
            self.primary_pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=20,
                **self.primary_config
            )
            logger.info(f"✅ Primary database pool initialized: "
                       f"{self.primary_config['database']}")
            self.using_fallback = False
        except Exception as e:
            logger.error(f"❌ Failed to initialize primary database: {e}")
            self.primary_pool = None
            self.using_fallback = True
        
        # Always initialize fallback pool
        try:
            self.fallback_pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=20,
                **self.fallback_config
            )
            logger.info(f"✅ Fallback database pool initialized: "
                       f"{self.fallback_config['database']}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize fallback database: {e}")
            self.fallback_pool = None
            if self.primary_pool is None:
                raise Exception("Both primary and fallback databases failed!")
    
    def _should_retry_primary(self) -> bool:
        """Check if we should retry connecting to primary database."""
        if not self.using_fallback:
            return False
        
        current_time = time.time()
        if current_time - self.last_primary_attempt >= self.retry_interval:
            self.last_primary_attempt = current_time
            return True
        
        return False
    
    def _try_reconnect_primary(self):
        """Attempt to reconnect to primary database."""
        if not self._should_retry_primary():
            return
        
        logger.info("Attempting to reconnect to primary database...")
        
        try:
            # Close existing pool if it exists
            if self.primary_pool:
                self.primary_pool.closeall()
            
            # Create new pool
            self.primary_pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=20,
                **self.primary_config
            )
            
            # Test connection
            conn = self.primary_pool.getconn()
            conn.close()
            self.primary_pool.putconn(conn)
            
            logger.info("✅ Successfully reconnected to primary database!")
            self.using_fallback = False
            
        except Exception as e:
            logger.warning(f"⚠️ Primary database still unavailable: {e}")
            self.primary_pool = None
    
    @contextmanager
    def get_connection(self, dict_cursor: bool = True):
        """
        Get a database connection with automatic fallback.
        
        Args:
            dict_cursor: If True, return RealDictCursor
        
        Yields:
            Database connection
        """
        # Try to reconnect to primary if using fallback
        if self.using_fallback:
            self._try_reconnect_primary()
        
        connection = None
        pool_used = None
        
        try:
            # Try primary first
            if self.primary_pool and not self.using_fallback:
                try:
                    connection = self.primary_pool.getconn()
                    pool_used = 'primary'
                    
                    # Set cursor factory if needed
                    if dict_cursor:
                        connection.cursor_factory = RealDictCursor
                    
                    logger.debug(f"Using primary database: "
                                f"{self.primary_config['database']}")
                    
                except Exception as e:
                    logger.error(f"❌ Primary database connection failed: {e}")
                    
                    # Return connection to pool if we got one
                    if connection:
                        self.primary_pool.putconn(connection)
                        connection = None
                    
                    # Mark as using fallback
                    self.using_fallback = True
            
            # Use fallback if primary failed or unavailable
            if connection is None and self.fallback_pool:
                try:
                    connection = self.fallback_pool.getconn()
                    pool_used = 'fallback'
                    
                    # Set cursor factory if needed
                    if dict_cursor:
                        connection.cursor_factory = RealDictCursor
                    
                    logger.warning(f"⚠️ Using fallback database: "
                                  f"{self.fallback_config['database']}")
                    
                except Exception as e:
                    logger.error(f"❌ Fallback database connection failed: {e}")
                    if connection:
                        self.fallback_pool.putconn(connection)
                        connection = None
            
            # If still no connection, raise error
            if connection is None:
                raise Exception("Both primary and fallback databases "
                               "are unavailable!")
            
            # Yield the connection
            yield connection
            
        finally:
            # Return connection to appropriate pool
            if connection:
                try:
                    if pool_used == 'primary' and self.primary_pool:
                        self.primary_pool.putconn(connection)
                    elif pool_used == 'fallback' and self.fallback_pool:
                        self.fallback_pool.putconn(connection)
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {e}")
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get information about current database connection."""
        return {
            'using_fallback': self.using_fallback,
            'primary_available': self.primary_pool is not None,
            'fallback_available': self.fallback_pool is not None,
            'current_database': (
                self.fallback_config['database'] if self.using_fallback
                else self.primary_config['database']
            ),
            'last_primary_attempt': self.last_primary_attempt,
        }
    
    def close_all(self):
        """Close all connection pools."""
        if self.primary_pool:
            self.primary_pool.closeall()
            logger.info("Primary database pool closed")
        
        if self.fallback_pool:
            self.fallback_pool.closeall()
            logger.info("Fallback database pool closed")


# Global instance
_db_manager: Optional[DatabaseConnectionManager] = None


def get_db_manager(config: Optional[Dict[str, Any]] = None) -> DatabaseConnectionManager:
    """
    Get or create the global database manager instance.
    
    Args:
        config: Optional configuration dictionary
    
    Returns:
        DatabaseConnectionManager instance
    """
    global _db_manager
    
    if _db_manager is None:
        _db_manager = DatabaseConnectionManager(config)
    
    return _db_manager


def get_db_connection(dict_cursor: bool = True):
    """
    Convenience function to get a database connection.
    
    Args:
        dict_cursor: If True, return RealDictCursor
    
    Returns:
        Context manager yielding database connection
    """
    manager = get_db_manager()
    return manager.get_connection(dict_cursor=dict_cursor)


# Example usage
if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Testing Database Connection Manager")
    print("=" * 60)
    
    # Get database manager
    manager = get_db_manager()
    
    # Get connection and test
    with manager.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT current_database(), version()")
        result = cur.fetchone()
        
        print(f"\nConnected to: {result['current_database']}")
        print(f"PostgreSQL version: {result['version'][:50]}...")
    
    # Show status
    info = manager.get_database_info()
    print(f"\nDatabase Status:")
    print(f"  Current: {info['current_database']}")
    print(f"  Using fallback: {info['using_fallback']}")
    print(f"  Primary available: {info['primary_available']}")
    print(f"  Fallback available: {info['fallback_available']}")
    
    # Close all
    manager.close_all()
    print("\n✅ Test completed successfully!")
