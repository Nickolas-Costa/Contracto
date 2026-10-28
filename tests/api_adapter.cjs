// Contrato nativo do api.js: mesmos comandos/argumentos sob pywebview, Tauri e sem shell.
const fs=require('node:fs'), vm=require('node:vm'), path=require('node:path'), assert=require('node:assert');
const codigo=fs.readFileSync(path.join(__dirname,'../frontend/js/api.js'),'utf8');
const carregar=(extra)=>{const window={addEventListener(){},navigator:{userAgent:''},...extra};
  vm.runInNewContext(codigo,{window,navigator:window.navigator,atob:s=>Buffer.from(s,'base64').toString('binary'),Blob:class{constructor(p,o){this.p=p;this.o=o}},Uint8Array});
  return window.ContractoAPI;};
const comandos=[['selectOutput',[],'select_output',[]],['selectFile',[],'select_file',[]],['selectAttachment',[],'select_file',[]],
 ['selectBackup',[],'select_backup',[]],['selectDocuments',[],'select_documents',[]],['importProfile',[],'import_profile',[]],
 ['exportProfile',['MCMV'],'export_profile',['MCMV']],['openResult',['job1'],'open_result',['job1']],['openFile',['f1'],'open_file',['f1']]];
(async()=>{
  // pywebview: métodos de pywebview.api com argumentos posicionais.
  const chamadas=[];
  const api=new Proxy({},{get:(_,nome)=>(...a)=>{chamadas.push([nome,a]);return {ok:true,nome}}});
  const py=carregar({pywebview:{api}});
  assert.equal(py.disponivel(),true);
  for(const [fn,args,nome,esperado] of comandos){chamadas.length=0;await py[fn](...args);assert.deepEqual(chamadas,[[nome,esperado]],fn);}
  chamadas.length=0;await py.request('POST','/api/v1/x',{a:1});assert.deepEqual(chamadas,[['request',['POST','/api/v1/x',{a:1}]]]);
  // Tauri: invoke(nome, argumentos nomeados).
  const invocacoes=[];
  const tauri=carregar({__TAURI__:{core:{invoke:async(n,a)=>{invocacoes.push([n,a]);return {ok:true}}}}});
  assert.equal(tauri.disponivel(),true);
  for(const [fn,args,nome] of comandos){invocacoes.length=0;await tauri[fn](...args);assert.equal(invocacoes[0][0],nome,fn);}
  invocacoes.length=0;await tauri.exportProfile('MCMV');assert.deepEqual(invocacoes,[['export_profile',{nome:'MCMV'}]]);
  invocacoes.length=0;await tauri.openResult('j');assert.deepEqual(invocacoes,[['open_result',{job_id:'j'}]]);
  invocacoes.length=0;await tauri.request('GET','/api/v1/health');assert.deepEqual(invocacoes,[['request',{method:'GET',path:'/api/v1/health',payload:undefined}]]);
  // Sem shell (navegador comum): falha explícita, sem exceção.
  const nada=carregar({});
  assert.equal(nada.disponivel(),false);
  assert.equal((await nada.request('GET','/api/v1/health')).status,503);
  assert.equal((await nada.selectOutput()).code,'sem_ponte');
  // Método ausente no shell: "unsupported", sem exceção.
  const parcial=carregar({pywebview:{api:{}}});
  assert.equal((await parcial.importProfile()).code,'unsupported');
  console.log('API-ADAPTER OK');
})().catch(e=>{console.error(e);process.exit(1)});
