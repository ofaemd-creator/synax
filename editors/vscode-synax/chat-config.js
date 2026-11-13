/** Shared, testable configuration boundary for the chat subprocess. */
const path = require('node:path');
const fs = require('node:fs');

function chatEnvironment(config, inherited) {
    const env = { ...inherited };
    const modelPath = config.get('llm.modelPath');
    if (modelPath) env.SYNAX_MODEL_PATH = modelPath;
    return env;
}

function findChatScript(config, folders, extensionRoot) {
    const custom = config.get('chat.scriptPath');
    const siblingBundles = [];
    try {
        const parent = path.dirname(extensionRoot);
        if (fs.existsSync(parent)) {
            const dirs = fs.readdirSync(parent)
                .filter(d => d.startsWith('synaxcode.synax-lang-'))
                .sort()
                .reverse();
            for (const d of dirs) {
                siblingBundles.push(path.join(parent, d, 'bundled', 'synax_chat.py'));
            }
        }
    } catch (e) {}

    const candidates = [
        ...(custom ? [custom.trim()] : []),
        ...(folders || []).map(f => path.join(f.uri.fsPath, 'synax_chat.py')),
        path.join(extensionRoot, 'bundled', 'synax_chat.py'),
        ...siblingBundles,
        '/Users/o.farukaydin/.gemini/antigravity/scratch/synax/synax_chat.py'
    ];
    const script = candidates.find(p => fs.existsSync(p));
    if (!script) throw new Error('SYNAX chat backend not found. Configure synax.chat.scriptPath.');
    return { script, cwd: path.dirname(script) };
}
module.exports = { chatEnvironment, findChatScript };
