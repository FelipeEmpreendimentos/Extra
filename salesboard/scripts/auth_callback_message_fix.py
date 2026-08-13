from pathlib import Path

app = Path('salesboard/app/app.js')
html = Path('salesboard/app/index.html')
text = app.read_text(encoding='utf-8')

old = '''  function setInlineMessage(selector, message, error = false) {
    const box = $(selector);
'''
new = '''  function authCallbackMessage() {
    const code = String(params.get('error_code') || params.get('error') || '').toLowerCase();
    const description = String(params.get('error_description') || '').replace(/\\+/g, ' ').trim().toLowerCase();
    if (!code && !description) return '';
    if (code.includes('access_denied') || description.includes('access denied') || description.includes('cancel')) return 'O login foi cancelado. Nenhuma alteração foi feita na sua conta.';
    if (description.includes('invalid_client') || description.includes('client secret')) return 'O login com Google não pôde ser concluído porque a integração do provedor precisa ser revisada. Use e-mail e senha enquanto isso.';
    if (code.includes('otp_expired') || code.includes('token_expired') || description.includes('expired') || description.includes('invalid token')) return 'Este link de autenticação não é mais válido. Solicite um novo link e tente novamente.';
    return 'Não foi possível concluir a autenticação. Tente novamente; se o problema continuar, use e-mail e senha.';
  }

  function setInlineMessage(selector, message, error = false) {
    const box = $(selector);
'''
if text.count(old) != 1:
    raise SystemExit(f'callback helper anchor count={text.count(old)}')
text = text.replace(old, new, 1)

old = '''    if (!session) {
      showAuth(params.get('mode') === 'register' ? 'register' : 'login');
      return;
    }
'''
new = '''    if (!session) {
      const callbackMessage = authCallbackMessage();
      showAuth(params.get('mode') === 'register' ? 'register' : 'login');
      if (callbackMessage) setAuthMessage(callbackMessage, true);
      return;
    }
'''
if text.count(old) != 1:
    raise SystemExit(f'no-session callback anchor count={text.count(old)}')
text = text.replace(old, new, 1)
app.write_text(text, encoding='utf-8')

html_text = html.read_text(encoding='utf-8')
for old, new in [
    ('<div id="auth-message" class="auth-message" hidden></div>', '<div id="auth-message" class="auth-message" role="status" aria-live="polite" hidden></div>'),
    ('<div id="forgot-status" class="auth-message" hidden></div>', '<div id="forgot-status" class="auth-message" role="status" aria-live="polite" hidden></div>'),
    ('<div id="recovery-message" class="auth-message" hidden></div>', '<div id="recovery-message" class="auth-message" role="status" aria-live="polite" hidden></div>')
]:
    if html_text.count(old) != 1:
        raise SystemExit(f'ARIA status anchor missing: {old}')
    html_text = html_text.replace(old, new, 1)
html.write_text(html_text, encoding='utf-8')
print('Auth callback and live status messages repaired.')
