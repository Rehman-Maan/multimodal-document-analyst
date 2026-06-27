import ssl

import httpx
from django.conf import settings


def get_openai_client():
    from openai import OpenAI

    ssl_context = ssl.create_default_context()
    if hasattr(ssl, "VERIFY_X509_STRICT"):
        ssl_context.verify_flags &= ~ssl.VERIFY_X509_STRICT
    http_client = httpx.Client(verify=ssl_context, timeout=30)
    try:
        return OpenAI(api_key=settings.OPENAI_API_KEY, http_client=http_client)
    except TypeError:
        http_client.close()
        return OpenAI(api_key=settings.OPENAI_API_KEY)
