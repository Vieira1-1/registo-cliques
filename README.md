## Manual de Utilizador (resumo)

A aplicação apresenta 4 botões, cada um representando uma atividade na biblioteca.
Ao clicar num botão, o sistema regista o clique numa base de dados SQLite com:
- botão/atividade
- clique nº (contador diário independente por botão)
- data
- hora (HH:MM)

### Como usar
1. Clicar numa das atividades.
2. Confirmar o registo na janela (modal) com data/hora e clique nº.
3. Consultar o log da sessão na página.
4. Para análise no Excel, usar o botão **Exportar CSV**.

### Exportar para Excel
A aplicação disponibiliza um ficheiro CSV através do endpoint:
`/api/export.csv`
