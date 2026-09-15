// Contract test: executes actual frontend logic with synthetic DOM/API adapters.
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
async function scenario(withAttachment) {
  const nodes = new Map();
  const makeNode = () => ({value:'',style:{},parentElement:{},handlers:{},append(){},setAttribute(){},addEventListener(k,fn){this.handlers[k]=fn;}});
  const document = {getElementById(id){if(!nodes.has(id))nodes.set(id,makeNode());return nodes.get(id);},createElement:makeNode};
  document.getElementById('anexo-tipo').value='ANEXO';
  document.getElementById('formato-saida').value='PDF';
  let payload;
  const window = {
    ContractoAPI:{request:async(method,url,body)=>{if(method==='POST'){payload=body;return {status:202,data:{job_id:'synthetic-job'}};}return {status:200,data:{status:'completed',file_ids:[]}};}},
    ContractoUI:{toast(){}},
    ContractoEtapa1:{lerParaEtapa2:()=>({participants:[{name:'Pessoa Sintetica'}],output_id:'synthetic-output',file_ids:['generated-pdf']})},
    pywebview:{api:{select_file:async()=>({selection_id:'synthetic-attachment'})}}
  };
  vm.runInNewContext(fs.readFileSync(path.join(process.argv[2]||path.join(__dirname,'source'),'frontend/js/etapa2.js'),'utf8'),{window,document,setInterval:()=>1,clearInterval(){}});
  window.ContractoEtapa2.ligar();
  if(withAttachment)await document.getElementById('btn-anexo').handlers.click();
  await document.getElementById('btn-finalizar').handlers.click();
  const passed = payload.file_ids?.includes('generated-pdf') === true && (!withAttachment || payload.attachments?.[0]?.file_id==='synthetic-attachment');
  console.log(JSON.stringify({scenario:withAttachment?'generated plus attachment':'generated only',passed,payload}));
  return passed;
}
(async()=>{const a=await scenario(false);const b=await scenario(true);process.exitCode=a&&b?0:1;})();
