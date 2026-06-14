import time
import logging
from collections import defaultdict
from threading import Lock
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('django.security')

# ─── Rate Limiter simples em memória ────────────────────────────────────────
_rate_data = defaultdict(list)
_rate_lock = Lock()

RATE_LIMIT_RULES = {
    '/login/':    (10, 60),   # 10 tentativas por 60 s
    '/cadastro/': (5,  300),  # 5 cadastros por 5 min
}


def _get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


class RateLimitMiddleware(MiddlewareMixin):
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
                        logger.warning(f'Rate limit atingido: {ip} em {path}')
                        return HttpResponse(
                            'Muitas tentativas. Aguarde alguns minutos.',
                            content_type='text/plain; charset=utf-8'
                        )
        return None


# ─── Headers de segurança adicionais ────────────────────────────────────────
class SecurityHeadersMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "frame-ancestors 'none';"
        )
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        # Remove header que revela tecnologia
        if 'X-Powered-By' in response:
            del response['X-Powered-By']
        return response
