import re
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def extract_twitter_url(text: str) -> str | None:
    """Extrai o primeiro URL do Twitter/X de um texto."""
    pattern = r'https?://(twitter|x)\.com/[^\s]+'
    match = re.search(pattern, text)
    return match.group(0) if match else None


async def download_twitter_video(twitter_url: str) -> tuple[bytes | None, str | None]:
    """
    Baixa o vídeo do Twitter/X usando twitsave.com

    Returns:
        tuple: (video_bytes, error_message)
    """
    try:
        # Verifica se o URL é válido
        parsed = urlparse(twitter_url)
        if not parsed.netloc in ['twitter.com', 'x.com']:
            return None, "URL inválido. Deve ser do twitter.com ou x.com"

        # Usa twitsave.com para baixar
        api_url = "https://twitsave.com/info"

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Primeiro, obtém informações do vídeo
            response = await client.post(api_url, data={"url": twitter_url})
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Procura pelo link de download de maior qualidade
            video_element = soup.find('a', {'class': 'twitsave-btn'})

            if not video_element:
                return None, "Não foi possível encontrar o vídeo"

            video_url = video_element.get('href')

            if not video_url:
                return None, "Não foi possível obter o link do vídeo"

            # Baixa o vídeo
            video_response = await client.get(video_url)
            video_response.raise_for_status()

            return video_response.content, None

    except httpx.TimeoutException:
        return None, "Timeout ao baixar o vídeo. Tente novamente."
    except httpx.HTTPStatusError as e:
        return None, f"Erro HTTP ao baixar vídeo: {e.response.status_code}"
    except Exception as e:
        return None, f"Erro ao baixar vídeo: {str(e)}"
