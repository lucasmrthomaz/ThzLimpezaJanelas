# THZ Limpeza de Janelas

Cleaner do perfil Windows (`C:\Users\Lucas`) para remover lixo do sistema: pastas vazias, caches, temporários e arquivos grandes antigos.

---

## Stack

| Tecnologia | Versão | Uso |
|---|---|---|
| Python 3 | 3.12+ | Runtime |
| PySide6 | 6.11.1 | GUI (Qt for Python) |
| send2trash | — | Envio seguro para Lixeira do Windows |
| os.scandir | stdlib | Varredura performática de diretórios (stat-free IO) |
| QThread | PySide6 | Threads independentes para scan sem travar UI |
| threading / concurrent.futures | stdlib | Cálculo paralelo de tamanho de diretórios |

---

## Estrutura do Projeto

```
ThzLimpezaJanelas/
  main.py        # Entry point (define run(); orquestra QApplication)
  main.pyw       # Execução sem console — delega para main.run()
  config.py      # Constantes: HOME, APPD, SKIP_DIRS, CACHE_PATTERNS, KNOWN_CACHE, CARD_CFG, TABS
  utils.py       # fmt, parse_size, dir_size
  theme.py       # Detecção claro/escuro e construção do QSS global
  workers.py     # ScanWorker (QThread) — varreduras em thread separada
  widgets.py     # StatCard, SizeWidgetItem, TabPage
  window.py      # Window (QMainWindow) — dashboard + abas + status
  Iniciar.bat    # Atalho: python main.py
  AGENTS.md      # Este documento (contexto para novas conversas)
```

---

## Constantes Globais (`config.py`)

### `SKIP_DIRS` — `frozenset`
Diretórios do sistema ignorados em TODAS as varreduras (case-insensitive):
```
windows, program files, program files (x86), $recycle.bin,
system volume information, perflogs, recovery, winnt,
all users, default user, public, default
```

### `CACHE_PATTERNS` — `list[str]`
Padrões de nome usados pelo scan dinâmico de cache (abrange nomes como `cache`, `temp`, `logs`, `crash`, `node_modules`, `__pycache__`, `.git`, etc.)

### `KNOWN_CACHE` — `list[str]`
Caminhos relativos à `AppData` com caches conhecidos de aplicativos:
- Navegadores (Chrome, Edge, Firefox)
- Gerenciadores de pacote (npm, pip, Yarn, NuGet)
- Aplicativos (Discord, Slack, Spotify, Teams, OneDrive, Steam, etc.)
- Sistema (Temp, INetCache, CrashDumps, WER, AppCache)

### `CARD_CFG` — `list[tuple(key, icon, label, color)]`
Configuração dos cartões do dashboard:
```
USER      📁 Perfil do Usuário     #0078D4 (azul)
APPDATA   📂 AppData               #0078D4 (azul)
EMPTY     📭 Pastas Vazias         #5C2D91 (roxo)
CACHE     🗑️ Cache/Temporários     #D83B01 (laranja)
LARGE_OLD ⚠️ Arquivos +1 ano       #E81123 (vermelho)
```

### `TABS` — `list[tuple(key, label)]`
Configuração das abas do `QTabWidget`.

### Outras constantes
- `HOME` = `%USERPROFILE%` (ex: `C:\Users\Lucas`)
- `APPD` = `HOME + \AppData`
- `CUTOFF` = `time.time() - 365*24*3600` (1 ano atrás)
- `BIG` = `100 * 1024 * 1024` (100 MB)

---

## Funções Utilitárias

### `fmt(n: int) -> str`
Formata bytes para string legível: `0 B`, `1.5 KB`, `3.2 MB`, `1.8 GB`, `2.4 TB`

### `parse_size(text: str) -> float`
Interpreta o texto formatado de volta para bytes. Ex: `"1.5 MB"` → `1572864.0`

### `dir_size(root: str, check=None) -> int`
Calcula tamanho total recursivo de um diretório usando **pilha iterativa** (stack) + `os.scandir`. Evita recursão profunda e syscalls extras.
- `follow_symlinks=False` — não segue junctions do Windows
- `check` (callable opcional) é chamado dentro do loop para cancelamento cooperativo — o `ScanWorker` passa `self._check`
- Engole `PermissionError` e `OSError` silenciosamente

---

## Classes

### `Cancelled(Exception)`
Exceção usada internamente pelos workers para interromper a varredura quando o usuário clica em "Cancelar".

---

### `ScanWorker(QThread)`
Worker principal. Executa a varredura de acordo com `self.kind` em uma thread separada.

#### Signals
| Signal | Tipo | Descrição |
|---|---|---|
| `item` | `Signal(str, object, str)` | `(path, size_bytes, info)` — um item encontrado |
| `status` | `Signal(str)` | Mensagem de status |
| `progress` | `Signal(int, int)` | `(current, total)` — progresso |
| `done` | `Signal()` | Varredura concluída (ou cancelada) |

#### Métodos
- `__init__(kind: str)` — kind é um dos `"USER"`, `"APPDATA"`, `"EMPTY"`, `"CACHE"`, `"LARGE_OLD"`
- `abort()` — sinaliza cancelamento (thread-safe)
- `_check()` — levanta `Cancelled` se `abort()` foi chamado

#### Fluxo (`run()`)
1. Dispara para o método específico baseado em `self.kind`
2. Se `Cancelled` for levantado, emite `status("Cancelado.")` e retorna
3. Emite `done()` ao final

#### Scans Implementados

| kind | Método | Descrição |
|---|---|---|
| `USER` | `_scan_root(HOME, skip_appdata=True)` | Top-level items do perfil |
| `APPDATA` | `_scan_root(APPD, skip_appdata=False)` | Top-level items da AppData |
| `EMPTY` | `_scan_empty()` | Caminha HOME + APPD com pilha, emite pastas sem filhos (vazias) |
| `CACHE` | `_scan_cache()` | 1. Verifica `KNOWN_CACHE` (paths fixos); 2. `_find_caches()` dinâmico até depth 3 |
| `LARGE_OLD` | `_scan_old()` | Caminha HOME, emite arquivos com `size >= BIG` e `mtime < CUTOFF` |

#### Detalhes do `_scan_root`
- Coleta entradas com `os.scandir`
- Para cada diretório: calcula `dir_size` **sequencialmente** (evita thrashing de I/O com múltiplas threads concorrentes)
- Para cada arquivo: emite `item(path, size, "")` diretamente
- Emite `progress(i+1, total)` no loop
- `dir_size` recebe `self._check` para permitir cancelamento cooperativo

---

### `StatCard(QFrame)`
Cartão do dashboard com indicador visual (borda superior colorida).

| Método | Descrição |
|---|---|
| `set(v, sub="")` | Atualiza valor principal e subtítulo |

#### Layout
```
┌─────────────────────┐
│  📁 Perfil do Usuário│  ← label (10px, bold, cinza)
│  134 itens           │  ← valor (18px, extrabold)
│  2.3 GB              │  ← subtítulo (10px, cinza)
└─────────────────────┘
  ↑ borda 3px colorida
```

---

### QTreeWidget (dentro de TabPage)
Cada aba contém um `QTreeWidget` com colunas `Item | Tamanho | Info`.

#### Criação do Item (`_add`)
```python
item = QTreeWidgetItem()
item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
item.setCheckState(0, Qt.Unchecked)          # ← ANTES do setText
item.setText(0, path)
item.setText(1, fmt(size) if size else "0 B")
item.setText(2, info)
item.setData(0, Qt.UserRole, path)            # caminho original para deleção
item.setToolTip(0, path)
# Coloração: >1GB vermelho, >500MB laranja
self.tree.addTopLevelItem(item)
```

#### Dados armazenados
- `item.data(0, Qt.UserRole)` — caminho original usado no `delete_selected()`

#### Interação com Checkbox
- **Clique na coluna Tamanho ou Info** (`_toggle_item` com `column > 0`): alterna o checkstate do checkbox (coluna 0)
- **Clique no checkbox nativo** (coluna 0, área do indicador): Qt alterna automaticamente (não há dupla alternância porque `_toggle_item` só age em `column > 0`)
- **Clique no texto do path** (coluna 0, fora do checkbox): não alterna (comportamento esperado — o checkbox nativo do Qt lida com essa área e apenas o indicador é clicável)

#### Estilo mínimo
```css
QTreeWidget::indicator { width: 18px; height: 18px; }
QTreeWidget::indicator:checked { background: #0078D4; border: 1px solid #0078D4; border-radius: 3px; }
QTreeWidget::indicator:unchecked { background: white; border: 1px solid #999; border-radius: 3px; }
QTreeWidget { border: none; alternate-background-color: #F8F8F8; }
QTreeWidget::item:hover { background: #E8F4FD; }
QHeaderView::section { background: #F8F8F8; color: #666;
    padding: 4px 6px; border: none;
    border-bottom: 2px solid #E0E0E0; font-weight: 700; font-size: 11px; }
```

---

### `TabPage(QWidget)`
Uma aba completa com toolbar, barra de progresso, status e tree.

| Signal | Tipo | Descrição |
|---|---|---|
| `scanned` | `Signal(str, int, object)` | `(kind, count, total_bytes)` — emitido ao finalizar scan |

#### Signals recebidos do `ScanWorker`
| Signal do worker | Handler |
|---|---|
| `item` | `_add(path, size, info)` → `self.tree.add(...)` |
| `status` | `self.lbl.setText(...)` |
| `progress` | `lambda c, t: setRange/setValue` |
| `done` | `_done()` |

#### Métodos
| Método | Descrição |
|---|---|
| `start()` | Inicia scan (se worker já rodando, ignora) |
| `_toggle_item(item, column)` | Alterna checkbox se `column > 0` (conectado a `itemClicked`) |
| `_cancel()` | Chama `worker.abort()` |
| `_sel_all()` | Marca checkbox de todos os itens |
| `_desel_all()` | Desmarca checkbox de todos |
| `_delete()` | Coleta itens marcados, confirma, envia para lixeira, reinicia scan |
| `_done()` | Esconde progresso, atualiza label, emite `scanned` |
| `_enable(busy)` | Habilita/desabilita botões conforme estado de scan |

#### Botões
| Botão | Estilo | Função |
|---|---|---|
| "▶ Escanear" | BTN (azul) | `start()` |
| "⏹ Cancelar" | BTN_GRAY | `_cancel()` |
| "☑ Selecionar" | BTN_OUT (borda) | `_sel_all()` |
| "☐ Desmarcar" | BTN_OUT | `_desel_all()` |
| "🗑 Lixeira" | BTN_RED (vermelho) | `_delete()` |

---

### `Window(QMainWindow)`
Janela principal contendo dashboard + abas.

#### Layout
```
┌──────────────────────────────────────────────┐
│  🧹 Thz Limpeza de Janelas                   │  ← header
├────────┬────────┬────────┬────────┬──────────┤
│ USER   │APPDATA │ EMPTY  │ CACHE  │ LARGE_OLD│  ← StatCards
│ 12 it. │ 8 it.  │ 340 it.│ 470 it.│ 3 it.    │
│ 1.2 GB │ 0.8 GB │ 0 B    │ 14.9 GB│ 2.1 GB   │
├────────┴────────┴────────┴────────┴──────────┤
│  📁 Perfil | 📂 AppData | 📭 Vazias | ...    │  ← QTabWidget
│  ┌────────────────────────────────────────┐  │
│  │ [▶ Escanear] [⏹ Cancelar] [☑] [☐] [🗑]│  │  ← TabPage toolbar
│  │ Status: 470 itens | 14.9 GB            │  │
│  │ ████████████████████░░░░░░░░░░░░░      │  │  ← progresso
│  │ ┌ Item           │ Tamanho │ Info    ┐ │  │
│  │ │ ☐ C:\...\Temp  │ 1.7 GB  │ Cache   │ │  │  ← TreeView
│  │ │ ☑ C:\...\npm   │ 549 MB  │ Cache   │ │  │
│  │ └────────────────┴─────────┴─────────┘ │  │
│  └────────────────────────────────────────┘  │
│  ⚡ Cada aba tem seu próprio botão...        │  ← status
└──────────────────────────────────────────────┘
```

#### Cards do Dashboard
6 `StatCard` em linha: USER, APPDATA, EMPTY, CACHE, LARGE_OLD, TOTAL GERAL (verde).
Atualizados via `_on_scan(kind, count, total)`.

#### Abas
5 `TabPage` em `QTabWidget`, cada uma com scan independente e concorrente.

---

## Estilos Globais

### Paleta (`C`)
| Chave | Cor | Uso |
|---|---|---|
| `bg` | `#F5F5F5` | Fundo da janela |
| `card` | `#FFFFFF` | Fundo de cartões e abas |
| `border` | `#E0E0E0` | Bordas |
| `text` | `#1A1A1A` | Texto principal |
| `dim` | `#666666` | Texto secundário |
| `blue` | `#0078D4` | Accent primário |

### Botões
| Estilo | Fundo | Texto | Hover |
|---|---|---|---|
| `BTN` (scan) | `#0078D4` | white | `#106EBE` |
| `BTN_GRAY` (cancel) | `#6C757D` | white | `#5A6268` |
| `BTN_RED` (delete) | `#D9534F` | white | `#C9302C` |
| `BTN_OUT` (select) | white | `#333` | `#F0F0F0` |

### `GLOBAL_QSS`
Stylesheet aplicado ao `QMainWindow` que propaga para todos os widgets. Inclui:
- Fonte padrão: `Segoe UI, Arial, sans-serif` (13px)
- Abas `QTabWidget` / `QTabBar` com bordas arredondadas e cor de seleção
- `QScrollBar` fino (6px) com cantos arredondados
- `QProgressBar` com gradiente azul (`#0078D4` → `#00A2E8`)

### Tema Dinâmico (Claro/Escuro)
Detectado automaticamente via registro do Windows em `_detect_dark()`:
- Chave: `HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize\AppsUseLightTheme`
- `0` = escuro, `1` = claro
- Gera cores `C`, botões `BTN*` e `GLOBAL_QSS` via `_build_theme(dark)` no módulo
- O tree widget também usa cores do `C` para indicator, header, hover e alternating rows

---

## Fluxo de Sinais (Signal Flow)

```
[ScanWorker thread]                    [Main thread]
                                        
_scan_root()                           
  ├─ dir_size(e.path, self._check)      # cálculo sequencial do diretório
  │   └─ item.emit(path, size)
  │       └─ (queued)                  
  │           └─ TabPage._add()
  │                       └─ TreeView.add() → checkable item
  │                                     
  └─ done.emit()
      └─ (queued)                      
          └─ TabPage._done()           
              ├─ atualiza label        
              └─ scanned.emit(kind, count, total)
                  └─ (direct)          
                      └─ Window._on_scan()
                          └─ atualiza StatCards
```

**Nota**: Sinais entre threads usam `Qt.QueuedConnection` automático. Sinais no mesmo thread usam `Qt.DirectConnection`.

---

## Como Executar

```powershell
python main.py
```

Ou via `Iniciar.bat` / `main.pyw` para executar sem console.

Dependências (já instaladas):
```powershell
pip install PySide6 send2trash
```

---

## Performance

### I/O
- `os.scandir` em vez de `os.walk`/`os.listdir` — retorna `stat` sem syscall extra
- Traversal iterativo (stack) — sem overhead de recursão Python
- `dir_size` sequencial (evita thrashing de I/O com threads concorrentes)
- `follow_symlinks=False` — evita seguir junctions do Windows
- Empty scan para no **primeiro filho** encontrado (early break)

### Threading
- Cada aba tem seu próprio `ScanWorker` rodando em `QThread` independente
- Várias abas podem escanear simultaneamente
- `dir_size` recebe `self._check` para cancelamento cooperativo dentro do loop

---

## Bugs/Issues Conhecidos (Resolvidos)

| Issue | Causa | Fix |
|---|---|---|
| Startup crash: `ValueError: not enough values to unpack` | `CARD_CFG` com tuplas de 3 elementos, loop esperava 4 | Separar icon do label: `(key, icon, label, color)` |
| `OverflowError` com tamanhos >2GB | Signal usava `int` (32-bit C int) | Mudar para `object` nos parâmetros de tamanho: `Signal(str, object, str)` |
| Checkbox não aparecia | `setCheckState` depois de `setText` + stylesheet `QTreeWidget::item` interferindo | Flags antes de setters + remover `QTreeWidget::item{padding}` |
| SetStyle Fusion reduz a barra de título | Usar tema nativo do Windows | Manter `app.setStyle("Fusion")` opcional **ou** remover para barra nativa; verificar visualmente |
| Classe `_SizeWorker` (paralela) referida na doc | Doc registrava worker que não existe mais | `dir_size` é sequencial; remover menções a `_SizeWorker` |
| Checkbox invisível (branco sobre branco) | Nenhum estilo visual no indicador | `QTreeWidget::indicator:checked` com fundo azul + `:unchecked` com borda cinza |
| Seleção "confusa" — clique no texto não marca | `itemClicked` não conectado | `_toggle_item()` — clique em col 1+ alterna checkbox; col 0 deixa nativo do Qt |

---

## Diretrizes para Desenvolvimento Futuro

### Convenções de Código
- Sem comentários em bloco no código (manter limpo)
- Nomes em inglês para classes/funções, UI em português (para o usuário final)
- Signals com tipos explícitos: `str`, `int`, `object` (não usar `'q'` ou tipos C++)
- Estilos via variáveis no dicionário `C` ou constantes `BTN*`

### Adicionando um Novo Tipo de Scan
1. Adicionar constante em `TABS` e `CARD_CFG`
2. Criar método `_scan_novo()` em `ScanWorker`
3. Adicionar dispatcher no `if/elif` de `ScanWorker.run()`
4. Opcional: adicionar cor/ícone em `CARD_CFG`

### Adicionando Novo Cache Conhecido
Adicionar caminho relativo a `AppData` em `KNOWN_CACHE`:
```python
r'Local\MeuApp\Cache',
```

### Testando
- Não há test suite formal. Testar manualmente:
  ```powershell
  python main.py
  ```
- Verificar: startup sem erros, scan em cada aba, checkboxes, cancelamento, deleção

### Debug
- Adicionar prints no callback `_add` para verificar chegada de itens
- Usar `ScanWorker` standalone com signals para testar scan sem UI
