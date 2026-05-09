from fastapi import Request
from slowapi import Limiter


def get_real_ip(request: Request) -> str:
    return request.client.host  # zero trust em headers


limiter = Limiter(key_func=get_real_ip)
