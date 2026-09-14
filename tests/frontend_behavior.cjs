const fs=require('node:fs'), vm=require('node:vm'), path=require('node:path'), assert=require('node:assert/strict');
const source=name=>fs.readFileSync(path.join(__dirname,'../frontend/js',name),'utf8');
const flush=()=>new Promise(resolve=>setImmediate(resolve));
async function bootstrap(){
 const elements=new Map();
 const make=()=>({dataset:{},children:[],addEventListener(k,fn){this[k]=fn},append(n){this.children.push(n)},set textContent(v){this.text=v;this.children=[]}});
 for(const id of ['conexao','btn-gerar','btn-finalizar','btn-pasta'])elements.set(id,make());
 let calls=0,one=0,two=0;
 const events={};
 const document={readyState:'complete',getElementById:id=>elements.get(id),createElement:make};
 const window={ContractoAPI:{disponivel:()=>true,request:async()=>({status:++calls===1?503:200})},
  ContractoUI:{aplicarTemaInicial(){}},ContractoEtapa1:{ligar(){one++},atualizar(){},reconectar(){}},
  ContractoEtapa2:{ligar(){two++},atualizar(){},reconectar(){}},addEventListener(k,fn){events[k]=fn}};
 vm.runInNewContext(source('app.js'),{window,document,setTimeout,clearTimeout});
 await flush();assert.equal(window.ContractoApp.pronto(),false);
 elements.get('conexao').children[0].click();await flush();
 assert.equal(window.ContractoApp.pronto(),true);assert.equal(calls,2);assert.equal(one,1);assert.equal(two,1);
 events.pywebviewready();events.pywebviewready();await flush();
 assert.equal(one,1);assert.equal(two,1);
 console.log('PASS bootstrap 503 -> retry 200; duplicate ready events');
}
function fields(){
 const window={};vm.runInNewContext(source('form-state.js'),{window});const f=window.ContractoForm;
 const definitions=[{id:'endereco',escopo:'participante'},{id:'regime',escopo:'global'},{id:'segredo',visivel_quando:[{regime:['B']}],limpar_quando_oculto:true}];
 const draft={people:[{nome_completo:'A',cpf:'52998224725',endereco:'Rua A',segredo:'oculto'},{nome_completo:'B',cpf:'11144477735',endereco:'Rua B'}],globals:{regime:'A',data_assinatura:'14/09/2026',local_assinatura:'QA'}};
 const result=f.participants(draft,definitions);
 assert.equal(result[0].campos_dinamicos.endereco,'Rua A');assert.equal(result[1].campos_dinamicos.endereco,'Rua B');
 assert.equal(result[0].endereco,undefined);assert.equal(result[0].campos_dinamicos.segredo,'');
 assert.equal(result[1].campos_dinamicos.regime,'A');assert.equal(draft.people[0].segredo,'oculto');
 assert.equal(f.cpfValid('529.982.247-25'),true);assert.equal(f.cpfValid('11111111111'),false);
 assert.equal(f.dateValid('31/02/2026'),false);assert.equal(f.dateValid('29/02/2024'),true);
 console.log('PASS canonical serialization, globals, hidden fields, CPF and dates');
}
(async()=>{fields();await bootstrap();})().catch(error=>{console.error(error);process.exitCode=1});
