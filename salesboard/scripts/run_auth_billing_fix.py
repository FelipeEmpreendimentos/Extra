from pathlib import Path
import runpy

patch = Path('salesboard/scripts/fix_auth_billing.py')
text = patch.read_text(encoding='utf-8')
text = text.replace("toast('Não foi possível atualizar', friendlyError(error), 'error');", "toast('Não foi possível atualizar a senha', friendlyError(error), 'error');")
patch.write_text(text, encoding='utf-8')
runpy.run_path(str(patch), run_name='__main__')
