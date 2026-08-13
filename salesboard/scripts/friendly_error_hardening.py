from pathlib import Path

path = Path('salesboard/app/app.js')
text = path.read_text(encoding='utf-8')

old = '''    if (code === 'user_already_exists' || message.includes('already registered') || message.includes('already exists')) return 'Já existe uma conta com este e-mail. Entre normalmente ou use “Esqueci a senha”.';
    if (message.includes('password should be')) return 'A senha não atende aos requisitos de segurança. Use pelo menos 8 caracteres.';
    if (code.includes('otp_expired') || code.includes('token_expired') || message.includes('otp expired') || message.includes('token has expired') || message.includes('invalid token')) return 'Este link não é mais válido. Solicite um novo link e use apenas o e-mail mais recente.';
    return friendlyError(error);
'''
new = '''    if (code === 'user_already_exists' || message.includes('already registered') || message.includes('already exists')) return 'Já existe uma conta com este e-mail. Entre normalmente ou use “Esqueci a senha”.';
    if (code === 'email_address_invalid' || message.includes('email address') && message.includes('invalid')) return 'Este endereço de e-mail não foi aceito. Confira se ele está correto e tente novamente.';
    if (code === 'signup_disabled') return 'A criação de novas contas está temporariamente indisponível. Tente novamente mais tarde.';
    if (code === 'weak_password' || message.includes('password should be')) return 'A senha não atende aos requisitos de segurança. Use pelo menos 8 caracteres.';
    if (code === 'same_password' || message.includes('same password')) return 'A nova senha precisa ser diferente da senha atual.';
    if (code === 'user_banned') return 'Este acesso está temporariamente indisponível. Entre em contato com o suporte se precisar de ajuda.';
    if (code === 'over_request_rate_limit' || message.includes('too many requests')) return 'Foram feitas muitas tentativas em pouco tempo. Aguarde alguns instantes e tente novamente.';
    if (message.includes('failed to fetch') || message.includes('network') || message.includes('load failed')) return 'Não foi possível conectar ao serviço de autenticação. Verifique sua internet e tente novamente.';
    if (code.includes('otp_expired') || code.includes('token_expired') || message.includes('otp expired') || message.includes('token has expired') || message.includes('invalid token')) return 'Este link não é mais válido. Solicite um novo link e use apenas o e-mail mais recente.';
    return 'Não foi possível concluir esta ação de acesso. Tente novamente; se o problema continuar, use outra forma de entrada.';
'''
if text.count(old) != 1:
    raise SystemExit(f'auth error anchor count={text.count(old)}')
text = text.replace(old, new, 1)

old = '''    if (message.includes('CATEGORY_TYPE_MISMATCH')) return 'A categoria escolhida não combina com o tipo do lançamento.';
    if (message.includes('foreign key')) return 'Este item está sendo usado em lançamentos e não pode ser excluído agora.';
    return message.length > 180 ? 'Não foi possível concluir a operação. Tente novamente.' : message;
'''
new = '''    if (message.includes('CATEGORY_TYPE_MISMATCH')) return 'A categoria escolhida não combina com o tipo do lançamento.';
    if (message.includes('account_is_archived')) return 'Esta conta está arquivada e não pode receber novos lançamentos. Reative-a nas Configurações para usá-la novamente.';
    if (message.includes('category_is_archived')) return 'Esta categoria está arquivada e não pode ser usada em novos lançamentos. Reative-a nas Configurações para usá-la novamente.';
    if (message.includes('foreign key')) return 'Este item possui histórico vinculado e não pode ser apagado diretamente.';
    if (message.includes('JWT') || message.includes('jwt') || message.includes('Session not found') || message.includes('session_not_found') || /\\b(401|403)\\b/.test(message)) return 'Sua sessão não é mais válida. Entre novamente para continuar.';
    if (message.toLowerCase().includes('failed to fetch') || message.toLowerCase().includes('network') || message.toLowerCase().includes('load failed')) return 'Não foi possível conectar ao servidor. Verifique sua internet e tente novamente.';
    if (/sqlstate|postgres|relation |schema cache|permission denied|violates|pgrst|prepared statement/i.test(message)) return 'Não foi possível concluir a operação por uma falha interna. Atualize os dados e tente novamente.';
    return message.length > 140 ? 'Não foi possível concluir a operação. Tente novamente.' : message;
'''
if text.count(old) != 1:
    raise SystemExit(f'friendly error anchor count={text.count(old)}')
text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')
print('User-facing errors hardened.')
