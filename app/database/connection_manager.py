"""
Database Connection Manager - Manages database connections and query execution.
"""

import aiomysql
import time
from typing import Dict, Any, List, Optional
from app.core.logging import logger


class DatabaseConnectionManager:
    """Manages database connection pools and query execution"""
    
    def __init__(self):
        """Initialize connection manager"""
        self.pools: Dict[str, aiomysql.Pool] = {}
        self.schema_cache: Dict[str, Dict[str, Any]] = {}
        self.schema_cache_ttl = 3600  # 1 hour
        self.query_timeout = 30  # 30 seconds
    
    def configure_database(
        self,
        database: str,
        host: str,
        port: int,
        database_name: str,
        user: str,
        password: str
    ):
        """
        Configure database connection parameters
        
        Args:
            database: Database identifier (e.g., 'sales', 'inventory')
            host: Database host
            port: Database port
            database_name: Database name
            user: Database user
            password: Database password
        """
        # Store config for lazy connection
        if not hasattr(self, '_configs'):
            self._configs = {}
        
        self._configs[database] = {
            'host': host,
            'port': port,
            'database': database_name,
            'user': user,
            'password': password
        }
        
        logger.info_structured(
            "Database configured",
            database=database,
            host=host,
            port=port
        )
    
    async def get_connection_pool(self, database: str) -> aiomysql.Pool:
        """
        Get or create connection pool for database
        
        Args:
            database: Database identifier
            
        Returns:
            Connection pool
        """
        if database in self.pools:
            return self.pools[database]
        
        # Get config
        if not hasattr(self, '_configs') or database not in self._configs:
            raise ValueError(f"Database '{database}' not configured")
        
        config = self._configs[database]
        
        # Create connection pool
        try:
            pool = await aiomysql.create_pool(
                host=config['host'],
                port=config['port'],
                db=config['database'],
                user=config['user'],
                password=config['password'],
                minsize=2,
                maxsize=10,
                autocommit=False
            )
            
            self.pools[database] = pool
            
            logger.info_structured(
                "Database connection pool created",
                database=database
            )
            
            return pool
            
        except Exception as e:
            logger.error_structured(
                "Failed to create database connection pool",
                database=database,
                error=str(e)
            )
            raise
    
    async def execute_query(
        self,
        database: str,
        sql: str,
        params: Optional[List[Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute SQL query with parameters
        
        Args:
            database: Database identifier
            sql: SQL query
            params: Query parameters (list)
            
        Returns:
            List of result rows as dictionaries
        """
        pool = await self.get_connection_pool(database)
        
        try:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # Set read-only session
                    await cursor.execute("SET SESSION TRANSACTION READ ONLY")
                    
                    # Execute query
                    if params:
                        await cursor.execute(sql, params)
                    else:
                        await cursor.execute(sql)
                    
                    # Fetch results
                    rows = await cursor.fetchall()
                    results = list(rows)
                
                logger.info_structured(
                    "Query executed successfully",
                    database=database,
                    row_count=len(results)
                )
                
                return results
                
            
        except Exception as e:
            logger.error_structured(
                "Query execution failed",
                database=database,
                error=str(e)
            )
            raise
    
    async def get_schema(self, database: str) -> Dict[str, Any]:
        """
        Get database schema metadata with caching
        
        Args:
            database: Database identifier
            
        Returns:
            Schema metadata dictionary
        """
        cache_key = f"schema_{database}"
        
        # Check cache
        if cache_key in self.schema_cache:
            cached = self.schema_cache[cache_key]
            if time.time() - cached["timestamp"] < self.schema_cache_ttl:
                logger.debug(f"Returning cached schema for {database}")
                return cached["schema"]
        
        # Fetch schema
        schema = await self._fetch_schema(database)
        
        # Cache it
        self.schema_cache[cache_key] = {
            "schema": schema,
            "timestamp": time.time()
        }
        
        logger.info_structured(
            "Schema fetched and cached",
            database=database,
            table_count=len(schema.get('tables', {}))
        )
        
        return schema
    
    async def _fetch_schema(self, database: str) -> Dict[str, Any]:
        """
        Fetch database schema from information_schema
        
        Args:
            database: Database identifier
            
        Returns:
            Schema metadata
        """
        pool = await self.get_connection_pool(database)
        
        try:
            async with pool.acquire() as conn:
                # Get tables and columns
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    tables_query = """
                        SELECT 
                            table_name,
                            column_name,
                            data_type,
                            is_nullable
                        FROM information_schema.columns
                        WHERE table_schema = DATABASE()
                        ORDER BY table_name, ordinal_position
                    """
                    
                    await cursor.execute(tables_query)
                    rows = await cursor.fetchall()
                
                logger.info_structured(
                    "Fetched schema rows",
                    database=database,
                    row_count=len(rows)
                )
                
                # Organize by table
                tables = {}
                for row in rows:
                    # Handle both dict and tuple results
                    if isinstance(row, dict):
                        table_name = row.get('table_name') or row.get('TABLE_NAME')
                    else:
                        table_name = row[0]  # First column is table_name
                    if table_name not in tables:
                        tables[table_name] = {
                            'columns': [],
                            'foreign_keys': []
                        }
                    
                    # Extract column info handling both dict and tuple
                    if isinstance(row, dict):
                        col_name = row.get('column_name') or row.get('COLUMN_NAME')
                        col_type = row.get('data_type') or row.get('DATA_TYPE')
                        col_nullable = row.get('is_nullable') or row.get('IS_NULLABLE')
                    else:
                        col_name = row[1]  # column_name
                        col_type = row[2]  # data_type
                        col_nullable = row[3]  # is_nullable
                    
                    tables[table_name]['columns'].append({
                        'name': col_name,
                        'type': col_type,
                        'nullable': col_nullable == 'YES'
                    })
                
                # Get foreign keys with a new cursor
                async with conn.cursor(aiomysql.DictCursor) as fk_cursor:
                    fk_query = """
                        SELECT
                            tc.table_name,
                            kcu.column_name,
                            kcu.referenced_table_name AS foreign_table_name,
                            kcu.referenced_column_name AS foreign_column_name
                        FROM information_schema.table_constraints AS tc
                        JOIN information_schema.key_column_usage AS kcu
                            ON tc.constraint_name = kcu.constraint_name
                            AND tc.table_schema = kcu.table_schema
                        WHERE tc.constraint_type = 'FOREIGN KEY'
                            AND tc.table_schema = DATABASE()
                    """
                    
                    await fk_cursor.execute(fk_query)
                    fk_rows = await fk_cursor.fetchall()
                
                for row in fk_rows:
                    # Handle both dict and tuple formats
                    if isinstance(row, dict):
                        table_name = row.get('table_name') or row.get('TABLE_NAME')
                        col_name = row.get('column_name') or row.get('COLUMN_NAME')
                        foreign_table = row.get('foreign_table_name') or row.get('FOREIGN_TABLE_NAME')
                        foreign_col = row.get('foreign_column_name') or row.get('FOREIGN_COLUMN_NAME')
                    else:
                        table_name = row[0]
                        col_name = row[1]
                        foreign_table = row[2]
                        foreign_col = row[3]
                    
                    if table_name in tables:
                        tables[table_name]['foreign_keys'].append({
                            'column': col_name,
                            'references': f"{foreign_table}.{foreign_col}"
                        })
                
                return {
                    'database': database,
                    'tables': tables
                }
                
        except Exception as e:
            logger.error_structured(
                "Failed to fetch schema",
                database=database,
                error=str(e)
            )
            # Return empty schema on error
            return {
                'database': database,
                'tables': {}
            }
    
    async def close_all(self):
        """Close all connection pools"""
        for database, pool in self.pools.items():
            try:
                await pool.close()
                logger.info_structured(
                    "Connection pool closed",
                    database=database
                )
            except Exception as e:
                logger.error_structured(
                    "Error closing connection pool",
                    database=database,
                    error=str(e)
                )
        
        self.pools.clear()
