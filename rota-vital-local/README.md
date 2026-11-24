# Rota Vital — Serverless 100% local

Este projeto roda no computador usando somente **Python 3** e a biblioteca padrão. Não é necessário usar AWS, AWS SAM CLI, Docker ou conta na nuvem.

## O que foi implementado

A função recebe dados de uma requisição do Rota Vital e devolve uma guia de transporte. Também há um servidor HTTP local, contador de invocações, validação de dados, testes e uma simulação do limite de tempo.

## Pré-requisito

Instale Python 3.10 ou superior. Não há dependências externas nem `pip install`.

Verifique:

```bash
python --version
```

No Linux/macOS, pode ser necessário usar `python3` em vez de `python`.

## 1. Executar os testes

Windows:

```powershell
python app.py --test
```

Linux/macOS:

```bash
python3 app.py --test
```

Saída esperada:

```text
Todos os testes passaram.
```

## 2. Executar uma invocação por evento

```bash
python app.py --invoke
```

Esse comando simula a função recebendo um evento e imprime a guia gerada.

## 3. Executar por HTTP

Abra um terminal na pasta do projeto e execute:

```bash
python app.py --serve
```

Aparecerá:

```text
Servidor ativo em http://127.0.0.1:3000/guias
```

Mantenha esse terminal aberto. Em outro terminal, faça uma chamada.

No Windows PowerShell:

```powershell
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:3000/guias -ContentType 'application/json' -Body '{"requisicaoId":"R-002","hospital":"H-Caruaru","bolsas":["A-POS-0101"]}'
```

Com `curl`:

```bash
curl -i -X POST http://127.0.0.1:3000/guias \
  -H "Content-Type: application/json" \
  -d '{"requisicaoId":"R-002","hospital":"H-Caruaru","bolsas":["A-POS-0101"]}'
```

Faça a chamada três vezes. O campo `invocacaoNesteAmbiente` mostrará que o processo foi reaproveitado.

## 4. Testar o erro de validação

```bash
curl -i -X POST http://127.0.0.1:3000/guias \
  -H "Content-Type: application/json" \
  -d '{"hospital":"H-Recife"}'
```

O resultado esperado é HTTP 400 com `requisicaoId obrigatório`.

## 5. Testar o limite de tempo

```bash
python app.py --timeout
```

O pedido demora cinco segundos, mas o limite demonstrado no projeto é de três segundos. O programa deve informar que a execução excedeu o timeout.

## 6. Ver as respostas e o guião do vídeo

```bash
python app.py --trabalho
```

## 7. Estrutura

```text
rota-vital-local/
├── app.py
├── README.md
├── events/
│   ├── pedido.json
│   ├── sem-requisicao-id.json
│   └── demorar.json
├── testes/
│   └── test_app.py
└── evidencias/
    └── REGISTO.md
```

## Uso de IA

A implementação/revisão teve apoio de IA. O estudante deve executar, conferir, compreender e adaptar o código, os tempos medidos e as respostas antes da entrega.
