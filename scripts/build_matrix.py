#!/usr/bin/env python3
"""Generate the CLI/form/validation/state/test mapping from the registry."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def matrix():
    catalog = json.loads((ROOT / "operations.json").read_text())
    pt = json.loads((ROOT / "i18n/pt-BR.json").read_text())
    lines = ["# Matriz CLI / interface — Mullvad 2026.5", "", "Cada linha corresponde a um formulário registrado. A árvore de navegação (seção e operação) abre os campos indicados; comandos avançados têm formulários, sem console de comandos. Todos os parâmetros passam por `backend.arguments`; as respostas de leitura passam por `backend.parse_output`.", "", "A referência inglesa de cada comando fica na aba **Ajuda do CLI**, e o formulário mostra o comando equivalente com credenciais mascaradas. `--help`/`-h` e `--version`/`-V` são opções informativas globais: ajuda no formulário e versão em manutenção. `status --json` é aplicado pelo adaptador. `--assume-yes` e `--confirm` são internos e só aparecem depois da confirmação gráfica. Os aliases curtos e longos são equivalentes; o adaptador usa os longos.", "", "| Comando | Seção / formulário | Campos e validação | Leitura do daemon | Teste |", "|---|---|---|---|---|"]
    for op in catalog:
        fields = []
        for field in op["fields"]:
            name = field.get("flag", field["name"])
            if field.get("stdin"): name += " (stdin)"
            spec = field["kind"]
            if field.get("choices"): spec += ": " + ", ".join(field["choices"])
            if "minimum" in field: spec += f" {field['minimum']}–{field['maximum']}"
            if field.get("allow_any"): spec += " / any"
            if field.get("many"): spec += " (lista)"
            if field.get("secret"): spec += " (sigiloso)"
            if field.get("required"): spec += " *"
            fields.append(f"`{name}`: {spec}")
        cmd = "mullvad-exclude" if op["id"] == "split.launch" else "mullvad " + " ".join(op["argv"])
        lines.append(f"| `{cmd}` | {pt['section.' + op['section']]} / {pt[op['label']]} | {'; '.join(fields) or 'Sem campos'} | `{op['state']}` + settings JSON | `test_all_operation_arguments`, QML mock |")
    lines += ["", "## Contratos e limites", "", "- [Arquitetura e segurança](arquitetura.md): envelopes JSONL, validação, erros, versões, parsers e armazenamento.", "- `test_known_argument_contracts` verifica argumentos sensíveis, opcionais e variádicos por exemplos independentes; `test_all_finite_operations_execute` percorre cada operação finita com CLI simulado.", "- O teste QML percorre e submete os 88 formulários em quatro combinações (inglês/pt-BR × escuro/claro), verifica confirmação e limpeza dos campos sigilosos. Leituras, snapshots e streams têm testes de processo separados.", "- `test_custom_wireguard_private_key_only_uses_stdin` verifica a entrada que não aparece em `--help`: a chave privada do servidor próprio é enviada por stdin.", "- Nomes de cifras Shadowsocks são validados sintaticamente e pelo CLI; o formulário aceita todos os nomes suportados pela versão instalada, sem restringir a três cifras comuns.", "- [Checklist manual](validacao-manual.md): todas as mutações reais permanecem pendentes; a cobertura automatizada usa um CLI simulado.", ""]
    lines.insert(-1, "- A leitura compartilhada `export-settings -` apresenta configurações completas em JSON, com segredos ocultos e sem gravar arquivo. Ela complementa campos omitidos pelos getters textuais, como DAITA direto e userspace. O CLI não oferece getter do nível/filtro de logs; esses valores não são apresentados como conhecidos.")
    return "\n".join(lines)


if __name__ == "__main__":
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs/matriz-cli.md").write_text(matrix())
