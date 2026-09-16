const vscode = require('vscode');
const http = require('http');
const path = require('path');

const WATCH_LIST = new Set([
    'claude.md',
    'agents.md',
    'gemini.md',
    '.cursorrules',
    '.windsurfrules',
    'copilot-instructions.md',
    'mcp.json',
    '.mcp.json',
    'mcp-config.json',
    'settings.json'
]);

function activate(context) {
    const outputChannel = vscode.window.createOutputChannel('SENTINEL.md');
    outputChannel.appendLine('SENTINEL.md extension active');

    const saveDisposable = vscode.workspace.onDidSaveTextDocument(document => {
        const basename = path.basename(document.fileName).toLowerCase();
        
        if (!WATCH_LIST.has(basename)) {
            return;
        }

        const fileContent = document.getText();
        const boundary = '----WebKitFormBoundarySentinel' + Math.random().toString(36).substring(2);
        
        const bodyBuffer = Buffer.from(
            `--${boundary}\r\n` +
            `Content-Disposition: form-data; name="file"; filename="${path.basename(document.fileName)}"\r\n` +
            `Content-Type: application/octet-stream\r\n\r\n` +
            `${fileContent}\r\n` +
            `--${boundary}--\r\n`,
            'utf-8'
        );

        const options = {
            hostname: '127.0.0.1',
            port: 8000,
            path: '/scan/file',
            method: 'POST',
            headers: {
                'Content-Type': `multipart/form-data; boundary=${boundary}`,
                'Content-Length': bodyBuffer.length
            }
        };

        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', chunk => { data += chunk; });
            res.on('end', () => {
                if (res.statusCode !== 200) {
                    outputChannel.appendLine(`Scan failed with status ${res.statusCode}: ${data}`);
                    return;
                }
                
                try {
                    const result = JSON.parse(data);
                    
                    outputChannel.appendLine(`Scan results for ${basename}:`);
                    outputChannel.appendLine(JSON.stringify(result, null, 2));

                    const score = result.trust_score;
                    const band = result.color_band;
                    const findingsCount = result.findings ? result.findings.length : 0;
                    
                    if (band === 'green') {
                        vscode.window.showInformationMessage(`SENTINEL: ${result.filename} — ${score}/100 CLEAN`);
                    } else if (band === 'amber') {
                        vscode.window.showWarningMessage(`SENTINEL: ${result.filename} — ${score}/100 SUSPICIOUS (${findingsCount} finding(s))`);
                    } else if (band === 'red') {
                        vscode.window.showErrorMessage(`SENTINEL: ${result.filename} — ${score}/100 COMPROMISED (${findingsCount} finding(s))`);
                    }
                } catch (e) {
                    outputChannel.appendLine(`Error parsing response: ${e.message}`);
                }
            });
        });

        req.on('error', (e) => {
            outputChannel.appendLine(`Network error, scan skipped for ${basename}: ${e.message}`);
        });

        req.write(bodyBuffer);
        req.end();
    });

    context.subscriptions.push(saveDisposable);
    context.subscriptions.push(outputChannel);
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
}
