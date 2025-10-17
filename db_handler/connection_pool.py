import boto3
import threading
from typing import List, Optional
from queue import Queue, Empty
import logging

logger = logging.getLogger(__name__)

class DynamoPool:
    def __init__(self, region: str, pool_size: int = 10):
        self.region = region
        self.pool_size = pool_size
        self.pool: Queue = Queue(maxsize=pool_size)
        self.lock = threading.Lock()
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool with DynamoDB resources"""
        for _ in range(self.pool_size):
            resource = boto3.resource('dynamodb', region_name=self.region)
            self.pool.put(resource)
        logger.info(f"Initialized DynamoDB pool with {self.pool_size} connections")
    
    def get_connection(self):
        """Get a connection from the pool"""
        try:
            return self.pool.get(timeout=5)
        except Empty:
            logger.warning("Pool exhausted, creating new connection")
            return boto3.resource('dynamodb', region_name=self.region)
    
    def return_connection(self, connection):
        """Return connection to pool"""
        try:
            self.pool.put_nowait(connection)
        except:
            pass  # Pool is full, connection will be garbage collected

    def close_all(self):
        """Close all connections in pool"""
        while not self.pool.empty():
            try:
                self.pool.get_nowait()
            except Empty:
                break
        logger.info("Closed all pool connections")