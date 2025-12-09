"""
Rate Limiting Middleware
Implementação simples usando contadores em memória (para produção, usar Redis)
"""
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time


class RateLimiter:
    """Gerenciador de rate limiting"""
    
    def __init__(self):
        # Em produção, usar Redis
        self._counters: Dict[str, list] = defaultdict(list)
        self._cleanup_interval = 300  # Limpa a cada 5 minutos
        self._last_cleanup = time.time()
    
    def _cleanup_old_entries(self):
        """Remove entradas antigas"""
        current_time = time.time()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
        
        cutoff = current_time - 3600  # Remove entradas com mais de 1 hora
        for key in list(self._counters.keys()):
            self._counters[key] = [
                timestamp for timestamp in self._counters[key]
                if timestamp > cutoff
            ]
            if not self._counters[key]:
                del self._counters[key]
        
        self._last_cleanup = current_time
    
    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int]:
        """
        Verifica se o limite foi excedido
        
        Args:
            key: Chave única (ex: user_id, ip)
            max_requests: Número máximo de requisições
            window_seconds: Janela de tempo em segundos
        
        Returns:
            (allowed, remaining)
        """
        self._cleanup_old_entries()
        
        current_time = time.time()
        cutoff = current_time - window_seconds
        
        # Remove requisições antigas
        self._counters[key] = [
            timestamp for timestamp in self._counters[key]
            if timestamp > cutoff
        ]
        
        # Conta requisições na janela
        count = len(self._counters[key])
        
        if count >= max_requests:
            return False, 0
        
        # Adiciona requisição atual
        self._counters[key].append(current_time)
        
        remaining = max_requests - count - 1
        return True, remaining


# Instância global
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Obtém instância do rate limiter"""
    return _rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware de rate limiting"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.rate_limiter = get_rate_limiter()
    
    async def dispatch(self, request: Request, call_next):
        # Ignora health check e docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json", "/"]:
            return await call_next(request)
        
        # Obtém chave (IP ou user_id se autenticado)
        key = request.client.host if request.client else "unknown"
        
        # Se autenticado, usa user_id
        # (precisa extrair do token, mas por simplicidade usa IP)
        
        # Verifica rate limit
        allowed, remaining = self.rate_limiter.check_rate_limit(
            key=key,
            max_requests=self.requests_per_minute,
            window_seconds=60
        )
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas requisições. Tente novamente em alguns instantes.",
                headers={"Retry-After": "60"}
            )
        
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response


def setup_rate_limiting(app, requests_per_minute: int = 60):
    """Configura rate limiting na aplicação"""
    app.add_middleware(RateLimitMiddleware, requests_per_minute=requests_per_minute)

