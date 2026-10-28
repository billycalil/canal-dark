# Canal "Histórias do Livro de Mórmon": rotina diária

Cada execução produz **2 Shorts** e os agenda no Metricool.

## Passo a passo

1. **Escolher 2 passagens novas.** Consulte `historico.json` e nunca repita uma referência. Prefira a ordem da fila abaixo; quando ela acabar, escolha outras histórias marcantes. Proporção: cerca de 3 do Livro de Mórmon para 1 da Bíblia.
2. **Conferir os fatos.** Antes de escrever, confirme na escritura (busca na web, ex.: churchofjesuschrist.org/study ou uma Bíblia online) quem fez o quê, em que capítulo e versículos. Não invente detalhes. Se tiver dúvida sobre um fato, deixe-o de fora.
3. **Escrever o roteiro** em `roteiros/AAAA-MM-DD-<tema>.json`, no formato do exemplo `roteiros/2026-10-28-jovens-guerreiros.json`:
   - 6 a 8 segmentos de 8 a 16 palavras, com a história contada com suas próprias palavras (não copie o texto das traduções oficiais; no máximo uma frase curta entre aspas).
   - O primeiro segmento é o gancho (`"gancho": true`): uma frase de impacto que gere curiosidade.
   - `aplicacao`: uma frase curta de aplicação para a vida, em tom reverente e esperançoso.
   - `cena` de cada segmento: `deserto`, `noite`, `arco`, `arco_quebrado`, `aurora`, `mar`, `cidade`, `fogo`, `oracao`, `luz`, `multidao`, `exercito`, `arvore`. Escolha a que combina com o momento da história.
   - Título com até 70 caracteres terminando em `#shorts`; descrição com 1 a 2 frases, a referência, um convite para comentar e 4 a 5 hashtags.
   - Tom: devocional e narrativo, respeitoso, sem criticar outras religiões, sem afirmar vínculo oficial com a Igreja.
4. **Gerar o vídeo:** `pip install --break-system-packages numpy pillow` (se faltar) e
   `python3 gerador.py roteiros/<arquivo>.json videos/<arquivo>.mp4` (de 25 a 75 s; o script recusa fora disso).
5. **Olhar alguns quadros** do vídeo para conferir se o texto cabe na tela e a cena faz sentido.
6. **Registrar** os 2 vídeos em `historico.json`, fazer commit e push para `main`.
7. **Agendar no Metricool** (marca `7718121`, rede `youtube`, tipo `short`, `madeForKids: false`, `privacy: public`, `category: EDUCATION`):
   - mídia: `https://raw.githubusercontent.com/billycalil/canal-dark/main/videos/<arquivo>.mp4`
   - horários (America/Sao_Paulo): primeiro vídeo às **12:00**, segundo às **19:00** do mesmo dia.
   - `autoPublish: false`: o Billy recebe a notificação no app do Metricool e publica com um toque.
8. **Avisar o Billy** com os dois títulos, as referências e os horários agendados.

## Fila de histórias

Livro de Mórmon:
- O Irmão de Jarede e as pedras iluminadas (Éter 3)
- Abinádi diante do rei Noé (Mosias 11–17)
- Samuel, o lamanita, sobre a muralha (Helamã 13–16)
- A visita de Cristo às Américas (3 Néfi 11)
- A conversão de Alma, o filho (Mosias 27)
- A árvore da vida (1 Néfi 8)
- A Liahona (1 Néfi 16; Alma 37)
- Amon defende os rebanhos do rei Lamôni (Alma 17–18)
- O rei Benjamim e o discurso na torre (Mosias 2)
- Néfi e as placas de latão (1 Néfi 3–4)
- Os barcos dos jareditas atravessando o mar (Éter 2 e 6)
- O capitão Morôni e o estandarte da liberdade (Alma 46)
- Enos ora o dia inteiro (Enos 1)
- Alma e Amuleque na prisão (Alma 14)
- Cristo abençoa as crianças (3 Néfi 17)

Bíblia:
- Davi e Golias (1 Samuel 17)
- Daniel na cova dos leões (Daniel 6)
- Sadraque, Mesaque e Abede-Nego na fornalha (Daniel 3)
- Moisés e o Mar Vermelho (Êxodo 14)
- Pedro anda sobre as águas (Mateus 14)
- O filho pródigo (Lucas 15)
- José do Egito perdoa os irmãos (Gênesis 45)
- Ester diante do rei (Ester 4–5)
