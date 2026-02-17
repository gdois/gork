# Pull Request: Add !twitter command to download videos and images from X/Twitter

## Descrição

Adiciona um novo comando `!twitter` que permite baixar e enviar vídeos ou imagens do X/Twitter diretamente pelo WhatsApp.

## Como usar

```
!twitter https://x.com/usuario/status/12345
```

ou

```
!twitter https://twitter.com/usuario/status/12345
```

**O comando detecta automaticamente se o post contém um vídeo ou uma imagem e envia a mídia apropriada!**

## O que foi implementado

### 1. Novo módulo: `twitter_video.py`

Localização: `api/routes/webhook/evolution/functions/twitter_video.py`

Funções criadas:
- `extract_twitter_url(text: str)`: Extrai URLs do Twitter/X de um texto usando regex
- `download_twitter_media(twitter_url: str)`: Baixa mídia (vídeo ou imagem) usando o serviço twitsave.com

Funcionalidades:
- Suporta URLs de twitter.com e x.com
- **Detecta automaticamente se é vídeo ou imagem**
- Validação de URL
- Timeout de 30 segundos
- Tratamento de erros completo
- Retorna tupla (media_bytes, media_type, error_message)
- media_type pode ser "video" ou "image"

### 2. Função `send_video` no Evolution API

Localização: `external/evolution/image.py`

Nova função `send_video(contact_id, video_base64, quoted_message_id=None)`:
- Envia vídeos em formato MP4 via WhatsApp
- Suporta quoted_message_id para responder mensagens
- Usa mediatype: "video"
- Mimetype: "video/mp4"

### 3. Handler do comando `!twitter`

Localização: `api/routes/webhook/evolution/handles.py`

Função `handle_twitter_command(remote_id, conversation, message_id)`:
1. Extrai o URL do Twitter/X da mensagem
2. Envia mensagem "Baixando a mídia..."
3. Baixa a mídia usando `download_twitter_media`
4. Detecta o tipo de mídia (vídeo ou imagem)
5. Converte para base64
6. Envia via `send_video` (se vídeo) ou `send_image` (se imagem)
7. Envia mensagem de confirmação

Tratamento de erros:
- URL inválido ou não encontrado
- Erro de download
- Timeout
- Falha ao baixar
- Mídia não encontrada (nem vídeo nem imagem)

### 4. Atualização da lista de comandos

Localização: `api/routes/webhook/evolution/handles.py`

- Adicionado `!twitter` à lista `COMMANDS`
- Categoria: "media"
- Descrição: "Baixa vídeos ou imagens de links do X/Twitter e envia. _[Ex: !twitter https://x.com/usuario/status/12345]_"
- Criada nova categoria "📹 MÍDIA" no help

### 5. Atualização do processador de comandos

Localização: `api/routes/webhook/evolution/processors.py`

- Adicionada verificação de `!twitter` em `process_explicit_commands`
- Importa `handle_twitter_command` dos handlers

## Dependências

- `beautifulsoup4` (já estava nas dependências)
- `httpx` (já estava nas dependências)
- `twitsave.com` (serviço externo para download de vídeos e imagens)

## Arquivos modificados

```
api/routes/webhook/evolution/functions/__init__.py |  1 +
api/routes/webhook/evolution/functions/twitter_video.py   | 59 ++++++++++++++++++++
api/routes/webhook/evolution/handles.py            | 64 +++++++++++++++++++++-
api/routes/webhook/evolution/processors.py         |  7 ++-
external/evolution/__init__.py                     |  2 +-
external/evolution/image.py                        | 31 ++++++++++-
6 files changed, 158 insertions(+), 6 deletions(-)
```

## Como criar o Pull Request

### Opção 1: Via GitHub CLI (se estiver instalado)

```bash
# Criar fork do repositório
gh repo fork pedrohgoncalvess/gork --remote-name upstream

# Adicionar seu fork como remote
git remote add fork https://github.com/SEU_USERNAME/gork.git

# Fazer push para seu fork
git push fork master

# Criar PR
gh pr create --repo pedrohgoncalvess/gork --title "feat: Add !twitter command to download videos from X/Twitter" --body "Veja o arquivo TWITTER_COMMAND_PR.md para detalhes."
```

### Opção 2: Manualmente

1. Vá para https://github.com/pedrohgoncalvess/gork
2. Clique em "Fork" no canto superior direito
3. Clone seu fork:
   ```bash
   git clone https://github.com/SEU_USERNAME/gork.git
   cd gork
   ```
4. Adicione o remote original:
   ```bash
   git remote add upstream https://github.com/pedrohgoncalvess/gork.git
   ```
5. Mescle as mudanças do workspace para seu fork:
   ```bash
   git remote add workspace /home/homolog/.openclaw/workspace/gork
   git fetch workspace
   git merge workspace/master
   ```
6. Push para seu fork:
   ```bash
   git push origin master
   ```
7. Vá para https://github.com/pedrohgoncalvess/gork e clique em "Pull requests"
8. Clique em "New pull request"
9. Selecione "Compare across forks"
10. Escolha seu fork e branch master
11. Preencha título e descrição (usando TWITTER_COMMAND_PR.md)
12. Clique em "Create pull request"

## Testes sugeridos

1. Comando sem URL:
   ```
   !twitter
   ```
   Esperado: mensagem de erro pedindo URL válido

2. URL inválida:
   ```
   !twitter https://google.com
   ```
   Esperado: mensagem de erro indicando URL inválido

3. URL válido do X/Twitter com vídeo:
   ```
   !twitter https://x.com/usuario/status/12345
   ```
   Esperado: vídeo baixado e enviado

4. URL válido do X/Twitter com imagem:
   ```
   !twitter https://x.com/usuario/status/67890
   ```
   Esperado: imagem baixada e enviada

5. Verificar se o vídeo aparece no WhatsApp com qualidade aceitável
6. Verificar se a imagem aparece no WhatsApp com qualidade aceitável

## Possíveis melhorias futuras

- Adicionar suporte para escolher qualidade do vídeo
- Suportar downloads de múltiplos vídeos de uma thread
- Adicionar cache para evitar downloads repetidos da mesma mídia
- Adicionar opção para enviar como GIF (se o vídeo for curto)
- Suportar download de GIFs do Twitter/X
- Adicionar opção para baixar legendas/subtitles
