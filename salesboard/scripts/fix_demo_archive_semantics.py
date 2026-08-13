from pathlib import Path

path = Path('salesboard/app/app.js')
text = path.read_text(encoding='utf-8')
old = '''      if (demoMode) {
        state[config.key] = state[config.key].filter((item) => item.id !== id);
        if (mode === 'goal') state.transactions.forEach((transaction) => {
          if (transaction.goal_id === id) {
            transaction.goal_id = null;
            transaction.goal_amount = null;
          }
        });
      } else if (shouldArchive) {'''
new = '''      if (demoMode) {
        if (shouldArchive) {
          const catalog = mode === 'account' ? state.accountCatalog : state.categoryCatalog;
          const catalogItem = catalog.find((item) => item.id === id);
          if (catalogItem) catalogItem.archived = true;
          state[config.key] = state[config.key].filter((item) => item.id !== id);
        } else {
          state[config.key] = state[config.key].filter((item) => item.id !== id);
          if (mode === 'goal') state.transactions.forEach((transaction) => {
            if (transaction.goal_id === id) {
              transaction.goal_id = null;
              transaction.goal_amount = null;
            }
          });
        }
      } else if (shouldArchive) {'''
if text.count(old) != 1:
    raise SystemExit(f'Expected demo delete branch once, found {text.count(old)}')
text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')
print('Demo archive semantics now match production.')
