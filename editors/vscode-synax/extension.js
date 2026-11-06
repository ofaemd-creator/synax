const vscode = require('vscode');
const child_process = require('child_process');
const path = require('path');
const fs = require('fs');

/**
 * SYNAX Code VS Code Extension — AI Chat & Autopoiesis Controller
 */
function activate(context) {
    console.log('[SYNAX] VS Code Extension v0.6.0 activated.');

    const provider = new SynaxChatViewProvider(context.extensionUri, context);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(SynaxChatViewProvider.viewType, provider, {
            webviewOptions: { retainContextWhenHidden: true }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('synax.openChat', () => {
            vscode.commands.executeCommand('workbench.view.extension.synax-sidebar');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('synax.teachSkill', async () => {
            const concept = await vscode.window.showInputBox({
                prompt: 'Edinilecek Yeni Becerinin / Kavramın Adı:',
                placeHolder: 'örn: serebral_oksijen_indeksi'
            });
            if (!concept) return;

            const formula = await vscode.window.showInputBox({
                prompt: `'${concept}' Becerisinin Matematiksel / Nöral Formülü:`,
                placeHolder: 'örn: relu(a - b) * 0.75 + bias'
            });
            if (!formula) return;

            provider.teachSkillDirect(concept, formula);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('synax.compileCurrent', () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showWarningMessage('Aktif bir SYNAX (.sx) dosyası açık değil.');
                return;
            }
            provider.compileCurrentDocument(editor.document.getText());
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('synax.checkCurrent', () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;
            provider.checkCurrentDocument(editor.document.fileName);
        })
    );
}

class SynaxChatViewProvider {
    static viewType = 'synax.chatView';

    constructor(extensionUri, context) {
        this._extensionUri = extensionUri;
        this._context = context;
        this._view = undefined;
        this._proc = null;
        this._rpcPending = new Map();
        this._rpcId = 0;
    }

    resolveWebviewView(webviewView, context, _token) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        webviewView.webview.html = this._getHtmlForWebview();

        webviewView.webview.onDidReceiveMessage(async (data) => {
            switch (data.type) {
                case 'sendMessage':
                    await this._handleUserMessage(data.text);
                    break;
                case 'insertCode':
                    await this._insertCodeToActiveEditor(data.code);
                    break;
                case 'compileCode':
                    await this.compileCurrentDocument(data.code);
                    break;
                case 'ready':
                    this._ensureBackend();
                    break;
            }
        });

        this._ensureBackend();
    }

    _findSynaxPath() {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (workspaceFolders) {
            for (const f of workspaceFolders) {
                const p = path.join(f.uri.fsPath, 'synax_chat.py');
                if (fs.existsSync(p)) return { script: p, cwd: f.uri.fsPath };
            }
        }
        // Fallback to configured or global
        return { script: 'synax_chat.py', cwd: process.cwd() };
    }

    _ensureBackend() {
        if (this._proc && !this._proc.killed) return;

        const info = this._findSynaxPath();
        const pythonBin = vscode.workspace.getConfiguration('python').get('defaultInterpreterPath') || 'python3';

        try {
            this._proc = child_process.spawn(pythonBin, [info.script, '--json-rpc'], {
                cwd: info.cwd,
                env: { ...process.env, PYTHONPATH: `${info.cwd}:${info.cwd}/src` }
            });

            let buffer = '';
            this._proc.stdout.on('data', (chunk) => {
                buffer += chunk.toString('utf-8');
                const lines = buffer.split('\n');
                buffer = lines.pop(); // keep remainder

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const json = JSON.parse(line);
                        this._handleRpcResponse(json);
                    } catch (e) {
                        console.error('[SYNAX RPC Parse Error]', e, line);
                    }
                }
            });

            this._proc.stderr.on('data', (err) => {
                console.error('[SYNAX Backend stderr]', err.toString());
            });

            this._proc.on('close', (code) => {
                console.log(`[SYNAX Backend exited with ${code}]`);
                this._proc = null;
            });

            this._postToWebview({ type: 'status', connected: true });
        } catch (e) {
            console.error('[SYNAX Backend Launch Failed]', e);
            this._postToWebview({ type: 'status', connected: false, error: e.message });
        }
    }

    _sendRpc(method, params) {
        this._ensureBackend();
        return new Promise((resolve, reject) => {
            const id = ++this._rpcId;
            this._rpcPending.set(id, { resolve, reject });
            const payload = JSON.stringify({ id, method, params }) + '\n';
            try {
                this._proc.stdin.write(payload);
            } catch (err) {
                this._rpcPending.delete(id);
                reject(err);
            }
        });
    }

    _handleRpcResponse(resp) {
        const id = resp.id;
        if (id && this._rpcPending.has(id)) {
            const { resolve, reject } = this._rpcPending.get(id);
            this._rpcPending.delete(id);
            if (resp.error) {
                reject(new Error(resp.error));
            } else {
                resolve(resp.result);
            }
        }
    }

    async _handleUserMessage(text) {
        if (!text || !text.trim()) return;

        // Visual feedback to user
        this._postToWebview({ type: 'addMessage', sender: 'user', text: text });
        this._postToWebview({ type: 'setTyping', typing: true });

        const activeEditor = vscode.window.activeTextEditor;
        const editorText = activeEditor ? activeEditor.document.getText() : '';

        try {
            const result = await this._sendRpc('chat', {
                message: text,
                context: {
                    editorText: editorText,
                    fileName: activeEditor ? activeEditor.document.fileName : ''
                }
            });

            this._postToWebview({
                type: 'addMessage',
                sender: 'assistant',
                text: result.text || '',
                code: result.code || null,
                language: result.language || 'synax',
                action: result.action || null
            });
        } catch (err) {
            this._postToWebview({
                type: 'addMessage',
                sender: 'assistant',
                text: `❌ Hata: ${err.message}`,
                action: 'error'
            });
        } finally {
            this._postToWebview({ type: 'setTyping', typing: false });
        }
    }

    async teachSkillDirect(concept, formula) {
        const command = `kendine şu beceriyi edin: ${concept} = ${formula}`;
        await this._handleUserMessage(command);
    }

    async compileCurrentDocument(sxCode) {
        const command = `derle:\n${sxCode}`;
        await this._handleUserMessage(command);
    }

    async checkCurrentDocument(filePath) {
        const command = `kontrol et: ${filePath}`;
        await this._handleUserMessage(command);
    }

    async _insertCodeToActiveEditor(code) {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            const doc = await vscode.workspace.openTextDocument({ content: code, language: 'synax' });
            await vscode.window.showTextDocument(doc);
            return;
        }

        editor.edit(editBuilder => {
            const selection = editor.selection;
            if (selection.isEmpty) {
                editBuilder.insert(selection.active, '\n' + code + '\n');
            } else {
                editBuilder.replace(selection, code);
            }
        });
        vscode.window.showInformationMessage('✓ Kod aktif SYNAX editörüne başarıyla eklendi.');
    }

    _postToWebview(msg) {
        if (this._view) {
            this._view.webview.postMessage(msg);
        }
    }

    _getHtmlForWebview() {
        return `<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SYNAX Code AI Chat</title>
  <style>
    :root {
      --bg: var(--vscode-editor-background, #0f172a);
      --fg: var(--vscode-editor-foreground, #e2e8f0);
      --card: var(--vscode-sideBar-background, #1e293b);
      --border: var(--vscode-widget-border, #334155);
      --accent: #38bdf8;
      --accent-hover: #0284c7;
      --green: #10b981;
      --amber: #f59e0b;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: var(--vscode-font-family, -apple-system, sans-serif); }
    body {
      background: var(--bg);
      color: var(--fg);
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
      font-size: 13px;
    }
    #header {
      padding: 10px 14px;
      background: rgba(30, 41, 59, 0.7);
      backdrop-filter: blur(8px);
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
      font-weight: 600;
      color: var(--green);
    }
    .dot {
      width: 7px; height: 7px; border-radius: 50%; background: var(--green);
      box-shadow: 0 0 8px var(--green);
      animation: pulse 2s infinite;
    }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
    
    #pills {
      padding: 8px 12px;
      display: flex;
      gap: 6px;
      overflow-x: auto;
      border-bottom: 1px solid rgba(51, 65, 85, 0.4);
    }
    .pill {
      background: rgba(56, 189, 248, 0.1);
      border: 1px solid rgba(56, 189, 248, 0.25);
      color: var(--accent);
      padding: 4px 9px;
      border-radius: 12px;
      font-size: 11px;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.2s;
    }
    .pill:hover { background: rgba(56, 189, 248, 0.2); border-color: var(--accent); }

    #messages {
      flex: 1;
      overflow-y: auto;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .msg {
      max-width: 95%;
      padding: 10px 13px;
      border-radius: 10px;
      line-height: 1.5;
      word-break: break-word;
    }
    .msg.user {
      align-self: flex-end;
      background: #0284c7;
      color: white;
      border-bottom-right-radius: 2px;
    }
    .msg.assistant {
      align-self: flex-start;
      background: var(--card);
      border: 1px solid var(--border);
      border-bottom-left-radius: 2px;
    }
    .code-block {
      margin-top: 8px;
      background: #090d16;
      border: 1px solid var(--border);
      border-radius: 6px;
      overflow: hidden;
    }
    .code-header {
      background: #131b2e;
      padding: 5px 10px;
      font-size: 11px;
      color: #94a3b8;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid rgba(51, 65, 85, 0.5);
    }
    .code-actions button {
      background: transparent;
      border: 1px solid #475569;
      color: #cbd5e1;
      padding: 2px 7px;
      border-radius: 4px;
      font-size: 10px;
      cursor: pointer;
      margin-left: 4px;
    }
    .code-actions button:hover {
      background: #334155;
      color: white;
    }
    pre {
      padding: 10px;
      font-family: var(--vscode-editor-font-family, monospace);
      font-size: 12px;
      overflow-x: auto;
      color: #38bdf8;
    }
    #input-container {
      padding: 10px 14px;
      border-top: 1px solid var(--border);
      background: rgba(30, 41, 59, 0.5);
      display: flex;
      gap: 8px;
    }
    textarea {
      flex: 1;
      background: var(--card);
      border: 1px solid var(--border);
      color: var(--fg);
      padding: 8px 10px;
      border-radius: 6px;
      resize: none;
      height: 38px;
      outline: none;
      font-size: 12px;
    }
    textarea:focus { border-color: var(--accent); }
    button#send {
      background: var(--accent);
      color: #0f172a;
      border: none;
      border-radius: 6px;
      padding: 0 14px;
      font-weight: 700;
      font-size: 12px;
      cursor: pointer;
      transition: background 0.2s;
    }
    button#send:hover { background: var(--accent-hover); color: white; }
    .typing {
      font-style: italic;
      color: #94a3b8;
      font-size: 11px;
      display: none;
    }
  </style>
</head>
<body>
  <div id="header">
    <div style="font-weight: 700; display:flex; align-items:center; gap:6px;">
      <span>🧬 SYNAX Code</span>
      <span style="font-size:10px; background:#334155; padding:1px 5px; border-radius:4px; color:#cbd5e1;">v0.6.0</span>
    </div>
    <div class="badge"><div class="dot"></div><span>Autopoiesis Aktif</span></div>
  </div>

  <div id="pills">
    <div class="pill" onclick="sendPrompt('kendine şu beceriyi edin: serebral_perfuzyon = relu(a - b) * bias')">🧠 Beceri Edin</div>
    <div class="pill" onclick="sendPrompt('kan basıncı ile intrakraniyal basınç farkının pozitif kısmını al')">🩺 CPP Analizi</div>
    <div class="pill" onclick="sendPrompt('hafızanı göster')">📚 Hafıza</div>
    <div class="pill" onclick="sendPrompt('durum')">⚡ Donanım</div>
  </div>

  <div id="messages">
    <div class="msg assistant">
      Merhaba Dr. Aydın! Ben <strong>SYNAX Code</strong> AI Asistanınızım.<br><br>
      Tıpkı Codex veya Claude Code gibi benimle serbest sohbet edebilir, <code>.sx</code> çekirdekleri ürettirebilir, donanım optimizasyonu yapabilirsiniz.<br><br>
      💡 <strong>En büyük farkım:</strong> Bana <em>"kendine şu beceriyi edin: [isim] = [formül]"</em> dediğinizde, cebirsel sadeleştirme ve donanım doğrulaması yaparak o beceriyi anında kriptografik hafızama işler ve kalıcı olarak öğrenirim!
    </div>
  </div>

  <div id="typing-indicator" style="padding: 0 14px 6px 14px;" class="typing">Synax düşünüyor ve silikonda doğrulanıyor...</div>

  <div id="input-container">
    <textarea id="prompt" placeholder="Komut verin veya 'kendine şu beceriyi edin: X = Y' yazın..." onkeydown="handleKey(event)"></textarea>
    <button id="send" onclick="submitMessage()">Gönder</button>
  </div>

  <script>
    const vscode = acquireVsCodeApi();
    const messages = document.getElementById('messages');
    const prompt = document.getElementById('prompt');
    const typing = document.getElementById('typing-indicator');

    window.addEventListener('message', event => {
      const msg = event.data;
      if (msg.type === 'addMessage') {
        renderMessage(msg);
      } else if (msg.type === 'setTyping') {
        typing.style.display = msg.typing ? 'block' : 'none';
        messages.scrollTop = messages.scrollHeight;
      }
    });

    function handleKey(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        submitMessage();
      }
    }

    function sendPrompt(text) {
      prompt.value = text;
      submitMessage();
    }

    function submitMessage() {
      const text = prompt.value.trim();
      if (!text) return;
      prompt.value = '';
      vscode.postMessage({ type: 'sendMessage', text: text });
    }

    function renderMessage(data) {
      const div = document.createElement('div');
      div.className = 'msg ' + data.sender;

      // Basit markdown biçimlendirme (bold, code, lists)
      let formatted = data.text
        .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
        .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
        .replace(/\`([^\\`]+)\`/g, '<code style="background:rgba(0,0,0,0.3); padding:1px 4px; border-radius:3px; color:#38bdf8;">$1</code>')
        .replace(/\\n/g, '<br>');

      div.innerHTML = formatted;

      if (data.code) {
        const codeBox = document.createElement('div');
        codeBox.className = 'code-block';
        codeBox.innerHTML = \`
          <div class="code-header">
            <span>\${data.language || 'synax'}</span>
            <div class="code-actions">
              <button onclick="insertCode(\\\`\${escapeCode(data.code)}\\\`)">Editöre Ekle</button>
              <button onclick="copyCode(\\\`\${escapeCode(data.code)}\\\`)">Kopyala</button>
            </div>
          </div>
          <pre><code>\${escapeHtml(data.code)}</code></pre>
        \`;
        div.appendChild(codeBox);
      }

      messages.appendChild(div);
      messages.scrollTop = messages.scrollHeight;
    }

    function escapeCode(str) {
      return str.replace(/\\/g, '\\\\').replace(/\`/g, '\\\`').replace(/\\\$/g, '\\\\$');
    }

    function escapeHtml(str) {
      return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function insertCode(code) {
      vscode.postMessage({ type: 'insertCode', code: code });
    }

    function copyCode(code) {
      navigator.clipboard.writeText(code);
    }

    // Ready signal
    vscode.postMessage({ type: 'ready' });
  </script>
</body>
</html>`;
    }
}

function deactivate() {
    console.log('[SYNAX] VS Code Extension deactivated.');
}

module.exports = {
    activate,
    deactivate
};
