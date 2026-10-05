# Matriz CLI / interface — Mullvad 2026.5

Cada linha corresponde a um formulário registrado. A árvore de navegação (seção e operação) abre os campos indicados; comandos avançados têm formulários, sem console de comandos. Todos os parâmetros passam por `backend.arguments`; as respostas de leitura passam por `backend.parse_output`.

A referência inglesa de cada comando fica na aba **Ajuda do CLI**, e o formulário mostra o comando equivalente com credenciais mascaradas. `--help`/`-h` e `--version`/`-V` são opções informativas globais: ajuda no formulário e versão em manutenção. `status --json` é aplicado pelo adaptador. `--assume-yes` e `--confirm` são internos e só aparecem depois da confirmação gráfica. Os aliases curtos e longos são equivalentes; o adaptador usa os longos.

| Comando | Seção / formulário | Campos e validação | Leitura do daemon | Teste |
|---|---|---|---|---|
| `mullvad connect` | Conexão / Conectar à VPN | `--wait`: bool | `status` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad disconnect` | Conexão / Desconectar da VPN | `--wait`: bool | `status` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad reconnect` | Conexão / Reconectar à VPN | `--wait`: bool | `status` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad status` | Conexão / Consultar estado da VPN | `--verbose`: bool; `--debug`: bool | `status` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad version` | Manutenção / Consultar versão e atualizações | Sem campos | `version` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad factory-reset` | Manutenção / Restaurar configurações de fábrica | Sem campos | `version` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad reset-settings` | Manutenção / Redefinir configurações preservando a conta | `--preserve`: multi: relay-settings, anti-censorship, custom-lists, api-access, update-default-location, allow-lan, lockdown-mode, auto-connect, tunnel-options, relay-overrides, show-beta-releases, recents (lista) | `version` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad import-settings` | Manutenção / Importar configurações JSON | `file`: file * | `version` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad export-settings` | Manutenção / Exportar configurações JSON | `file`: file * | `version` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad account create` | Conta e dispositivos / Criar conta e fazer login | Sem campos | `account.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad account login` | Conta e dispositivos / Fazer login na conta | `account`: account (sigiloso) * | `account.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad account logout` | Conta e dispositivos / Sair da conta | Sem campos | `account.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad account get` | Conta e dispositivos / Consultar conta e validade | `--verbose`: bool | `account.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad account list-devices` | Conta e dispositivos / Listar dispositivos da conta | `--account`: account (sigiloso); `--verbose`: bool | `account.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad account revoke-device` | Conta e dispositivos / Revogar dispositivo | `device`: text *; `--account`: account (sigiloso) | `account.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad account redeem` | Conta e dispositivos / Resgatar voucher | `voucher`: text (sigiloso) * | `account.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad auto-connect get` | Conexão / Consultar conexão automática | Sem campos | `status` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad auto-connect set` | Conexão / Alterar conexão automática | `policy`: enum: on, off * | `status` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad beta-program get` | Manutenção / Consultar notificações beta | Sem campos | `version` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad beta-program set` | Manutenção / Alterar notificações beta | `policy`: enum: on, off * | `version` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad lockdown-mode get` | DNS e rede / Consultar bloqueio fora da VPN | Sem campos | `dns.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad lockdown-mode set` | DNS e rede / Alterar bloqueio fora da VPN | `policy`: enum: on, off * | `dns.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad dns get` | DNS e rede / Consultar DNS | Sem campos | `dns.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad lan get` | DNS e rede / Consultar acesso à rede local | Sem campos | `dns.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad lan set` | DNS e rede / Alterar acesso à rede local | `policy`: enum: allow, block * | `dns.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad relay get` | Servidores e listas / Consultar critérios de servidores | Sem campos | `relay.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad relay list` | Servidores e listas / Listar servidores disponíveis | Sem campos | `relay.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad relay update` | Servidores e listas / Atualizar lista de servidores | Sem campos | `relay.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad api-access get` | Acesso à API / Consultar método de API atual | Sem campos | `api-access.list` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad api-access list` | Acesso à API / Listar métodos de acesso à API | Sem campos | `api-access.list` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad api-access edit` | Acesso à API / Editar método de acesso à API | `index`: integer 1–100000 *; `--name`: text; `--username`: text (sigiloso); `--password`: text (sigiloso); `--cipher`: cipher; `--ip`: ip; `--port`: port; `--local-port`: port; `--transport-protocol`: enum: TCP, UDP | `api-access.list` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad api-access remove` | Acesso à API / Remover método de acesso à API | `index`: integer 1–100000 * | `api-access.list` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad api-access enable` | Acesso à API / Ativar método de acesso à API | `index`: integer 1–100000 * | `api-access.list` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad api-access disable` | Acesso à API / Desativar método de acesso à API | `index`: integer 1–100000 * | `api-access.list` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad api-access use` | Acesso à API / Usar método de acesso à API | `index`: integer 1–100000 * | `api-access.list` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad api-access test` | Acesso à API / Testar método de acesso à API | `index`: integer 1–100000 * | `api-access.list` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad anti-censorship get` | Túnel / anticensura / Consultar anticensura | Sem campos | `tunnel.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad split-tunnel list` | Exclusão do túnel / Listar PIDs fora da VPN | Sem campos | `split-tunnel.list` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad split-tunnel add` | Exclusão do túnel / Excluir PID da VPN | `pid`: integer 1–2147483647 * | `split-tunnel.list` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad split-tunnel delete` | Exclusão do túnel / Restaurar proteção VPN do PID | `pid`: integer 1–2147483647 * | `split-tunnel.list` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad split-tunnel clear` | Exclusão do túnel / Restaurar proteção de todos os PIDs | Sem campos | `split-tunnel.list` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad status listen` | Conexão / Acompanhar estado da VPN | Sem campos | `status` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad tunnel get` | Túnel / anticensura / Consultar opções do túnel | Sem campos | `tunnel.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad custom-list new` | Servidores e listas / Criar lista personalizada | `name`: text * | `relay.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad custom-list list` | Servidores e listas / Consultar listas personalizadas | `name`: text | `relay.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad custom-list delete` | Servidores e listas / Excluir lista personalizada | `name`: text * | `relay.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad log set-level` | Manutenção / Configurar nível de log | `level`: enum: off, error, warn, info, debug, trace * | `version` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad log set-rust-log` | Manutenção / Configurar filtro RUST_LOG | `filter`: text * | `version` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad log listen` | Manutenção / Acompanhar logs do daemon | Sem campos | `version` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad dns set default` | DNS e rede / DNS padrão e bloqueios de conteúdo | `--block-ads`: bool; `--block-trackers`: bool; `--block-malware`: bool; `--block-adult-content`: bool; `--block-gambling`: bool; `--block-social-media`: bool | `dns.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad dns set custom` | DNS e rede / Configurar servidores DNS próprios | `servers`: ip (lista) * | `dns.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad relay set location` | Servidores e listas / Selecionar servidor de saída por localização | `country`: location *; `city`: city; `hostname`: text | `relay.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad relay set custom-list` | Servidores e listas / Selecionar lista de saída | `custom_list_name`: text * | `relay.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad relay set provider` | Servidores e listas / Filtrar provedores | `providers`: text (lista) * | `relay.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad relay set ownership` | Servidores e listas / Filtrar servidores próprios ou alugados | `ownership`: enum: any, owned, rented * | `relay.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad relay set ip-version` | Servidores e listas / Selecionar versão IP do túnel | `ip_version`: enum: any, ipv4, ipv6 * | `relay.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad relay set multihop` | Servidores e listas / Ativar ou desativar multihop | `use_multihop`: enum: on, off * | `relay.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad relay set custom` | Servidores e listas / Configurar servidor WireGuard próprio | `host`: text *; `port`: port *; `peer_pubkey`: key *; `tunnel_ip`: ip (lista) *; `--v4-gateway`: ip *; `--v6-gateway`: ip; `private_key (stdin)`: key (sigiloso) * | `relay.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad relay override get` | Servidores e listas / Consultar overrides de servidores | Sem campos | `relay.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad relay override clear-all` | Servidores e listas / Remover todos os overrides | Sem campos | `relay.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad api-access add shadowsocks` | Acesso à API / Adicionar proxy Shadowsocks | `name`: text *; `remote_ip`: ip *; `remote_port`: port *; `password`: text (sigiloso) *; `--disabled`: bool; `--cipher`: cipher * | `api-access.list` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad anti-censorship set mode` | Túnel / anticensura / Selecionar modo de anticensura | `mode`: enum: auto, off, wireguard-port, udp2tcp, shadowsocks, quic, lwo * | `tunnel.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad anti-censorship set udp2tcp` | Túnel / anticensura / Configurar porta UDP sobre TCP | `--port`: port / any * | `tunnel.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad anti-censorship set shadowsocks` | Túnel / anticensura / Configurar porta Shadowsocks | `--port`: port / any * | `tunnel.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad anti-censorship set wireguard-port` | Túnel / anticensura / Configurar porta WireGuard | `--port`: port / any * | `tunnel.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad anti-censorship set lwo` | Túnel / anticensura / Configurar porta LWO | `--port`: port / any * | `tunnel.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad tunnel set mtu` | Túnel / anticensura / Configurar MTU | `mtu`: integer 0–65535 / any * | `tunnel.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad tunnel set quantum-resistant` | Túnel / anticensura / Configurar resistência quântica | `state`: enum: on, off * | `tunnel.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad tunnel set daita` | Túnel / anticensura / Configurar DAITA | `state`: enum: on, off * | `tunnel.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad tunnel set daita-direct-only` | Túnel / anticensura / Configurar DAITA somente direto | `state`: enum: on, off * | `tunnel.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad tunnel set allowed-ips` | Túnel / anticensura / Configurar IPs e redes permitidas | `allowed_ips`: cidrs * | `tunnel.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad tunnel set rotation-interval` | Túnel / anticensura / Configurar intervalo de rotação da chave | `interval`: integer 24–720 / any * | `tunnel.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad tunnel set rotate-key` | Túnel / anticensura / Rotacionar chave WireGuard agora | Sem campos | `tunnel.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad tunnel set ipv6` | Túnel / anticensura / Configurar IPv6 no túnel | `state`: enum: on, off * | `tunnel.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad tunnel set userspace` | Túnel / anticensura / Configurar WireGuard em userspace | `state`: enum: on, off * | `tunnel.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad custom-list edit add` | Servidores e listas / Adicionar localização à lista | `name`: text *; `country`: location *; `city`: city; `hostname`: text | `relay.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad custom-list edit remove` | Servidores e listas / Remover localização da lista | `name`: text *; `country`: location *; `city`: city; `hostname`: text | `relay.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad custom-list edit rename` | Servidores e listas / Renomear lista | `name`: text *; `new_name`: text * | `relay.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad relay set entry location` | Servidores e listas / Selecionar entrada do multihop por localização | `country`: location *; `city`: city; `hostname`: text | `relay.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad relay set entry custom-list` | Servidores e listas / Selecionar lista de entrada do multihop | `custom_list_name`: text * | `relay.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad relay override set ipv4` | Servidores e listas / Definir override IPv4 | `hostname`: text *; `address`: ip * | `relay.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad relay override set ipv6` | Servidores e listas / Definir override IPv6 | `hostname`: text *; `address`: ip * | `relay.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad relay override unset ipv4` | Servidores e listas / Remover override IPv4 | `hostname`: text * | `relay.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad relay override unset ipv6` | Servidores e listas / Remover override IPv6 | `hostname`: text * | `relay.get` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad api-access add socks5 remote` | Acesso à API / Adicionar proxy SOCKS5 remoto | `name`: text *; `remote_ip`: ip *; `remote_port`: port *; `--disabled`: bool; `--username`: text (sigiloso); `--password`: text (sigiloso) | `api-access.list` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad api-access add socks5 local` | Acesso à API / Adicionar proxy SOCKS5 local | `name`: text *; `local_port`: port *; `remote_ip`: ip *; `remote_port`: port *; `--disabled`: bool; `--transport-protocol`: enum: TCP, UDP | `api-access.list` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad-exclude` | Exclusão do túnel / Lançar aplicativo fora da VPN | `executable`: executable *; `arguments`: argv | `split-tunnel.list` + settings JSON | `test_all_operation_arguments`, QML mock |
| `mullvad --version` | Manutenção / Versão do executável CLI | Sem campos | `version` + settings JSON | `test_all_operation_arguments`, QML mock |

## Contratos e limites

- [Arquitetura e segurança](arquitetura.md): envelopes JSONL, validação, erros, versões, parsers e armazenamento.
- `test_known_argument_contracts` verifica argumentos sensíveis, opcionais e variádicos por exemplos independentes; `test_all_finite_operations_execute` percorre cada operação finita com CLI simulado.
- O teste QML percorre e submete os 88 formulários em quatro combinações (inglês/pt-BR × escuro/claro), verifica confirmação e limpeza dos campos sigilosos. Leituras, snapshots e streams têm testes de processo separados.
- `test_custom_wireguard_private_key_only_uses_stdin` verifica a entrada que não aparece em `--help`: a chave privada do servidor próprio é enviada por stdin.
- Nomes de cifras Shadowsocks são validados sintaticamente e pelo CLI; o formulário aceita todos os nomes suportados pela versão instalada, sem restringir a três cifras comuns.
- [Checklist manual](validacao-manual.md): todas as mutações reais permanecem pendentes; a cobertura automatizada usa um CLI simulado.
- A leitura compartilhada `export-settings -` apresenta configurações completas em JSON, com segredos ocultos e sem gravar arquivo. Ela complementa campos omitidos pelos getters textuais, como DAITA direto e userspace. O CLI não oferece getter do nível/filtro de logs; esses valores não são apresentados como conhecidos.
