# Dank Mullvad VPN

Plugin Linux para **DankMaterialShell 1.6.2 / Quickshell** e **Mullvad CLI 2026.5**.
Oferece widget na DankBar, resumo no popout e uma janela com **88 formulários**,
em inglês e português brasileiro. As configurações da VPN continuam no daemon.

## Instalação

Requisitos: DMS 1.6.2 ou mais recente, Quickshell, Python 3.10+ e Mullvad VPN
2026.5 com `mullvad` e `mullvad-exclude` acessíveis no PATH do processo do DMS.
O daemon Mullvad deve estar ativo e acessível ao usuário. Não há dependências
Python adicionais.

1. Coloque este diretório em
   `~/.config/DankMaterialShell/plugins/DankMullvadVPN`.
2. Abra **Configurações → Plugins** no DMS, atualize a descoberta dos plugins
   e habilite **Dank Mullvad VPN** com as permissões do manifesto.
3. Adicione o widget `DankMullvadVPN` à DankBar nas configurações da barra.

O plugin pode ser habilitado sem reiniciar o DMS. Os testes gráficos usam uma
instância temporária do Quickshell com imports reais do DMS e backend simulado;
não alteram a VPN nem habilitam o plugin na sessão principal.

## Uso

Clique no widget para abrir o resumo e use **Abrir janela completa** para acessar
os formulários. Clique com o botão direito para abrir a janela diretamente.
O resumo fecha ao abrir a janela, inclusive quando uma ação pede confirmação.
O widget também aceita foco por Tab e abertura com Enter/Espaço.
A conexão rápida abre uma confirmação antes de conectar ou desconectar.
O estado e a localização vêm de `status --json`; `status --json listen` acompanha
mudanças e há uma consulta periódica de recuperação.
O painel de configurações completas consulta `export-settings -` por leitura,
oculta credenciais e permite conferir opções ausentes nos getters textuais.

Na janela, a árvore lateral agrupa as funções por seção, com contagem e ícones
de leitura, alteração e acompanhamento contínuo. A busca global filtra pelo nome
traduzido ou pelo comando; ↑/↓ no campo de busca percorrem os resultados. Em
janelas menores, a árvore dá lugar a seletores de seção e operação. O resumo
mostra estado colorido, localização, servidor/IP quando o daemon informa,
reconexão e a ação de conectar/desconectar. **Preferências** abre
idioma e exibição da localização. Os controles usam as cores e componentes do DMS.

`Ctrl+F` foca a busca; `Ctrl+R` atualiza as leituras; `Ctrl+Enter` executa
o formulário atual (alterações continuam exigindo confirmação). Escape limpa uma busca,
fecha as preferências ou fecha a janela. Em uma confirmação, Escape cancela,
e Tab/Shift+Tab circulam entre cancelar e executar. Fechar a janela, inclusive
pelo gerenciador de janelas, cancela a ação pendente e limpa os campos.

O formulário apresenta campos tipados com a opção do CLI correspondente, selos
(leitura, confirmação, contínuo, indisponível) e o comando equivalente, com
credenciais mascaradas e botão de cópia. Abaixo, abas mostram resultado, estado
atual, JSON completo, ajuda do CLI e logs, em fonte monoespaçada e copiáveis.
A confirmação repete o comando e destaca em vermelho ações destrutivas. Campos com `*` são obrigatórios;
campos opcionais vazios são omitidos. Entradas variádicas usam valores separados
por espaços; argumentos de aplicativos usam um vetor JSON, como
`["--new-window", "https://example.org"]`. Não existe console de comandos.
A referência inglesa do CLI pode ser expandida no formulário.

As seções cobrem conexão automática, conta e dispositivos, vouchers, servidores
e overrides, listas personalizadas, multihop, DAITA, criptografia, IPv6, MTU,
rotação de chaves, anticensura, DNS, bloqueios de conteúdo, LAN, bloqueio fora da
VPN, exclusão por PID, lançamento por `mullvad-exclude`, proxies para a API,
logs, exportação/importação e resets. Veja a [matriz completa](docs/matriz-cli.md).

Toda mutação requer confirmação contextual. Reset de fábrica também remove
conta, caches e logs. Exportações exigem caminho absoluto, usam permissão `0600`
e **recusam sobrescrever** arquivos; importações exigem um objeto JSON e recusam
links simbólicos. A chave privada de um servidor próprio é enviada por stdin.

## Preferências e IPC

O idioma automático segue `SessionData.locale` do DMS, com fallback à localidade
Qt e ao inglês. É possível escolher English ou Português (Brasil). O DMS salva
somente idioma e exibição da localização na barra.

```sh
dms ipc call DankMullvadVPN open
dms ipc call DankMullvadVPN settings
dms ipc call DankMullvadVPN toggle
```

`toggle` solicita a conexão/desconexão e abre a confirmação na janela.
`settings` abre as preferências da interface. Alternativamente, use o IPC
diretamente pela instância Quickshell que executa o DMS.

## Desenvolvimento e testes

```sh
python3 -m unittest discover -s tests
scripts/check
scripts/check --core
```

`scripts/check` verifica manifesto, cobertura de todos os comandos/opções,
traduções, matriz, testes Python e carregamento QML com os imports reais do DMS.
O teste gráfico usa o backend simulado, diretórios temporários e uma instância
separada. Requer uma sessão Wayland acessível; não reinicia a sessão principal.
Defina `DMS_QML_ROOT=/caminho/do/DMS` se necessário. `--core` omite explicitamente
o teste gráfico e é o modo portátil da CI; o workflow também permite executar
o teste completo num runner Linux preparado com DMS/Wayland.
O teste gráfico também requer o módulo QtTest do Qt 6 e envia cliques e teclas
a uma barra temporária: abertura do resumo/janela, busca, confirmação modal,
cancelamento, ciclo de foco, atalhos, preferências e layout de 640 px.

O backend simulado pode ser ativado para demonstração com
`DANK_MULLVAD_MOCK=1`. A interface mostra **SIMULAÇÃO**; nessa condição, nenhuma
ação real da VPN é executada.

Leia [Repository Guidelines](AGENTS.md), [arquitetura e segurança](docs/arquitetura.md),
[matriz CLI/interface](docs/matriz-cli.md) e
[checklist de validação/restauração](docs/validacao-manual.md).

## Solução de problemas

- **Executável ausente:** confira `mullvad --version` e o PATH do serviço DMS.
  O PATH do terminal pode ser diferente do PATH do serviço.
- **Daemon indisponível:** consulte `systemctl status mullvad-daemon` e
  `mullvad status --json` como o mesmo usuário do DMS.
- **Operação indisponível:** o adaptador verifica ajuda e opções da versão
  instalada e desativa o formulário com explicação. A versão-alvo é 2026.5.
- **Formato mudou:** o erro identifica o parser; atualize a fixture e o parser
  somente depois de conferir a saída e os testes.
- **Acompanhamento parado:** o status tenta recuperar automaticamente. Logs
  são iniciados/parados no formulário de manutenção e ficam limitados às
  últimas 200 linhas. A leitura de logs pode depender das permissões do Linux.
- **Adaptador parado:** recarregue o plugin pelo DMS. Não há retentativa de
  mutações: um timeout pode ocorrer depois de o daemon ter aplicado a ação.
- **Exportação falhou:** escolha outro arquivo e confira a permissão do
  diretório. O arquivo existente permanece intacto.

## Evidência de validação

A implementação foi verificada localmente com Mullvad 2026.5 e imports reais
do DMS 1.6.2. As leituras reais consultaram estado, opções e listas. **Nenhuma
conexão, desconexão, alteração, criação/revogação de conta ou reset real foi
executado.** A CI foi configurada, mas não foi publicada nem executada remotamente.
O [registro de validação](docs/validacao-manual.md) distingue testes simulados,
leituras reais e mutações pendentes.

Licença MIT. Projeto comunitário, sem afiliação com Mullvad ou DankMaterialShell.
