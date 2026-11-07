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
    const candidates = [
        ...(custom ? [custom.trim()] : []),
        ...(folders || []).map(f => path.join(f.uri.fsPath, 'synax_chat.py')),
        path.join(extensionRoot, 'bundled', 'synax_chat.py')
    ];
    const script = candidates.find(p => fs.existsSync(p));
    if (!script) throw new Error('SYNAX chat backend not found. Configure synax.chat.scriptPath.');
    return { script, cwd: path.dirname(script) };
}
module.exports = { chatEnvironment, findChatScript };
