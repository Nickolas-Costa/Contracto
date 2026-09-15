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
 assert.equal(window.ContractoApp.pronto(),true);assert.equal(calls,3);assert.equal(one,1);assert.equal(two,1);
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
function modal() {
  const registry = new Map();
  function el(tag, id) {
    const e = {tag, id: id || null, children: [], attrs: {}, dataset: {}, handlers: {},
      textContent: "", innerHTML: "", hidden: false, style: {}, parentElement: null,
      _classes: new Set(),
      get className() { return [...e._classes].join(" "); },
      set className(v) { e._classes = new Set(String(v || "").split(/\s+/).filter(Boolean)); },
      get classList() {
        return {
          add: (c) => e._classes.add(c),
          remove: (c) => e._classes.delete(c),
          contains: (c) => e._classes.has(c),
        };
      },
      setAttribute(k, v) { this.attrs[k] = v; }, getAttribute(k) { return this.attrs[k]; },
      removeAttribute(k) { delete this.attrs[k]; },
      addEventListener(k, fn) { this.handlers[k] = fn; },
      append(...nodes) { for (const n of nodes) { n.parentElement = this; this.children.push(n); } },
      replaceWith(other) {
        const pai = this.parentElement;
        if (pai) {
          const i = pai.children.indexOf(this);
          if (i >= 0) pai.children[i] = other;
          other.parentElement = pai;
        }
        if (this.id) registry.set(this.id, other);
      },
      replaceChildren() { this.children = []; },
      querySelector(sel) {
        const all = this.querySelectorAll(sel);
        return all[0] || null;
      },
      querySelectorAll(sel) {
        const out = [];
        const walk = (n) => {
          for (const c of n.children || []) {
            if (["button", "input", "select", "iframe"].includes(c.tag)) out.push(c);
            walk(c);
          }
        };
        walk(this);
        return out;
      },
      focus() { e.focused = true; },
      click() { if (this.handlers.click) this.handlers.click(); },
      contains(n) { return n === this || this.children.some((c) => c === n || (c.contains && c.contains(n))); },
      winfo_exists: undefined,
    };
    if (id) registry.set(id, e);
    return e;
  }
  const overlay = el("div", "overlay"); overlay.hidden = true;
  const pular = el("button", "pular-conteudo");
  const titulo = el("h2", "modal-titulo");
  const corpo = el("div", "modal-corpo");
  const acoes = el("div", "modal-acoes");
  const app = el("div", "app");
  overlay.append(titulo, corpo, acoes);
  const keyHandlers = [];
  const document = {
    readyState: "complete",
    activeElement: null,
    contains: () => true,
    getElementById: (id) => registry.get(id) || null,
    createElement: (tag) => el(tag),
    querySelectorAll: () => [],
    querySelector: (sel) => {
      if (sel === ".modal") {
        const m = el("div");
        return m;
      }
      const alvos = [];
      for (const [, node] of registry) {
        const achados = node.querySelectorAll(sel);
        for (const a of achados) alvos.push(a);
      }
      return alvos[0] || null;
    },
    addEventListener: (k, fn) => keyHandlers.push([k, fn]),
  };
  const window = {};
  vm.runInNewContext(source("ui.js"), { window, document, setTimeout, clearTimeout });
  const ui = window.ContractoUI;
  ui.abrirModal("Título", "corpo", [{ texto: "Ok", primario: true }]);
  assert.equal(overlay.hidden, false);
  // Faixa com X: o título deve estar dentro de um contêiner com botão fechar.
  const faixa = titulo.parentElement;
  assert.ok(faixa && faixa !== overlay, "título dentro da faixa do modal");
  assert.ok(faixa.classList.contains("modal-titulo-faixa"), "faixa com classe");
  const botoes = acoes.querySelectorAll("button");
  assert.equal(botoes.length, 1);
  const x = faixa.children.find((c) => c.tag === "button" && c.textContent === "✕");
  assert.ok(x, "botão X presente");
  assert.equal(x.attrs["aria-label"], "Fechar diálogo");
  // Escape fecha e Escape com overlay oculto não quebra.
  const esc = keyHandlers.find(([k]) => k === "keydown");
  assert.ok(esc, "handler de teclado registrado");
  esc[1]({ key: "Escape", preventDefault() {} });
  assert.equal(overlay.hidden, true);
  console.log("PASS modal com faixa, X e Escape");
}
(async()=>{fields();await bootstrap();modal();})().catch(error=>{console.error(error);process.exitCode=1});
