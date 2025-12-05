Classifique a intenção do usuário em uma das funções abaixo:

FUNÇÕES:
- remember: Agendar lembretes/avisos (ex: "me avisa", "lembra amanhã", "notifica sobre")
- search: Buscar na internet (ex: "pesquisa", "procura", "busca sobre", "qual é")
- image: Criar/editar imagens (ex: "gera imagem", "cria foto", "desenha", "ilustra")
- sticker: Fazer figurinha/sticker (ex: "cria sticker", "faz figurinha")
- transcribe: Transcrever áudio citado (contexto: respondendo áudio)
- resume: Resumir histórico da conversa (ex: "resume", "o que falamos", "histórico")
- model: Mostrar IA/modelos usados (ex: "qual modelo", "que IA", "versão")
- help: Listar comandos/ajuda (ex: "ajuda", "comandos", "como usar")
- conversation: Conversa genérica/perguntas

MODIFICADORES (combine com vírgula):
- audio: Usuário quer resposta em áudio (ex: "responde em áudio", "manda voz", "fala isso")

Mensagem: "{message}"

REGRAS:
1. Responda APENAS o nome da função
2. Se quer áudio + outra ação: "função,audio" (ex: "search,audio")
3. Se só quer áudio em conversa: "conversation,audio"
4. Na dúvida: "conversation"