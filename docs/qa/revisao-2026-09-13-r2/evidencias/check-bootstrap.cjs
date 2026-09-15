const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
async function run(firstStatus){
 const elements=new Map();
 const make=()=>({dataset:{},children:[],addEventListener(k,fn){this[k]=fn},append(n){this.children.push(n)},remove(){}});
 for(const id of ['conexao','btn-gerar','btn-finalizar','btn-pasta'])elements.set(id,make());
 let calls=0,stage1=0,stage2=0;
 const document={readyState:'complete',getElementById:id=>elements.get(id),createElement:make};
 const window={ContractoAPI:{disponivel:()=>true,request:async()=>({status:++calls===1?firstStatus:200})},ContractoUI:{aplicarTemaInicial(){}},ContractoEtapa1:{ligar(){stage1++}},ContractoEtapa2:{ligar(){stage2++}},addEventListener(){},removeEventListener(){}};
 vm.runInNewContext(fs.readFileSync(path.join(process.argv[2] || path.join(__dirname,'source'),'frontend/js/app.js'),'utf8'),{window,document,setTimeout,clearTimeout});
 await new Promise(resolve=>setImmediate(resolve));
 if(firstStatus!==200){const retry=elements.get('conexao').children[0];retry.click();await new Promise(resolve=>setImmediate(resolve));}
 const passed=stage1===1&&stage2===1&&elements.get('conexao').dataset.estado==='pronto';
 console.log(JSON.stringify({scenario:firstStatus===200?'initial connection':'503 then retry 200',passed,healthCalls:calls,stage1Bindings:stage1,stage2Bindings:stage2,connection:elements.get('conexao').dataset.estado}));
 return passed;
}
(async()=>{const a=await run(200),b=await run(503);process.exitCode=a&&b?0:1})();
