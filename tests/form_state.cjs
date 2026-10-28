// Carrega o form-state.js real e confere os validadores/formatadores contra vetores do Python.
const fs=require('node:fs'), vm=require('node:vm'), path=require('node:path'), assert=require('node:assert/strict');
const window={};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../frontend/js/form-state.js'),'utf8'),{window,console});
const F=window.ContractoForm, casos=JSON.parse(fs.readFileSync(0,'utf8'));
for(const [cnpj,esperado] of casos.cnpj) assert.equal(F.cnpjValid(cnpj),esperado,'CNPJ '+cnpj);
for(const [cnpj,esperado] of casos.cnpj) assert.equal(F.docValid(cnpj),esperado,'doc '+cnpj);
for(const [cpf,esperado] of casos.cpf) assert.equal(F.cpfValid(cpf),esperado,'CPF '+cpf);
for(const [entrada,final,progressivo] of casos.moeda){
  assert.equal(F.formatMoedaFinal(entrada),final,'moeda final '+entrada);
  assert.equal(F.formatMoedaProgressive(entrada),progressivo,'moeda progressiva '+entrada);
}
console.log('FORM-STATE OK');
