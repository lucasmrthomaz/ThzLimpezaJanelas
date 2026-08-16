<img width="1123" height="832" alt="image" src="https://github.com/user-attachments/assets/d6818245-d21a-4380-a96f-235a71b530e3" />

# 🧹 THZ Limpeza de Janelas

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg?style=flat-square&logo=python)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/UI-PySide6%20%2F%20Qt6-0078D4.svg?style=flat-square&logo=qt)](https://www.qt.io/)
[![Plataforma](https://img.shields.io/badge/Plataforma-Windows-0078D4.svg?style=flat-square&logo=windows)](https://microsoft.com/windows)
[![Licença](https://img.shields.io/badge/Licen%C3%A7a-AGPL-green.svg?style=flat-square)](LICENSE)

**THZ Limpeza de Janelas** é uma ferramenta de desktop moderna, rápida e intuitiva desenvolvida em Python e PySide6 (Qt6) para limpeza, otimização e recuperação de espaço em disco no Windows. Principalmente para o perfil do usuário. Projetada especificamente sob os princípios de **Clean Code**, **KISS** (Keep It Simple, Stupid) e arquitetura modular de alta performance.

---

## 📸 Interface e Layout

A aplicação conta com um painel superior reativo (dashboard) e uma estrutura de abas onde cada uma analisa e gerencia partes específicas do disco rígido:

* **📁 Perfil do Usuário**: Analisa e calcula o tamanho de diretórios na raiz do perfil do usuário (`C:\Users\<Nome>`), ocultando pastas ocultas e o AppData.
* **📂 AppData**: Analisa e calcula o tamanho dos diretórios internos no AppData (`Local`, `LocalLow` e `Roaming`).
* **📭 Pastas Vazias**: Varre recursivamente diretórios e aponta de forma instantânea pastas sem nenhum conteúdo útil.
* **🗑️ Cache e Temporários**: Localiza armazenamentos temporários conhecidos (Chrome, Edge, Spotify, Discord, Windows Temp, Log, Pip, Npm, etc.) e busca caches baseados em nome.
* **⚠️ Arquivos +1 ano (100MB+)**: Localiza arquivos pesados acumulados no disco que não sofreram nenhuma modificação no último ano.

---

## ✨ Recursos Exclusivos e Melhorias de UX

* **⚡ Escaneamento Assíncrono com Bufferização**: A busca é executada em uma thread de processamento em lote em segundo plano. Os resultados alimentam a interface a cada `100ms` em lote, garantindo que o programa se mantenha 100% responsivo, sem lentidão técnica ou travamento de cliques.
* **📐 Ordenação Numérica Perfeita (`SizeWidgetItem`)**: Customização robusta da ordenação no Qt. A tabela ordena o tamanho real de bytes de forma exata e coerente ao clicar na coluna **Tamanho** (`GB > MB > KB > B`), corrigindo a ordenação padrão de strings.
* **📂 Localização Rápida no Explorer**: Dê um clique duplo em qualquer arquivo ou pasta na tabela para abrir o local de destino destacado diretamente no Windows Explorer.
* **📋 Menu de Contexto Dinâmico**: Clique com o botão direito sobre um item da lista para abrir o local, copiar o caminho ou limpá-lo de forma isolada.
* **🛡️ Remoção Inteligente de Itens Bloqueados (Zero Spams)**: Ao limpar, os arquivos que não puderem ser enviados à Lixeira (dados em uso do sistema) são consolidados. O sistema exibe um aviso unificado de exclusão direta definitiva apenas uma vez, evitando loops infinitos de caixas de diálogo.
* **🌓 Integração de Tema Nativo**: Detecta de forma autônoma o tema atual (Solarizado claro ou Dark mode) do próprio sistema operacional Windows e formata a aplicação inteira de forma harmônica.

---

## 🛠️ Arquitetura do Projeto (Modularizada)

* **`main.py`** / **`main.pyw`**: Pontos de entrada limpos da aplicação.
* **`Iniciar.bat`**: Script inicializador portátil inteligente para dar dois cliques no Windows (executa via `pythonw` sem janelas pretas do Prompt de Comando).
* **`config.py`**: Declarações e isolamento de contornos de dados, ignores de pastas, listas de caches conhecidos e limiares de tempo e tamanho.
* **`theme.py`**: Responsável pela lógica de cores, botões, scrolls e folhas de estilo globais (QSS).
* **`workers.py`**: Threads exclusivas em segundo plano (`QThreads`) para listagem rápida de pastas sem travar a thread de interface (GUI).
* **`widgets.py`**: Organização de componentes da tela (`TabPage` e `StatCard`) e regras customizadas de cliques de navegação e menus.
* **`window.py`**: Gerenciador da tela principal (`MainWindow`), que monitora o processo global de carregamento e consolida o Dashboard de estatísticas.
* **`utils.py`**: Ferramentas puras de cálculo de tamanho físico real de diretórios e parses de medidas.

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
Certifique-se de possuir o **Python 3.12** instalado no ambiente de desenvolvimento.

### 1. Clonar ou Acessar a pasta do Projeto:
```bash
cd ThzLimpezaJanelas
```

### 2. Instalar Dependências Necessárias:
A aplicação requer as seguintes dependências externas (`PySide6` para visual e `send2trash` para exclusão sem perdas):
```bash
pip install PySide6 send2trash
```
*(Se estiver utilizando o interpretador do Microsoft Windows Store, instale via `python -m pip install PySide6 send2trash --user`)*

### 3. Iniciar a Aplicação:
* **Executar no Terminal**:
  ```bash
  python main.py
  ```
* **No Windows (Interface gráfica direta)**:
  Dê dois cliques no inicializador **`Iniciar.bat`** (ou direto em **`main.pyw`**). A ferramenta será carregada em silêncio e aberta na sua tela sem abrir console/linhas de comando adicionais do terminal.

---

## 📝 Licença
Este projeto é distribuído sob a licença AGPL 3.0 (GNU Affero General Public License v3.0). Consulte o arquivo [LICENSE](LICENSE) para obter mais informações.
