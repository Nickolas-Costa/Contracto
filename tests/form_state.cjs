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
// Máscaras com cursor: corrigir no meio, apagar separador, ponto digitado, 3º decimal, colar e telefone.
const campo=(valor,pos,anterior)=>({value:valor,selectionStart:pos,dataset:{anterior},setSelectionRange(p){this.selectionStart=p;}});
const digita=(v,pos,ant,ev,tipo)=>{const i=campo(v,pos,ant);F.mascarar(i,ev,F.mascaras[tipo]);return [i.value,i.selectionStart];};
assert.deepEqual(digita('1.2334,56',5,'1.234,56',{inputType:'insertText',data:'3'},'MOEDA'),['12.334,56',5]);
assert.deepEqual(digita('1234,56',1,'1.234,56',{inputType:'deleteContentBackward'},'MOEDA'),['234,56',0]);
assert.deepEqual(digita('1.23',4,'1.234',{inputType:'deleteContentBackward'},'MOEDA'),['123',3]);
assert.deepEqual(digita('12,5',3,'12',{inputType:'insertText',data:'.'},'AREA'),['12,5',3]);
assert.deepEqual(digita('1,5,',4,'1,5',{inputType:'insertText',data:','},'MOEDA'),['1,5',3]);
assert.deepEqual(digita('100,000',7,'100,00',{inputType:'insertText',data:'0'},'MOEDA'),['1.000,00',8]);
assert.deepEqual(digita('1.234,567',9,'1.234,56',{inputType:'insertText',data:'7'},'MOEDA')[0],'12.345,67');
assert.deepEqual(digita('1,239',3,'1,29',{inputType:'insertText',data:'3'},'MOEDA')[0],'1,23');
assert.deepEqual(digita('1234.5',6,'',{inputType:'insertFromPaste'},'MOEDA'),['1.234,5',6]);
assert.deepEqual(digita('12ab',4,'12',{inputType:'insertText',data:'b'},'INTEIRO'),['12',2]);
assert.equal(F.formatTelefoneProgressive('8898887777'),'(88) 9888-7777');
assert.equal(F.formatTelefoneProgressive('88988887777'),'(88) 98888-7777');
assert.equal(F.formatTelefoneProgressive('889'),'(88) 9');
assert.equal(F.calcular('a - b - c',{a:'500000,00',b:'400.000,50',c:''}),'99.999,50');
assert.equal(F.calcular('a - b',{a:'100',b:'200'}),'0,00');
assert.equal(F.calcular('a*b',{a:'1',b:'2'}),null);
assert.equal(F.rotuloOpcao({rotulos_opcoes:{X_Y:'Ação é útil'}},'X_Y'),'Ação é útil');
assert.equal(F.rotuloOpcao({},'APOSENTADO_OU_PENSIONISTA'),'Aposentado Ou Pensionista');
assert.equal(F.comporEndereco({tipo:'Rua',logradouro:'das Flores',numero:'12',cidade:'Camocim',uf:'CE',cep:'62400-000'}),'Rua das Flores, 12, Camocim-CE, 62400-000');
assert.equal(F.formatCepProgressive('62400000'),'62400-000');
console.log('FORM-STATE OK');
