const { test } = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { chatEnvironment, findChatScript } = require('../chat-config');
const config = values => ({ get: key => values[key] });

test('chat selects owned weights without configuring an external provider', () => {
    const env = chatEnvironment(config({ 'llm.modelPath': '/models/SynaxLLM' }), {});
    assert.equal(env.SYNAX_MODEL_PATH, '/models/SynaxLLM');
    assert.equal(env.SYNAX_LLM_BASE_URL, undefined);
});

test('workspace backend takes priority over bundled runtime', () => {
    const root = path.resolve(__dirname, '../../..');
    const result = findChatScript(config({}), [{ uri: { fsPath: root } }], path.dirname(__dirname));
    assert.equal(result.script, path.join(root, 'synax_chat.py'));
});

test('standalone installation selects bundled runtime', () => {
    const ext = path.dirname(__dirname);
    const result = findChatScript(config({}), [], ext);
    assert.equal(result.script, path.join(ext, 'bundled/synax_chat.py'));
});
