from pathlib import Path

path = Path('salesboard/app/app.js')
text = path.read_text(encoding='utf-8')

replacements = [
("""    accounts: [],
    categories: [],
    transactions: [],""", """    accounts: [],
    categories: [],
    accountCatalog: [],
    categoryCatalog: [],
    transactions: [],"""),
("""  function categoryById(id) {
    return state.categories.find((item) => item.id === id) || { name: 'Sem categoria', icon: '•', color: '#94a3b8' };
  }

  function accountById(id) {
    return state.accounts.find((item) => item.id === id) || { name: 'Conta removida', icon: '▣' };
  }""", """  function allCategories() {
    return state.categoryCatalog?.length ? state.categoryCatalog : state.categories;
  }

  function allAccounts() {
    return state.accountCatalog?.length ? state.accountCatalog : state.accounts;
  }

  function categoryById(id) {
    return allCategories().find((item) => item.id === id) || { name: 'Categoria indisponível', icon: '•', color: '#94a3b8' };
  }

  function accountById(id) {
    return allAccounts().find((item) => item.id === id) || { name: 'Conta indisponível', icon: '▣' };
  }"""),
("""      supabaseClient.from('accounts').select('*').eq('user_id', userId).eq('archived', false).order('created_at'),
      supabaseClient.from('categories').select('*').eq('user_id', userId).eq('archived', false).order('type').order('name'),""", """      supabaseClient.from('accounts').select('*').eq('user_id', userId).order('created_at'),
      supabaseClient.from('categories').select('*').eq('user_id', userId).order('type').order('name'),"""),
("""    state.accounts = accounts.data || [];
    state.categories = categories.data || [];
    state.transactions = transactions.data || [];""", """    state.accountCatalog = accounts.data || [];
    state.categoryCatalog = categories.data || [];
    state.accounts = state.accountCatalog.filter((row) => !row.archived);
    state.categories = state.categoryCatalog.filter((row) => !row.archived);
    state.transactions = transactions.data || [];"""),
("""    state.subscription = { plan: 'pro', status: 'active', billing_cycle: 'annual', cancel_at_period_end: false, current_period_end: new Date(now.getFullYear() + 1, now.getMonth(), now.getDate()).toISOString() };
    enterApp();""", """    state.subscription = { plan: 'pro', status: 'active', billing_cycle: 'annual', cancel_at_period_end: false, current_period_end: new Date(now.getFullYear() + 1, now.getMonth(), now.getDate()).toISOString() };
    state.accountCatalog = [...state.accounts];
    state.categoryCatalog = [...state.categories];
    enterApp();"""),
("""    const categories = state.categories.filter((category) => category.type === 'expense').map((category) => ({ ...category, total: categorySpent(category.id) })).filter((category) => category.total > 0).sort((a, b) => b.total - a.total);""", """    const categories = allCategories().filter((category) => category.type === 'expense').map((category) => ({ ...category, total: categorySpent(category.id) })).filter((category) => category.total > 0).sort((a, b) => b.total - a.total);"""),
("""    const expenses = state.categories.filter((category) => category.type === 'expense').map((category) => ({ ...category, total: categorySpent(category.id, selectedKey) })).filter((category) => category.total > 0).sort((a, b) => b.total - a.total);""", """    const expenses = allCategories().filter((category) => category.type === 'expense').map((category) => ({ ...category, total: categorySpent(category.id, selectedKey) })).filter((category) => category.total > 0).sort((a, b) => b.total - a.total);"""),
("""    const accountMovements = state.accounts.filter((account) => !account.archived).map((account) => {""", """    const accountMovements = allAccounts().map((account) => {""")
]

for old, new in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'Expected exactly one match, found {count}: {old[:80]!r}')
    text = text.replace(old, new, 1)

path.write_text(text, encoding='utf-8')
print('Archive catalogs preserved for historical rendering.')
