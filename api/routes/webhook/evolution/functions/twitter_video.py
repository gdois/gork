import re
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def extract_twitter_url(text: str) -> str | None:
    """Extrai o primeiro URL do Twitter/X de um texto."""
    pattern = r'https?://(twitter|x)\.com/[^\s]+'
    match = re.search(pattern, text)
    return match.group(0) if match else None


async def download_twitter_media(twitter_url: str) -> tuple[bytes | None, str, str | None]:
    """
    Baixa mídia (vídeo ou imagem) do Twitter/X usando twitsave.com

    Returns:
        tuple: (media_bytes, media_type, error_message)
                media_type: "video" ou "image"
    """
    try:
        # Verifica se o URL é válido
        parsed = urlparse(twitter_url)
        if not parsed.netloc in ['twitter.com', 'x.com']:
            return None, "", "URL inválido. Deve ser do twitter.com ou x.com"

        # Usa twitsave.com para baixar
        api_url = "https://twitsave.com/info"

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Primeiro, obtém informações da mídia
            response = await client.post(api_url, data={"url": twitter_url})
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Procura por vídeo primeiro
            video_element = soup.find('a', {'class': 'twitsave-btn'})

            if video_element:
                media_url = video_element.get('href')
                if media_url:
                    # Baixa o vídeo
                    video_response = await client.get(media_url)
                    video_response.raise_for_status()
                    return video_response.content, "video", None

            # Se não encontrou vídeo, procura por imagem
            image_element = soup.find('img', {'class': 'twitsave-img'})
            if image_element:
                media_url = image_element.get('src')
                if media_url:
                    # Baixa a imagem
                    image_response = await client.get(media_url)
                    image_response.raise_for_status()
                    return image_response.content, "image", None

            return None, "", "Não foi possível encontrar mídia (vídeo ou imagem) no post"

    except httpx.TimeoutException:
        return None, "", "Timeout ao baixar a mídia. Tente novamente."
    except httpx.HTTPStatusError as e:
        return None, "", f"Erro HTTP ao baixar mídia: {e.response.status_code}"
    except Exception as e:
        return None, "", f"Erro ao baixar mídia: {str(e)}"
