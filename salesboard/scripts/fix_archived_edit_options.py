from pathlib import Path

path = Path('salesboard/app/app.js')
text = path.read_text(encoding='utf-8')
old = '''  function renderSelectOptions(type = null) {
    const transactionType = type || $('input[name="transaction_type"]:checked')?.value || 'expense';
    $('#tx-category').innerHTML = state.categories.filter((category) => category.type === transactionType).map((category) => `<option value="${category.id}">${escapeHTML(category.icon)} ${escapeHTML(category.name)}</option>`).join('');
    $('#tx-account').innerHTML = state.accounts.map((account) => `<option value="${account.id}">${escapeHTML(account.icon)} ${escapeHTML(account.name)}</option>`).join('');
    const goalSelect = $('#tx-goal');'''
new = '''  function renderSelectOptions(type = null) {
    const transactionType = type || $('input[name="transaction_type"]:checked')?.value || 'expense';
    const editingRow = editingTransactionId ? state.transactions.find((item) => item.id === editingTransactionId) : null;
    const categoryOptions = state.categories.filter((category) => category.type === transactionType);
    const historicalCategory = editingRow?.category_id ? allCategories().find((category) => category.id === editingRow.category_id) : null;
    if (historicalCategory?.archived && historicalCategory.type === transactionType && !categoryOptions.some((category) => category.id === historicalCategory.id)) categoryOptions.push(historicalCategory);
    $('#tx-category').innerHTML = categoryOptions.map((category) => `<option value="${category.id}">${escapeHTML(category.icon)} ${escapeHTML(category.name)}${category.archived ? ' · Arquivada' : ''}</option>`).join('');

    const accountOptions = [...state.accounts];
    const historicalAccount = editingRow?.account_id ? allAccounts().find((account) => account.id === editingRow.account_id) : null;
    if (historicalAccount?.archived && !accountOptions.some((account) => account.id === historicalAccount.id)) accountOptions.push(historicalAccount);
    $('#tx-account').innerHTML = accountOptions.map((account) => `<option value="${account.id}">${escapeHTML(account.icon)} ${escapeHTML(account.name)}${account.archived ? ' · Arquivada' : ''}</option>`).join('');
    const goalSelect = $('#tx-goal');'''
if text.count(old) != 1:
    raise SystemExit(f'Expected renderSelectOptions block exactly once, found {text.count(old)}')
text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')
print('Archived references remain visible only while editing their historical transaction.')
