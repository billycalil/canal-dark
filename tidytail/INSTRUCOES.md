# TidyTail Co. (@tidytail.co): rotina diária de Instagram

Loja: TidyTail Co. (Shopify, dropshipping de produtos pet para os EUA). Público: donos de cachorro nos EUA. Todo o conteúdo é em **inglês**.
Cada execução produz **1 post (foto)** e **1 Reels** sobre um produto da loja e agenda os dois no Metricool, com publicação automática.

## Arquivos
- `produtos.json`: produtos da loja (handle, título, preço, link, descrição). As fotos estão em `produtos/<handle>/01.jpg ...`.
- `gerador_tt.py`: gera o post e o Reels a partir de um JSON (veja o cabeçalho do script).
- `historico.json`: o que já foi postado. Não repita o mesmo produto em dias seguidos; faça rodízio pelos 7 produtos, mudando o ângulo (benefício, problema, situação de uso, presente, comparação) quando um produto voltar.
- `posts/AAAA-MM-DD-<tema>.json` + `-post.jpg` + `-reel.mp4`: o material de cada dia.

## Passo a passo
1. Leia `historico.json` e escolha o produto do dia (o que está há mais tempo sem aparecer).
2. Olhe as fotos do produto (monte uma folha de miniaturas e veja). **Não use fotos com textos como "2pcs", "2 pieces" ou quantidades** que não correspondem ao que a loja vende, nem fotos com marcas de outras empresas. Prefira fotos limpas.
3. Escreva `posts/AAAA-MM-DD-<tema>.json`:
   - `post.headline`: até ~8 palavras, gancho de dor ou desejo do dono de cachorro. `post.sub`: nome curto do produto + 1 benefício.
   - `reel.slides`: 4 a 5 slides, texto curto (até ~8 palavras), começando com um gancho forte ("POV:", "Stop doing this...", "Your dog will thank you"). `reel.cta`: "Tap the link in bio" ou parecido.
   - Use só benefícios que estão na descrição do produto em `produtos.json`. Não invente funções, prêmios, avaliações ou números.
4. Gere: `python3 tidytail/gerador_tt.py tidytail/posts/<arquivo>.json` (precisa de ffmpeg e pillow; `pip install --break-system-packages pillow` se faltar). Confira a imagem e 2 quadros do Reels.
5. Registre em `historico.json`, faça commit e push para `main`.
6. Agende no Metricool (marca `7718121`, rede `instagram`, `autoPublish: true`, `isAiGenerated: false`):
   - Post: `instagramData.type = "POST"`, mídia `https://raw.githubusercontent.com/billycalil/canal-dark/main/tidytail/posts/<arquivo>-post.jpg`, às **13:00** (America/Sao_Paulo; 11h na costa leste dos EUA).
   - Reels: `instagramData.type = "REEL"`, `showReelOnFeed: true`, mídia `...-reel.mp4`, às **21:00** (America/Sao_Paulo; 19h na costa leste).
   - Se já passou do horário, use o próximo horário livre do mesmo tipo (no dia seguinte).
   - Legenda (em inglês): 2 a 3 frases sobre o problema e o produto, preço, "Free US shipping", "Shop: link in bio 🐾" e 8 a 12 hashtags (#dogsofinstagram #doggrooming #dogmom #doglife #petproducts #dogshedding ... adequadas ao produto).
7. Avise o Billy (em português) com o produto do dia e os dois horários agendados.

Se algo falhar (push recusado, Metricool sem o Instagram, erro no gerador), não improvise outro jeito de publicar: avise o Billy dizendo exatamente o que falhou.
