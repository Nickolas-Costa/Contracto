(async () => {
  const checks=[];
  const assert=(value,message)=>{if(!value)throw Error(message);checks.push(message);};
  const wait=async(fn,message)=>{const end=Date.now()+30000;while(Date.now()<end){if(fn())return;await new Promise(r=>setTimeout(r,80));}throw Error(message);};
  const $=id=>document.getElementById(id);
  const input=(id,value)=>{const el=$(id);if(!el)throw Error('missing '+id);el.value=value;el.dispatchEvent(new Event('input',{bubbles:true}));};
  const checkboxes=()=>[...document.querySelectorAll('#lista-formularios input')];
  try {
    await wait(()=>$('campo-0-endereco'),'form ready: inputs=' + [...document.querySelectorAll('input')].map(i=>i.id).join(','));
    assert([...document.querySelectorAll('#seletor-modelos .seletor-item')].filter(b=>b.getAttribute('aria-pressed')==='true').length===1,'one initial profile');
    const originalURL=location.href;$('pular-conteudo').click();
    assert(location.href===originalURL,'skip control moves focus without changing trusted URL');
    assert(document.querySelector('.toolbar .modos #modo-simples'),'modos inside toolbar (ADR 0021)');
    assert($('badge-participantes'),'participant badge visible');
    assert(!document.getElementById('conexao'),'backend indicator removed (ADR 0021)');
    assert(!document.querySelector('#participantes [aria-invalid="true"]'),'untouched fields do not show errors');
    $('campo-0-cpf').dispatchEvent(new Event('blur'));
    assert($('campo-0-cpf').getAttribute('aria-invalid')==='true','blur reveals field error');
    $('btn-ver-pendencias').click();
    await wait(()=>!document.getElementById('overlay').hidden && document.querySelector('.pendencia-item'),'pending review opens navigable modal');
    [...document.querySelectorAll('.modal .acoes button')].find(b=>b.textContent==='Fechar').click();
    await wait(()=>document.getElementById('overlay').hidden,'pending modal closes');
    // Primeira execução: a configuração inicial abre sozinha; o fluxo a dispensa como o usuário faria.
    await new Promise(r=>setTimeout(r,1400));
    if(!$('overlay').hidden){const b=[...document.querySelectorAll('#modal-acoes button')].find(x=>x.textContent==='Usar o padrão');assert(b,'first-run setup offers to keep defaults');b.click();const guia=async()=>{await wait(()=>!$('overlay').hidden,'guide opens after the first-run setup');[...document.querySelectorAll('#modal-acoes button')].find(x=>x.textContent==='Entendi, começar!').click();await wait(()=>$('overlay').hidden,'guide closes');};await guia();}
    // Leitura de documentos: o arrasto abre o modal, o PDF é lido e só o que o usuário confirma entra no formulário.
    assert($('leitura-banner')&&$('btn-ler-documentos'),'reading entry is a highlighted banner');
    window.ContractoArrasto.receberArrasto({selection_ids:[window.__qaAnexo.ids[0]],names:['cliente.pdf']});
    await wait(()=>$('leitura-aplicar')&&!$('leitura-aplicar').disabled,'document is read and proposals are ready');
    assert([...document.querySelectorAll('.leitura-rotulo')].map(x=>x.textContent).join()==='Nome completo,CPF','proposals list the form fields');
    assert(!document.querySelector('.leitura-arquivo input[placeholder*=nome i]'),'no rename field in the reading flow');
    assert($('campo-0-nome_completo').value==='','nothing is applied before confirming');
    // Remover e incluir outro arquivo não pode deixar o visualizador nem os valores do anterior.
    await wait(()=>document.querySelector('#leitura-doc iframe'),'viewer shows the first document');
    const antes=document.querySelector('#leitura-doc iframe').src;
    [...document.querySelectorAll('.leitura-arquivo button')].find(b=>b.textContent.includes('Remover')).click();
    await wait(()=>!document.querySelector('.leitura-arquivo'),'removed document leaves the list');
    assert(!document.querySelector('#leitura-doc iframe'),'viewer is cleared when no document is left');
    window.ContractoArrasto.receberArrasto({selection_ids:[window.__qaAnexo.ids[1]],names:['cliente.pdf']});
    await wait(()=>document.querySelector('#leitura-doc iframe')&&$('leitura-aplicar')&&!$('leitura-aplicar').disabled,'second document is read');
    assert(document.querySelector('#leitura-doc iframe').src!==antes,'viewer shows the new document, not the removed one');
    assert(!document.querySelector('.leitura-corpo .hint')?.textContent.includes('confiança'),'no confidence level shown');
    $('leitura-aplicar').click();await wait(()=>$('overlay').hidden,'reading modal closes after applying');
    assert($('campo-0-nome_completo').value==='ANA LIMA'&&$('campo-0-cpf').value==='529.982.247-25','confirmed values reach the form with masks');
    $('leitura-desfazer').click();await wait(()=>$('campo-0-nome_completo').value==='','undo restores the form');
    window.ContractoUI.mostrarTela('perfis');assert($('stepper').hidden,'profiles hide workflow steps');
    const cardsPerfis=()=>document.querySelectorAll('#lista-perfis .profile-item-card').length;
    await wait(()=>cardsPerfis()===2,'profile catalog shows detailed cards');
    assert(document.querySelectorAll('#lista-perfis .perfis-grupo').length===1 && $('perfis-grupo-formulario_simples').textContent.startsWith('Modo Simples'),'profiles grouped by mode (only non-empty groups)');
    input('buscar-perfis','QA A');await wait(()=>cardsPerfis()===1,'profile catalog filters by name');
    input('buscar-perfis','inexistente');await wait(()=>!$('perfis-vazio').hidden,'profile catalog reports an empty search');
    input('buscar-perfis','');
    // Módulo perfis.js: o catálogo novo chega ao gerenciador e à Etapa 1 pelo contexto (o CRUD
    // real é bloqueado quando o servidor recebe perfis fixos, como neste fixture).
    {const gp=window.ContractoAPI.getProfiles;
     window.ContractoAPI.getProfiles=async()=>{const r=await gp();return {status:200,data:[...r.data,{...r.data[0],profile_id:'qa-extra',name:'QA Extra',nome:'QA Extra'}]};};
     window.ContractoPerfis.carregarTela();
     await wait(()=>cardsPerfis()===3,'new catalog reaches the profile manager');
     await wait(()=>document.querySelectorAll('#seletor-modelos .seletor-item').length===3,'new catalog reaches the stage 1 selector');
     window.ContractoAPI.getProfiles=gp;window.ContractoPerfis.carregarTela();
     await wait(()=>cardsPerfis()===2&&document.querySelectorAll('#seletor-modelos .seletor-item').length===2,'catalog restored in both places');}
    window.ContractoUI.mostrarTela('config');assert($('stepper').hidden,'settings hide workflow steps');
    assert(!$('lista-capacidades'),'resources section removed from settings');
    window.ContractoUI.mostrarTela('inicio');assert(!$('stepper').hidden,'workflow restores steps');
    input('campo-0-nome_completo','PESSOA QA UM');input('campo-0-cpf','52998224725');
    $('modo-simples').click();
    await wait(()=>checkboxes().length===2,'simple lists both profiles');
    assert(checkboxes().filter(c=>c.checked).length===0,'simple starts unselected');
    $('modo-contrato').click();
    await wait(()=>document.querySelectorAll('#seletor-modelos .seletor-item').length===2,'contract lists both models');
    $('modo-simples').click();
    await wait(()=>checkboxes().length===2,'back to simple list');
    assert($('campo-0-nome_completo').value==='PESSOA QA UM','draft preserved after mode change');
    checkboxes()[1].click();await wait(()=>!$('btn-adicionar').disabled,'compose single profile');
    assert($('campo-0-nome_completo').value==='PESSOA QA UM','draft preserved after composition');
    await wait(()=>$('campo-0-endereco'),'single profile fields rendered');
    input('campo-0-endereco','RUA QA');
    checkboxes()[0].click();await wait(()=>window.ContractoEtapa1.composto()&&checkboxes().filter(c=>c.checked).length===2,'compose two profiles');
    // Regressão: render() precisa anexar o card mesmo com TEXTO_LONGO (textarea não
    // aceita .type) e com abas múltiplas; composto() fica true mesmo se render falhar.
    await wait(()=>$('campo-0-observacoes'),'long text field rendered after multi-profile compose');
    assert([...document.querySelectorAll('#participantes .field-section')].every(s=>s.hidden||s.querySelector('.field:not([hidden])')),'sections without visible fields hide their titles');
    // O atalho da Conferência alcança campos de qualquer página (antes ficava na página atual).
    {const ind=()=>document.querySelector('.paginacao-indicador')?.textContent||'';
     assert(!$('paginacao-form').hidden,'pagination visible with two profiles');
     $('paginacao-form').querySelector('button:last-child').click();const ultima=ind();
     window.ContractoEtapa1.irParaCampo(0,'valor');
     assert(ind()!==ultima&&ind().startsWith('Página 1'),'jump reaches a field on another page');}
    assert(document.querySelectorAll('#paginacao-form [role=tab]').length>=2&&document.querySelector('#paginacao-form [role=tab][aria-selected=true]'),'pagination is a free tab list');
    input('campo-global-cidade','CAMOCIM-CE');$('campo-global-cidade').dispatchEvent(new Event('change'));
    assert($('campo-global-comarca_x').value==='CAMOCIM-CE','picking a configured city fills its linked fields');
    {const h=document.createElement('div');window.ContractoMunicipios.montar(h,[{prefeitura:'A-CE',comarca:'A',texto_isencao:'Lei A'},{prefeitura:'B-CE',comarca:'B',texto_isencao:'Lei B'}],'B-CE');
     const r=window.ContractoMunicipios.ler(h);assert(r.padrao==='B-CE'&&r.municipios.length===2&&r.municipios[0].texto_isencao==='Lei A','municipality list round trips');}
    // Endereço: completo ou em partes; o texto completo é montado das partes.
    {const modo=[...document.querySelectorAll('.endereco-campo .seletor-item')].find(b=>b.textContent==='Detalhado');modo.click();
     input('campo-global-local_obra-logradouro','das Flores');input('campo-global-local_obra-numero','12');input('campo-global-local_obra-cidade','Camocim');
     const uf=$('campo-global-local_obra-uf');uf.value='CE';uf.dispatchEvent(new Event('change'));input('campo-global-local_obra-cep','62400000');
     assert($('campo-global-local_obra').value==='das Flores, 12, Camocim-CE, 62400-000','detailed address builds the full text');
     assert($('campo-global-local_obra-cep').value==='62400-000','CEP mask');
     const p=window.ContractoForm.participants({people:[{nome_completo:'A',cpf:''}],globals:{local_obra:'x',local_obra_uf:'CE'}},[{id:'local_obra',tipo:'ENDERECO',escopo:'global'}]);
     assert(p[0].campos_dinamicos.local_obra_uf==='CE'&&p[0].campos_dinamicos.local_obra_numero==='','address parts are sent to the server');}
    {const F=window.ContractoForm;assert(F.formatMoedaFinal('180000')==='180.000,00'&&F.formatMoedaFinal('1234.5')==='1.234,50'&&F.formatMoedaFinal('0,5')==='0,50'&&F.formatMoedaFinal('')==='','money formatter adds thousands and cents');}
    input('campo-0-valor','180000');assert($('campo-0-valor').value==='180.000','money input groups thousands while typing');
    $('campo-0-valor').dispatchEvent(new Event('blur'));assert($('campo-0-valor').value==='180.000,00','money input completes cents on blur');
    input('campo-0-valor','10,00');$('campo-0-valor').dispatchEvent(new Event('blur'));
    checkboxes()[0].click();await wait(()=>window.ContractoEtapa1.composto()&&checkboxes().filter(c=>c.checked).length===1,'back to single profile');
    input('campo-global-regime','B');
    assert(!$('campo-0-detalhe').parentElement.hidden,'conditional field visible');
    input('campo-global-regime','A');
    assert($('campo-0-detalhe').parentElement.hidden,'conditional field hidden');
    // Regressão: "Limpar" zera pessoas e campos compartilhados; o modo escolhido fica salvo.
    input('campo-global-regime','B');$('btn-limpar-campos').click();
    await wait(()=>!window.ContractoEtapa1.composto(),'clear resets composition');
    checkboxes()[1].click();await wait(()=>window.ContractoEtapa1.composto(),'recompose after clear');
    assert($('campo-global-regime').value==='A'&&$('campo-0-nome_completo').value==='','clear resets shared fields and people');
    assert(localStorage.getItem('contracto-modo')==='simples','last mode is remembered');
    input('campo-0-nome_completo','PESSOA QA UM');input('campo-0-cpf','52998224725');input('campo-0-endereco','RUA QA');
    $('btn-adicionar').click();
    input('campo-1-nome_completo','PESSOA QA DOIS');input('campo-1-cpf','11144477735');input('campo-1-endereco','RUA QA');
    input('data-assinatura','14/09/2026');input('local-assinatura','CIDADE QA');
    $('btn-pasta').click();await wait(()=>!$('btn-gerar').disabled,'generation enabled');
    assert($('campo-0-dobro').value==='20,00','backend calculated preview displayed');
    // Perfis simples: campo do formulário vazio não trava; a lista de pendências oferece "Gerar mesmo assim".
    input('campo-0-endereco','');await wait(()=>!$('btn-gerar').disabled&&$('pendencias').textContent.includes('opcional'),'optional pending does not block generation');
    assert(!$('btn-ver-pendencias').hidden,'pending list stays reachable');
    $('btn-gerar').click();await wait(()=>[...document.querySelectorAll('#modal-acoes button')].some(b=>b.textContent==='Gerar mesmo assim'),'pending list offers generate anyway');
    [...document.querySelectorAll('#modal-acoes button')].find(b=>b.textContent==='Gerar mesmo assim').click();
    await wait(()=>!$('tela-conferir').hidden&&$('corpo-conferencia').querySelector('.conf-aviso'),'generate anyway reaches the conference with a notice');
    $('btn-conferir-voltar').click();await wait(()=>$('tela-conferir').hidden,'back to the form');
    input('campo-0-endereco','RUA QA');await wait(()=>!$('btn-gerar').disabled,'form ready again');
    $('btn-gerar').click();
    await wait(()=>!$('tela-conferir').hidden,'conference screen opens');
    assert($('corpo-conferencia').textContent.includes('PESSOA QA'),'conference lists participants');
    assert($('corpo-conferencia').querySelector('h3'),'conference groups fields by section');
    assert($('corpo-conferencia').querySelector('.conf-cab .section-tag')&&!$('corpo-conferencia').querySelector('.conf-participante h3').textContent.includes('PESSOA'),'conference participant header shows count and does not repeat the name');
    // Conferência editável (ADR 0030, passo 1): o valor leva ao campo certo e o fluxo volta à Conferência.
    $('corpo-conferencia').querySelector('.conf-valor[aria-label^="Editar CPF"]').click();
    await wait(()=>$('tela-conferir').hidden&&$('campo-0-cpf').classList.contains('campo-destaque'),'conference value jumps to its field');
    $('btn-gerar').click();await wait(()=>!$('tela-conferir').hidden,'back to the conference after fixing');
    const request=window.ContractoAPI.request;
    let responseLost=false;
    window.ContractoAPI.request=async(method,path,payload)=>{
      const result=await request(method,path,payload);
      if(path==='/api/v1/jobs/generate' && result.status===202 && !responseLost){responseLost=true;return {status:503,data:{code:'simulated_response_loss'}};}
      return result;
    };
    $('btn-conferir-confirmar').click();$('btn-conferir-confirmar').click();
    await wait(()=>!$('btn-retomar').hidden && !$('btn-retomar').disabled,'ambiguous send recoverable');
    assert(window.ContractoEtapa2.ocupado(),'ambiguous send blocks duplicates');
    $('btn-retomar').click();
    await wait(()=>$('lista-resultados').children.length===2 && !window.ContractoEtapa2.ocupado(),'generation terminal');
    assert($('manifesto-resumo').textContent.includes('2 gerado'),'generated manifest');
    assert($('lista-anexos').textContent.includes('Gerado pelo Contracto'),'generated document has safe metadata');
    const seletorExtra=[...$('lista-docs-extras').querySelectorAll('button')].find(b=>/^(Selecionar|Trocar)$/.test(b.textContent));
    assert(seletorExtra,'conference offers a named extra selector');
    seletorExtra.click();
    await wait(()=>[...$('lista-docs-extras').querySelectorAll('button')].some(b=>b.textContent==='Remover'),'named extra attached');
    assert($('manifesto-resumo').textContent.includes('1/1 documento(s) extra(s)'),'named extra retained with generated');
    $('btn-finalizar').click();
    await wait(()=>[...document.querySelectorAll('.modal .acoes button')].some(b=>/mesmo assim/.test(b.textContent))||$('lista-resultados').children.length===3,'finalize confirm prompts or terminal');
    const confirmaFinal=[...document.querySelectorAll('.modal .acoes button')].find(b=>/mesmo assim/.test(b.textContent));
    if(confirmaFinal)confirmaFinal.click();
    await wait(()=>$('lista-resultados').children.length===3 && !window.ContractoEtapa2.ocupado(),'processing terminal');
    assert(!$('btn-abrir-pasta').hidden,'final folder available');
    const botoesEtapa2=[...document.querySelectorAll('#tela-etapa2 .acoes > button:not([hidden])')];
    assert(botoesEtapa2.at(-1).classList.contains('btn-primary') && botoesEtapa2[0].id==='btn-voltar','stage 2 actions end with the primary button, Voltar first');
    const caps=await window.ContractoAPI.getCapabilities(), cfg=(await window.ContractoAPI.getSettings()).data.formato_saida;
    assert($('formato-saida').value===(cfg==='PDF/A-2b'&&caps.ghostscript?'PDF/A-2b':'PDF'),'initial format follows the user setting');
    assert([...document.querySelectorAll('#formato-opcoes .formato-seletor [aria-pressed="true"]')].length===1,'format shown as toggle buttons with one pressed');
    assert($('btn-finalizar').disabled,'unchanged completed process cannot duplicate');
    $('lista-resultados').querySelector('button').click();
    await wait(()=>document.querySelector('.pdf-preview'),'viewer created');
    assert($('app').inert,'modal background inert');
    assert(document.querySelector('.pdf-preview').src.startsWith('blob:'),'viewer uses local blob');
    {const m=document.querySelector('.modal').getBoundingClientRect(),f=document.querySelector('.pdf-preview').getBoundingClientRect();
     assert(f.left>=m.left-1&&f.right<=m.right+1&&f.width>m.width*0.8,'viewer fits inside the modal width');}
    assert(getComputedStyle(document.querySelector('.toolbar')).position===(innerWidth>1100?'sticky':'relative'),'toolbar sticky above the collapse breakpoint');
    assert([...document.querySelectorAll('.modal .acoes button')].some(b=>b.textContent==='Abrir no leitor padrão'),'viewer offers external reader');
    [...document.querySelectorAll('.modal .acoes button')].find(b=>b.textContent==='Expandir').click();
    assert(document.querySelector('.modal').classList.contains('modal-viewer-expandido')&&!document.getElementById('overlay').hidden,'viewer expands and stays open');
    {const r=[...document.querySelectorAll('.modal .acoes button')].find(b=>b.textContent==='Reduzir');assert(r,'expanded viewer offers Reduzir');r.click();
     assert(!document.querySelector('.modal').classList.contains('modal-viewer-expandido')&&!document.getElementById('overlay').hidden,'Reduzir restores the viewer without closing');
     const m=document.querySelector('.modal').getBoundingClientRect();assert(Math.abs((m.left+m.right)/2-document.documentElement.clientWidth/2)<3,'viewer modal stays centered');}
    window.ContractoUI.fecharModal();assert(!$('app').inert&&!document.querySelector('.modal').classList.contains('modal-viewer')&&!document.querySelector('.modal').classList.contains('modal-viewer-expandido'),'modal releases background and viewer layout');
    if(window.__qaKeepResult){window.__qaResult={ok:true,checks};return;}
    window.ContractoUI.mostrarTela('inicio');
    assert(document.querySelector('[data-etapa="1"]').getAttribute('aria-current')==='step','navigation synchronized');
    input('campo-0-nome_completo','PESSOA QA EDITADA');
    assert($('btn-finalizar').disabled && !$('lista-resultados').children.length,'old result invalidated on edit');
    window.__qaResult={ok:true,checks};
  } catch(error) {window.__qaResult={ok:false,error:String(error),checks};}
})();
