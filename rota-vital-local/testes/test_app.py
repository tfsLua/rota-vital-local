import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from app import lambda_handler  # noqa: E402


def test_gera_guia():
    resposta = lambda_handler({"body": json.dumps({"requisicaoId": "R-001"})})
    assert resposta["statusCode"] == 201
    assert json.loads(resposta["body"])["guia"] == "G-R-001"


def test_campo_obrigatorio():
    resposta = lambda_handler({"body": "{}"})
    assert resposta["statusCode"] == 400
