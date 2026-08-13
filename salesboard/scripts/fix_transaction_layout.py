from pathlib import Path

path = Path('salesboard/app/index.html')
text = path.read_text(encoding='utf-8')

old = '''<label id="tx-goal-wrap">Meta (opcional)<select id="tx-goal"><option value="">Nenhuma meta</option></select><small class="field-help">Escolha uma meta para destinar parte ou todo o valor desta entrada.</small></label><label id="tx-goal-amount-wrap" hidden>Valor destinado à meta<div class="money-field"><span>R$</span><input id="tx-goal-amount" inputmode="decimal" placeholder="Valor inteiro da entrada" /></div><small class="field-help">Se ficar vazio, o valor inteiro da entrada será considerado na meta.</small></label><label>Status<select id="tx-status"><option value="paid">Pago/recebido</option><option value="pending">Pendente</option></select></label><label class="check recurring-field">'''

new = '''<label id="tx-goal-wrap">Meta (opcional)<select id="tx-goal"><option value="">Nenhuma meta</option></select><small class="field-help">Escolha uma meta para destinar parte ou todo o valor desta entrada.</small></label><label id="tx-status-wrap">Status<select id="tx-status"><option value="paid">Pago/recebido</option><option value="pending">Pendente</option></select></label><label id="tx-goal-amount-wrap" hidden>Valor destinado à meta<div class="money-field"><span>R$</span><input id="tx-goal-amount" inputmode="decimal" placeholder="Valor inteiro da entrada" /></div><small class="field-help">Se ficar vazio, o valor inteiro da entrada será considerado na meta.</small></label><label class="check recurring-field">'''

if text.count(old) != 1:
    raise SystemExit(f'Expected transaction field sequence exactly once, found {text.count(old)}')
text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')
print('Transaction layout order repaired.')
