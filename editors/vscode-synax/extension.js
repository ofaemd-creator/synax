const { chatEnvironment, findChatScript } = require('./chat-config');
const vscode = require('vscode');
const child_process = require('child_process');
const path = require('path');
const fs = require('fs');

/**
 * SYNAX Code VS Code Extension — AI Chat & Autopoietic Neuro-Symbolic Evolution Controller
 * Version: 0.8.0
 */
function activate(context) {
    console.log('[SYNAX] VS Code Extension v0.8.0 activated.');

    const provider = new SynaxChatViewProvider(context.extensionUri, context);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(SynaxChatViewProvider.viewType, provider, {
            webviewOptions: { retainContextWhenHidden: true }
        })
    );

    // ─────────────────────────────────────────────────────────────────
    // CodeLens Provider: Live inline action buttons above kernel & intent
    // ─────────────────────────────────────────────────────────────────
    context.subscriptions.push(
        vscode.languages.registerCodeLensProvider({ language: 'synax' }, {
            provideCodeLenses(document, token) {
                const lenses = [];
                const text = document.getText();
                const lines = text.split('\n');

                for (let i = 0; i < lines.length; i++) {
                    const line = lines[i];

                    // Kernel definition CodeLens
                    const mKernel = line.match(/^\s*kernel\s+([A-Za-z0-9_]+)/);
                    if (mKernel) {
                        const kName = mKernel[1];
                        const range = new vscode.Range(i, 0, i, line.length);
                        lenses.push(new vscode.CodeLens(range, {
                            title: `▶️ SYNAX Çalıştır & Doğrula (0-ULP Run)`,
                            command: 'synax.runKernel',
                            arguments: [document.uri.toString(), kName, i]
                        }));
                        lenses.push(new vscode.CodeLens(range, {
                            title: `⚡ SYNAX Evrimi Yarıştır: [ARM64 NEON / AVX2] [Arena]`,
                            command: 'synax.evolveKernel',
                            arguments: [document.uri.toString(), kName, i]
                        }));
                    }

                    // Intent declaration CodeLens
                    const mIntent = line.match(/^\s*intent\s+"([^"]+)"/);
                    if (mIntent) {
                        const intentDesc = mIntent[1];
                        const short = intentDesc.length > 32 ? intentDesc.slice(0, 32) + '...' : intentDesc;
                        const range = new vscode.Range(i, 0, i, line.length);
                        lenses.push(new vscode.CodeLens(range, {
                            title: `🧬 Niyetten Otonom Sentezle: "${short}"`,
                            command: 'synax.synthesizeFromIntent',
                            arguments: [document.uri.toString(), i, intentDesc]
                        }));
                    }
                }
                return lenses;
            }
        })
    );

    // ─────────────────────────────────────────────────────────────────
    // Completion Item Provider: Neuro-Symbolic intelligent completions
    // ─────────────────────────────────────────────────────────────────
    context.subscriptions.push(
        vscode.languages.registerCompletionItemProvider(
            { language: 'synax' },
            {
                provideCompletionItems(document, position, token, ctx) {
                    const items = [];

                    // intent snippet
                    const itemIntent = new vscode.CompletionItem('intent', vscode.CompletionItemKind.Snippet);
                    itemIntent.detail = 'SYNAX Nöro-Sembolik Niyet Deklarasyonu';
                    itemIntent.documentation = new vscode.MarkdownString('Doğal dilde klinik veya matematiksel niyeti belirtir; LLM ve genetik mutator 4 farklı kod varyantı üretir.');
                    itemIntent.insertText = new vscode.SnippetString('intent "${1:klinik veya sensör işlem niyeti}"\nsafety {\n    nonfinite = heal(0.0)\n    clamp = (${2:-50.0}, ${3:300.0})\n}\n');
                    items.push(itemIntent);

                    // kernel snippet
                    const itemKernel = new vscode.CompletionItem('kernel', vscode.CompletionItemKind.Snippet);
                    itemKernel.detail = 'SYNAX Soma Çekirdeği';
                    itemKernel.insertText = new vscode.SnippetString('kernel ${1:name}(${2:a: tensor<f32, N>}):\n    safety {\n        nonfinite = heal(0.0)\n    }\n    let ${3:result} = ${4:a}\n    return ${3:result}\n');
                    items.push(itemKernel);

                    // safety snippet
                    const itemSafety = new vscode.CompletionItem('safety', vscode.CompletionItemKind.Snippet);
                    itemSafety.detail = 'Ranvier Düğümü İmmün Kalkanı';
                    itemSafety.insertText = new vscode.SnippetString('safety {\n    nonfinite = ${1|heal(0.0),reject,zero_output|}\n    clamp = (${2:0.0}, ${3:300.0})\n}\n');
                    items.push(itemSafety);

                    // builtins
                    const funcs = [
                        ['select', 'select(cond, val_true, val_false) - Dallanmasız Koşullu Seçici (Branchless Mux)', 'select(${1:cond}, ${2:val_true}, ${3:val_false})'],
                        ['fma', 'fma(a, b, c) - Birleşik Çarpma-Toplama (a * b + c)', 'fma(${1:a}, ${2:b}, ${3:c})'],
                        ['clamp', 'clamp(x, lo, hi) - Akson Eşikleme', 'clamp(${1:x}, ${2:0.0}, ${3:300.0})'],
                        ['relu', 'relu(x) - Doğrultucu Eşik Fonksiyonu', 'relu(${1:x})'],
                        ['sigmoid', 'sigmoid(x) - Lojistik Nöral Kapı', 'sigmoid(${1:x})'],
                        ['tanh', 'tanh(x) - Hiperbolik Tanjant Aktivasyonu', 'tanh(${1:x})'],
                        ['sum', 'sum(x) - Dendritik Uzaysal & Zamansal Toplama', 'sum(${1:x})'],
                        ['mean', 'mean(x) - Dendritik Ortalama Potansiyel', 'mean(${1:x})'],
                        ['l2_norm', 'l2_norm(x) - Dendritik Sinyal Enerjisi (L2 Norm)', 'l2_norm(${1:x})'],
                        ['dot', 'dot(a, b) - Sinaptik Nokta Çarpımı', 'dot(${1:a}, ${2:b})'],
                    ];
                    for (const [name, detail, snip] of funcs) {
                        const it = new vscode.CompletionItem(name, vscode.CompletionItemKind.Function);
                        it.detail = detail;
                        it.insertText = new vscode.SnippetString(snip);
                        items.push(it);
                    }

                    return items;
                }
            },
            '"', '{', '(', ' '
        )
    );

    // ─────────────────────────────────────────────────────────────────
    // Commands Registration
    // ─────────────────────────────────────────────────────────────────
    context.subscriptions.push(
        vscode.commands.registerCommand('synax.openChat', () => {
            vscode.commands.executeCommand('workbench.view.extension.synax-sidebar');
            provider.switchTab('chat');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('synax.openEvolutionArena', () => {
            vscode.commands.executeCommand('workbench.view.extension.synax-sidebar');
            provider.switchTab('arena');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('synax.evolveKernel', async (uriStr, kernelName, line) => {
            vscode.commands.executeCommand('workbench.view.extension.synax-sidebar');
            provider.switchTab('arena');
            const editor = vscode.window.activeTextEditor;
            const code = editor ? editor.document.getText() : '';
            await provider.evolveActiveKernel(code, kernelName);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('synax.synthesizeFromIntent', async (uriStr, line, intentDesc) => {
            let intent = intentDesc;
            if (!intent) {
                intent = await vscode.window.showInputBox({
                    prompt: 'Otonom Kod Sentezi İçin Klinik / Matematiksel Niyetinizi Girin:',
                    placeHolder: 'örn: kan basıncı ile intrakraniyal basınç farkının pozitif kısmını al'
                });
            }
            if (!intent) return;

            vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: `🧬 SYNAX: "${intent}" niyetinden 4 aday algoritma sentezleniyor...`,
                cancellable: false
            }, async () => {
                const res = await provider.synthesizeFromIntent(intent);
                if (res && res.best_code) {
                    const editor = vscode.window.activeTextEditor;
                    if (editor) {
                        editor.edit(editBuilder => {
                            const pos = editor.selection.active;
                            editBuilder.insert(pos, '\n' + res.best_code + '\n');
                        });
                        vscode.window.showInformationMessage(`✓ SYNAX: Sentezlenen doğrulanmış çekirdek editöre eklendi! (Varyant: ${res.winner_id})`);
                    }
                }
            });
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('synax.showArenaReport', () => {
            vscode.commands.executeCommand('workbench.view.extension.synax-sidebar');
            provider.switchTab('arena');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('synax.toggleDreamMode', () => {
            provider.toggleDreamMode();
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
        vscode.commands.registerCommand('synax.runKernel', async () => {
            vscode.commands.executeCommand('workbench.view.extension.synax-sidebar');
            provider.switchTab('chat');
            const editor = vscode.window.activeTextEditor;
            const code = editor ? editor.document.getText() : '';
            await provider._handleUserMessage(code ? `/run ${code}` : '/run');
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

    context.subscriptions.push(
        vscode.commands.registerCommand('synax.reconnectBackend', () => {
            provider._restartBackend();
            vscode.window.showInformationMessage('🔄 SYNAX Backend bağlantısı yenilendi.');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('synax.disconnectBackend', () => {
            provider._disconnectBackend();
            vscode.window.showInformationMessage('⏹️ SYNAX Backend bağlantısı kesildi.');
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
        this._dreamModeEnabled = true;
        this._manualDisconnect = false;
        this._lastHtml = '';
    }

    resolveWebviewView(webviewView, context, _token) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        this._lastHtml = this._getHtmlForWebview();
        webviewView.webview.html = this._lastHtml;

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
                case 'evolveCode':
                    await this.evolveActiveKernel(data.code, data.kernelName);
                    break;
                case 'synthesizeIntent':
                    await this.synthesizeFromIntent(data.intent);
                    break;
                case 'toggleDream':
                    this.toggleDreamMode();
                    break;
                case 'ready':
                    if (this._proc && !this._proc.killed) {
                        this._postToWebview({ type: 'status', connected: true });
                    } else if (!this._manualDisconnect) {
                        this._ensureBackend();
                    } else {
                        this._postToWebview({ type: 'status', connected: false });
                    }
                    break;
                case 'reconnect':
                    this._restartBackend();
                    break;
                case 'disconnect':
                    this._disconnectBackend();
                    break;
            }
        });

        this._ensureBackend();
    }

    switchTab(tabName) {
        this._postToWebview({ type: 'switchTab', tab: tabName });
    }

    toggleDreamMode() {
        this._dreamModeEnabled = !this._dreamModeEnabled;
        const msg = this._dreamModeEnabled ? '🌙 Dream Mode (Boş Zaman Evrimi) Aktifleştirildi.' : '🌙 Dream Mode Duraklatıldı.';
        vscode.window.showInformationMessage(msg);
        this._postToWebview({ type: 'dreamStatus', enabled: this._dreamModeEnabled });
    }

    _findPythonBin() {
        const customPy = vscode.workspace.getConfiguration('synax').get('chat.pythonPath');
        if (customPy && typeof customPy === 'string' && customPy.trim() && fs.existsSync(customPy.trim())) {
            return customPy.trim();
        }

        const configPython = vscode.workspace.getConfiguration('python').get('defaultInterpreterPath');
        if (configPython && typeof configPython === 'string' && !configPython.includes('.venv-chat') && fs.existsSync(configPython)) {
            return configPython;
        }

        const candidates = [
            '/Users/o.farukaydin/.local/bin/python3',
            '/opt/homebrew/bin/python3',
            '/usr/local/bin/python3',
            '/usr/bin/python3',
            'python3'
        ];
        for (const c of candidates) {
            try {
                if (c.startsWith('/') && fs.existsSync(c)) return c;
            } catch (e) {}
        }
        return 'python3';
    }

    _findSynaxPath() {
        return findChatScript(vscode.workspace.getConfiguration('synax'),
            vscode.workspace.workspaceFolders, this._extensionUri.fsPath);
    }

    _disconnectBackend() {
        this._manualDisconnect = true;
        if (this._proc) {
            try { this._proc.kill(); } catch (e) {}
            this._proc = null;
        }
        this._postToWebview({ type: 'status', connected: false });
    }

    _restartBackend() {
        this._manualDisconnect = true;
        if (this._proc) {
            try { this._proc.kill(); } catch (e) {}
            this._proc = null;
        }
        const freshHtml = this._getHtmlForWebview();
        if (this._view && freshHtml !== this._lastHtml) {
            this._lastHtml = freshHtml;
            this._view.webview.html = freshHtml + `\n<!-- refresh:${Date.now()} -->`;
        }
        this._manualDisconnect = false;
        this._ensureBackend(true);
    }

    _ensureBackend(isReconnect = false) {
        if (this._proc && !this._proc.killed) return;
        this._manualDisconnect = false;

        const info = this._findSynaxPath();
        const pythonBin = this._findPythonBin();

        try {
            // Spawn with unbuffered stdio (-u)
            this._proc = child_process.spawn(pythonBin, ['-u', info.script, '--json-rpc'], {
                cwd: info.cwd,
                env: {
                    ...chatEnvironment(vscode.workspace.getConfiguration('synax'), process.env),
                    PYTHONUNBUFFERED: '1',
                    PYTHONPYCACHEPREFIX: path.join(this._context.globalStorageUri.fsPath, 'python-cache'),
                    PYTHONPATH: `${info.cwd}:${path.join(info.cwd, 'src')}:${process.env.PYTHONPATH || ''}`
                }
            });

            this._proc.on('error', (err) => {
                console.error('[SYNAX Backend Process Error]', err);
                this._proc = null;
                this._postToWebview({
                    type: 'status',
                    connected: false,
                    error: `Python işlemi başlatılamadı: ${err.message} (${pythonBin})`
                });
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
                const wasManual = this._manualDisconnect;
                this._postToWebview({
                    type: 'status',
                    connected: false,
                    error: (!wasManual && code !== 0 && code !== null) ? `SYNAX motoru kapandı (çıkış kodu: ${code})` : undefined
                });
            });

            this._postToWebview({ type: 'status', connected: true, reconnected: isReconnect });
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

        this._postToWebview({ type: 'addMessage', sender: 'user', text: text });
        this._postToWebview({ type: 'setTyping', typing: true });

        const activeEditor = vscode.window.activeTextEditor;
        const editorText = activeEditor ? activeEditor.document.getText() : '';
        const selectionText = activeEditor && !activeEditor.selection.isEmpty ? activeEditor.document.getText(activeEditor.selection) : '';

        try {
            const result = await this._sendRpc('chat', {
                message: text,
                context: {
                    editorText: editorText,
                    selectionText: selectionText,
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

    async evolveActiveKernel(code, kernelName) {
        this._postToWebview({ type: 'arenaStatus', status: 'evaluating', message: 'Nöral adaylar üretiliyor ve silikonda yarışıyor...' });
        try {
            const res = await this._sendRpc('evolve', {
                target: code || kernelName || 'cerebral_perfusion_pressure'
            });
            if (res && res.report) {
                this._postToWebview({
                    type: 'arenaReport',
                    report: res.report,
                    markdown: res.markdown
                });
                const w = res.report.winner;
                if (w) {
                    vscode.window.showInformationMessage(`🏆 SYNAX Evrimi Kazandı: ${w.label} (${res.report.peak_throughput_gbs} GB/s | ${res.report.speedup}x Hızlanma)`);
                }
            }
        } catch (err) {
            vscode.window.showErrorMessage(`Evrim Arenası Hatası: ${err.message}`);
            this._postToWebview({ type: 'arenaStatus', status: 'error', message: err.message });
        }
    }

    async synthesizeFromIntent(intent) {
        try {
            const res = await this._sendRpc('synthesize', { intent: intent });
            if (res && res.candidates) {
                this._postToWebview({
                    type: 'synthesisResult',
                    intent: intent,
                    best_code: res.best_code,
                    winner_id: res.winner_id,
                    candidates: res.candidates
                });
            }
            return res;
        } catch (err) {
            vscode.window.showErrorMessage(`Sentez Hatası: ${err.message}`);
            return null;
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
        const candidates = [
            path.join(this._extensionUri.fsPath, 'media', 'index.html')
        ];

        // If VS Code upgraded the extension in-place and removed the old version directory
        // before window reload, automatically discover the newest installed synax-lang-* folder.
        try {
            const extRoot = path.dirname(this._extensionUri.fsPath);
            if (fs.existsSync(extRoot)) {
                const dirs = fs.readdirSync(extRoot)
                    .filter(d => d.startsWith('synaxcode.synax-lang-'))
                    .sort()
                    .reverse();
                for (const d of dirs) {
                    candidates.push(path.join(extRoot, d, 'media', 'index.html'));
                }
            }
        } catch (e) {}

        candidates.push(
            '/Users/o.farukaydin/.gemini/antigravity/scratch/synax/editors/vscode-synax/media/index.html',
            '/Users/o.farukaydin/Desktop/AI modeller/SYNAX/proje/editors/vscode-synax/media/index.html'
        );

        for (const htmlPath of candidates) {
            try {
                if (fs.existsSync(htmlPath)) {
                    return fs.readFileSync(htmlPath, 'utf-8');
                }
            } catch (e) {}
        }
        return '<html><body><p>SYNAX UI yüklenemedi: media/index.html bulunamadı.</p></body></html>';
    }
}

function deactivate() {
    console.log('[SYNAX] VS Code Extension deactivated.');
}

module.exports = {
    activate,
    deactivate
};
