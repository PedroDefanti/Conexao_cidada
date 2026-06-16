import time
import logging
from collections import defaultdict
from threading import Lock
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('django.security')

# ─── Rate Limiter ─────────────────────────────────────────────────────────────
# Em produção com múltiplos workers, troque por django-ratelimit + Redis.
# Exemplo com Redis:
#   pip install django-ratelimit
#   @ratelimit(key='ip', rate='10/m', method='POST', block=True)
#
# A implementação abaixo é segura para desenvolvimento e ambientes single-worker.
_rate_data: dict = defaultdict(list)
_rate_lock = Lock()

RATE_LIMIT_RULES = {
    '/login/':    (10, 60),   # 10 tentativas por 60 s
    '/cadastro/': (5,  300),  # 5 cadastros por 5 min
}


def _get_client_ip(request) -> str:
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiter em memória (por processo).

    ATENÇÃO: em produção com gunicorn/uvicorn e múltiplos workers,
    cada processo mantém seu próprio estado. Para rate-limiting global,
    utilize django-ratelimit com backend Redis:

        RATELIMIT_USE_CACHE = 'default'  # aponta para Redis no settings.py
    """

    def process_request(self, request):
        if request.method != 'POST':
            return None

        for path, (limit, window) in RATE_LIMIT_RULES.items():
            if request.path.startswith(path):
                ip = _get_client_ip(request)
                key = f'{ip}:{path}'
                now = time.time()
                with _rate_lock:
                    timestamps = [t for t in _rate_data[key] if now - t < window]
                    timestamps.append(now)
                    _rate_data[key] = timestamps
                    if len(timestamps) > limit:
                        logger.warning(
                            f'Rate limit atingido: {ip} em {path} '
                            f'({len(timestamps)} tentativas em {window}s)'
                        )
                        return HttpResponse(
                            'Muitas tentativas. Aguarde alguns minutos e tente novamente.',
                            status=429,
                            content_type='text/plain; charset=utf-8',
                        )
        return None


# ─── Headers de segurança ─────────────────────────────────────────────────────
class SecurityHeadersMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; "
            "frame-ancestors 'none';"
        )
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        response.headers.pop('X-Powered-By', None)
        return response