# Validação real e restauração

## Registro desta implementação — 5 de outubro de 2026

- Mullvad CLI instalado: **2026.5**; daemon acessível por leitura fora do sandbox.
- DMS usado no teste: **v1.6.2**, em seu diretório runtime da sessão.
- Leituras reais: `status --json`, versão, políticas de conexão automática/beta/
  bloqueio, DNS, LAN, relays e overrides, métodos de API, anticensura, PIDs
  excluídos, opções do túnel, conta/dispositivos e listas personalizadas.
- A conexão estava ativa; a coleta não conectou, desconectou, reconectou nem
  alterou configurações. As fixtures ocultam números de conta, chaves e senhas.
- Testes Python usam um executável simulado: parâmetros, operações, validação,
  redaction, parsers, erros, timeouts, concorrência, eventos, shutdown e arquivos.
- Teste QML usa imports reais do DMS e backend simulado, em configuração e
  diretórios temporários: barra horizontal/vertical, popout, janela, preferências,
  todos os formulários, confirmações e limpeza de segredos nos dois idiomas e
  temas. Esse teste não habilita o plugin na sessão principal.
- A CI está configurada no repositório; execução remota não foi realizada.
- Nenhuma mutação real listada abaixo foi testada. Esses itens são pendências
  deliberadas da validação física/operacional, não comandos para executar agora.
- A verificação final do adaptador realizou **20 leituras**, todas com sucesso,
  incluindo configurações completas por `export-settings -` e o evento inicial
  de `status --json listen`, encerrando o monitor depois. O registro está em
  [read-only-validation.json](read-only-validation.json).
- `scripts/check` executa **18 testes Python**, confere **232 chaves de tradução**
  e submete **88 formulários × 4 combinações de idioma/tema**. Imagens locais
  de inspeção ficam em `test-results/`, fora do Git.
- A revisão da janela testa cliques reais QtTest na barra e no popout, busca
  global e vazia, campos descartados ao fechar, confirmação modal, Tab cíclico,
  Escape, Ctrl+F, preferências, bloqueio durante conexão e layout de 640 px.
  O backend dessas interações é simulado; isso não valida mutações reais.
- Nesta revisão, o plugin foi habilitado na sessão principal e adicionado à
  barra **Main Bar**, antes da bandeja do sistema. A janela de 1060 × 780 px
  foi aberta via IPC; barra e janela foram inspecionadas com o tema real.
  A configuração da barra foi comparada com o backup: apenas o novo widget
  foi acrescentado. O DMS não foi reiniciado e a VPN permaneceu conectada.
  O backup local está em `test-results/dms-settings-before-widget.json` (`0600`).
  Para desfazer a integração, remova o widget nas configurações da DankBar e
  desabilite o plugin. Não restaure o arquivo inteiro se outras preferências
  tiverem mudado desde o backup.

## Preparação antes de qualquer teste real

1. Obtenha autorização explícita para a operação concreta. Tenha acesso local
   ao desktop; mudanças de rede podem interromper uma sessão remota.
2. Registre estado, servidor, políticas DNS/LAN/bloqueio e opções do túnel, sem
   guardar credenciais em relatórios. Anote como restaurar os PIDs excluídos.
3. Exporte um backup para um arquivo novo em diretório privado (`0600`) usando
   o formulário. Confira que o arquivo é JSON e mantenha-o fora do Git.
4. Tenha o aplicativo oficial disponível. Guarde o número de recuperação da
   conta em local seguro. Exportar configurações **não** garante backup da conta,
   chaves, dispositivos, vouchers, processos ou logs.
5. Mude um recurso por vez. Registre resultado, estado final, alcance de rede,
   versão e data. Não descreva uma requisição enviada como mudança confirmada.

## Checklist de mutações pendentes

| Família | Teste manual pendente | Restauração |
|---|---|---|
| Conexão | [ ] conectar / desconectar / reconectar, com e sem espera | Restaurar estado e servidor anterior |
| Políticas | [ ] conexão automática, beta, LAN e bloqueio fora da VPN | Reaplicar cada valor anterior; conferir internet e LAN |
| Conta | [ ] login / logout / criação | Reentrar na conta anterior pelo aplicativo oficial; criação usa nova conta |
| Dispositivos | [ ] revogação | Pode exigir cadastrar novo dispositivo; a revogação anterior não é reversível |
| Vouchers | [ ] resgate | Usar voucher de teste autorizado; resgate não é reversível |
| Relays | [ ] localização / provedor / propriedade / IP / atualização | Reaplicar critérios anteriores e aguardar lista/estado final |
| Multihop | [ ] ativação, entrada por localização e listas | Restaurar entrada/saída e flag anterior |
| Servidor próprio | [ ] host, portas, gateways, IPs e chaves via stdin | Voltar à seleção normal anterior; descartar chave de teste com segurança |
| Overrides | [ ] set/unset IPv4/IPv6 e limpeza completa | Reaplicar overrides do backup ou valores anotados |
| Listas | [ ] criar / adicionar / remover / renomear / excluir | Importar backup ou recriar listas e referências anteriores |
| Túnel | [ ] MTU, quantum, DAITA, DAITA direto, IPv6, userspace | Reaplicar opções anteriores e verificar conectividade |
| Chaves | [ ] intervalo 24–720 h / any e rotação imediata | Restaurar intervalo; chave rotacionada não retorna pelo backup de settings |
| Rotas | [ ] allowed IPs, incluindo restauração com campo vazio | Reaplicar redes anteriores; confirmar rotas IPv4/IPv6 |
| Anticensura | [ ] auto/off/WireGuard/UDP2TCP/Shadowsocks/QUIC/LWO e portas | Restaurar modo/portas anteriores e verificar handshake |
| DNS | [ ] seis bloqueios e DNS próprio IPv4/IPv6 | Restaurar política/servidores anteriores; conferir resolução |
| Split por PID | [ ] adicionar / excluir / limpar PIDs | Reaplicar os PIDs ainda existentes; observar descendentes |
| Lançamento excluído | [ ] executar app e argumentos literais | Encerrar o app de teste e conferir PIDs fora da VPN |
| API | [ ] adicionar/editar/remover, ativar/desativar/usar métodos | Restaurar métodos e seleção anteriores; conferir acesso à conta |
| Proxies | [ ] SOCKS5 remoto/local, autenticação, TCP/UDP e Shadowsocks | Restaurar método anterior; remover proxy de teste |
| Logs | [ ] nível / filtro e acompanhamento real | Reaplicar nível/filtro anterior; parar acompanhamento |
| Arquivos | [ ] exportar/importar com daemon real | Importar backup autorizado; confirmar estado e todas as seções |
| Reset parcial | [ ] reset-settings com cada conjunto preserve | Importar backup e restaurar valores não exportados |
| Reset de fábrica | [ ] factory-reset | Reentrar na conta, importar backup, restaurar processos; logs/caches removidos não voltam |

## Verificação da interface na sessão principal

- [x] Habilitar pelo gerenciador de plugins e adicionar à DankBar.
- [ ] Testar popout, clique direito, IPC `open`/`settings`/`toggle` e múltiplos monitores.
- [ ] Confirmar navegação Tab/Shift+Tab, Enter/Espaço e Escape, além de leitor de tela.
- [ ] Conferir contraste, dimensionamento e rolagem com fontes/DPI reais.
- [ ] Mudar o idioma do DMS em modo automático; verificar fallback inglês.
- [ ] Descarregar o plugin e confirmar ausência de streams/processo Python órfãos.
- [ ] Reiniciar o daemon separadamente em ambiente autorizado e observar recuperação.

O teste automatizado de carregamento/submissão não substitui essas interações
físicas nem prova que uma operação de rede funcionou no daemon real. A entrega
do código não inclui executar os itens pendentes sem autorização.
