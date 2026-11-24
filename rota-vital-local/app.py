#!/usr/bin/env python3
"""
ATIVIDADE INDIVIDUAL 1 — SERVERLESS
Infraestrutura de Software · ADS · CESAR School · 2026.2

Projeto 100% local para a função HTTP do Rota Vital.
Não precisa de AWS, SAM CLI, Docker, conta ou cartão.

O que este ficheiro contém:
  1. Função de processamento: lambda_handler(event, context)
  2. Endpoint HTTP local: POST /guias
  3. Invocação por evento em formato semelhante a API Gateway
  4. Contador global para observar reaproveitamento do ambiente
  5. Validação de requisicaoId
  6. Simulação de timeout com demorar=true
  7. Testes automáticos (--test)
  8. Respostas às perguntas da atividade e guião do vídeo

COMO EXECUTAR
-------------
1) Verificar a função e os testes:

    python3 rota_vital_serverless.py --test

2) Invocar como evento Lambda:

    python3 rota_vital_serverless.py --invoke
    python3 rota_vital_serverless.py --invoke

3) Iniciar o endpoint HTTP local:

    python3 rota_vital_serverless.py --serve

   Noutro terminal, chamar três vezes:

    curl -i -X POST http://127.0.0.1:3000/guias \
      -H 'Content-Type: application/json' \
      -d '{"requisicaoId":"R-002","hospital":"H-Caruaru","bolsas":["A-POS-0101"]}'

4) Testar erro de campo obrigatório:

    curl -i -X POST http://127.0.0.1:3000/guias \
      -H 'Content-Type: application/json' \
      -d '{"hospital":"H-Recife"}'

5) Testar timeout. O limite local deste ficheiro é de 3 segundos; o pedido
   solicita 5 segundos para demonstrar o erro:

    python3 rota_vital_serverless.py --timeout

OBSERVAÇÃO SOBRE O CONTADOR
---------------------------
O contador é uma variável global. Ele pode aumentar quando o mesmo processo
é reutilizado, mas volta a zero quando o processo é reiniciado. Portanto, não
é armazenamento persistente nem deve guardar dados importantes do sistema.

USO DE IA
---------
A implementação/revisão teve apoio de IA. O estudante deve executar, conferir,
compreender e adaptar o código, os tempos e as respostas antes da entrega.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

# Estado global utilizado apenas para demonstrar o reaproveitamento do ambiente.
contador = 0
TIMEOUT_SEGUNDOS = 3


def _resposta(status_code: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Cria uma resposta no formato esperado pelo API Gateway/Lambda."""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload, ensure_ascii=False),
    }


def lambda_handler(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    """Função serverless que gera uma guia de transporte do Rota Vital."""
    global contador
    contador += 1

    try:
        body = event.get("body") or "{}"
        pedido = json.loads(body) if isinstance(body, str) else body
    except (TypeError, json.JSONDecodeError):
        return _resposta(400, {"erro": "body deve ser um JSON válido"})

    if not isinstance(pedido, dict):
        return _resposta(400, {"erro": "body deve ser um objeto JSON"})

    if "requisicaoId" not in pedido or not pedido["requisicaoId"]:
        return _resposta(400, {"erro": "requisicaoId obrigatório"})

    # Demonstração do limite de tempo: excede TIMEOUT_SEGUNDOS.
    if pedido.get("demorar"):
        time.sleep(5)

    guia = {
        "guia": "G-" + str(pedido["requisicaoId"]),
        "hospital": pedido.get("hospital"),
        "bolsas": pedido.get("bolsas", []),
        "invocacaoNesteAmbiente": contador,
    }
    return _resposta(201, guia)


def _evento(pedido: dict[str, Any]) -> dict[str, Any]:
    """Converte um pedido em evento semelhante ao recebido pelo API Gateway."""
    return {
        "resource": "/guias",
        "path": "/guias",
        "httpMethod": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(pedido, ensure_ascii=False),
        "isBase64Encoded": False,
    }


class RotaVitalHTTPHandler(BaseHTTPRequestHandler):
    """Adaptador HTTP local para chamar o mesmo lambda_handler."""

    def do_POST(self) -> None:  # noqa: N802 - nome exigido pelo BaseHTTPRequestHandler
        if self.path != "/guias":
            self._responder(404, {"erro": "rota não encontrada"})
            return

        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(tamanho).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            self._responder(400, {"erro": "corpo da requisição inválido"})
            return

        resultado = lambda_handler({"httpMethod": "POST", "path": "/guias", "body": body})
        self._responder(resultado["statusCode"], json.loads(resultado["body"]))

    def _responder(self, status: int, payload: dict[str, Any]) -> None:
        dados = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def log_message(self, formato: str, *args: Any) -> None:
        print("[HTTP] " + formato % args)


def iniciar_servidor(porta: int = 3000) -> None:
    servidor = ThreadingHTTPServer(("127.0.0.1", porta), RotaVitalHTTPHandler)
    print(f"Servidor ativo em http://127.0.0.1:{porta}/guias")
    print("Prima Ctrl+C para parar.")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
    finally:
        servidor.server_close()


def executar_testes() -> None:
    """Executa testes essenciais sem dependências externas."""
    global contador
    contador = 0

    resultado = lambda_handler(_evento({"requisicaoId": "R-TEST", "hospital": "H-Recife"}))
    assert resultado["statusCode"] == 201
    payload = json.loads(resultado["body"])
    assert payload["guia"] == "G-R-TEST"
    assert payload["hospital"] == "H-Recife"
    assert payload["invocacaoNesteAmbiente"] == 1

    resultado = lambda_handler(_evento({"requisicaoId": "R-TEST-2"}))
    assert resultado["statusCode"] == 201
    assert json.loads(resultado["body"])["invocacaoNesteAmbiente"] == 2

    resultado = lambda_handler(_evento({"hospital": "H-Recife"}))
    assert resultado["statusCode"] == 400
    assert "requisicaoId" in json.loads(resultado["body"])["erro"]

    resultado = lambda_handler(_evento({"requisicaoId": "R-JSON", "bolsas": []}))
    assert resultado["statusCode"] == 201

    resultado = lambda_handler({"body": "isto não é JSON"})
    assert resultado["statusCode"] == 400

    print("Todos os testes passaram.")


def invocar_exemplo(timeout: bool = False) -> None:
    pedido = {
        "requisicaoId": "R-003" if timeout else "R-001",
        "hospital": "H-Recife",
        "bolsas": ["O-NEG-0142"],
    }
    if timeout:
        pedido["demorar"] = True

    print("Evento enviado:")
    print(json.dumps(_evento(pedido), indent=2, ensure_ascii=False))
    inicio = time.perf_counter()

    if timeout:
        # Simula o timeout configurado no template AWS SAM.
        thread_result: list[dict[str, Any]] = []
        thread = threading.Thread(
            target=lambda: thread_result.append(lambda_handler(_evento(pedido)))
        )
        thread.start()
        thread.join(TIMEOUT_SEGUNDOS)
        if thread.is_alive():
            print(f"ERRO: execução excedeu o timeout de {TIMEOUT_SEGUNDOS} segundos.")
            return
        resultado = thread_result[0]
    else:
        resultado = lambda_handler(_evento(pedido))

    decorrido = time.perf_counter() - inicio
    print(f"Tempo: {decorrido:.3f}s")
    print("Resposta:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))


def mostrar_trabalho() -> None:
    print(
        """
RESPOSTAS PARA O README/ENTREGA

1. A primeira invocação tende a demorar mais porque o ambiente precisa ser
   criado e inicializado. Na fase Init, o runtime Python, o código e os
   módulos da função são carregados. Em chamadas posteriores, o ambiente pode
   ser reutilizado, evitando parte desse trabalho. Registar os tempos reais.

2. invocacaoNesteAmbiente pode aumentar quando o mesmo processo/ambiente é
   reaproveitado. Após reiniciar o processo, volta a zero. Isso prova que uma
   variável global pode sobreviver entre chamadas, mas não há garantia de que
   o ambiente será reutilizado. Não se deve usar variável global como banco de
   dados ou armazenamento persistente.

3. demorar=true faz a função dormir cinco segundos. Como o limite local deste
   exercício é de três segundos, a execução é considerada timeout. No Lambda,
   o limite máximo de uma execução depende do tipo de invocação; para uma
   invocação comum, pode chegar a 15 minutos. Aqui vale o timeout configurado.

4. Custo aproximado usando os valores do enunciado:
   requisição: US$ 0,20 / 1.000.000 = US$ 0,0000002;
   128 MB = 0,125 GB; 0,125 GB x 0,1 s = 0,0125 GB-s;
   execução: 0,0125 x US$ 0,0000166667 = US$ 0,0000002083;
   total aproximado: US$ 0,0000004083 por invocação;
   1.000.000 invocações: aproximadamente US$ 0,4083, antes da franquia.

5. Faz sentido para tarefas curtas e independentes, como validar uma
   requisição, gerar uma guia ou publicar uma notificação. Não é ideal para
   processos longos, conexões persistentes ou tarefas que dependam de estado
   local confiável. Para esses casos, usar fila, worker, banco ou serviço de
   longa duração."""
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Rota Vital — função serverless local")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--test", action="store_true", help="executa os testes")
    grupo.add_argument("--invoke", action="store_true", help="invoca um evento de exemplo")
    grupo.add_argument("--serve", action="store_true", help="inicia POST /guias na porta 3000")
    grupo.add_argument("--timeout", action="store_true", help="demonstra o timeout de 3 segundos")
    grupo.add_argument("--trabalho", action="store_true", help="mostra respostas e guião do vídeo")
    args = parser.parse_args()

    if args.test:
        executar_testes()
    elif args.invoke:
        invocar_exemplo()
    elif args.serve:
        iniciar_servidor()
    elif args.timeout:
        invocar_exemplo(timeout=True)
    elif args.trabalho:
        mostrar_trabalho()


if __name__ == "__main__":
    main()
