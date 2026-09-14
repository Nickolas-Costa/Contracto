(async () => {
  const checks=[];
  const assert=(value,message)=>{if(!value)throw Error(message);checks.push(message);};
  const wait=async(fn,message)=>{const end=Date.now()+30000;while(Date.now()<end){if(fn())return;await new Promise(r=>setTimeout(r,80));}throw Error(message);};
  const $=id=>document.getElementById(id);
  const input=(id,value)=>{const el=$(id);if(!el)throw Error('missing '+id);el.value=value;el.dispatchEvent(new Event('input',{bubbles:true}));};
  const checkboxes=()=>[...document.querySelectorAll('#lista-formularios input')];
  try {
    await wait(()=>$('campo-0-endereco'),'form ready');
    assert(checkboxes().filter(c=>c.checked).length===1,'one initial profile');
    const originalURL=location.href;$('pular-conteudo').click();
    assert(document.activeElement===$('telas')&&location.href===originalURL,'skip control moves focus without changing trusted URL');
    assert(!document.querySelector('#participantes [aria-invalid="true"]'),'untouched fields do not show errors');
    $('campo-0-cpf').dispatchEvent(new Event('blur'));
    assert($('campo-0-cpf').getAttribute('aria-invalid')==='true','blur reveals field error');
    $('btn-ver-pendencias').click();
    const errorLink=[...document.querySelectorAll('#modal-corpo button')].find(b=>b.textContent.includes('CPF'));
    assert(!!errorLink,'summary links to human field labels');errorLink.click();
    assert(document.activeElement===$('campo-0-cpf') && $('overlay').hidden,'summary closes then focuses selected field');
    window.ContractoUI.mostrarTela('perfis');assert($('stepper').hidden,'profiles hide workflow steps');
    window.ContractoUI.mostrarTela('config');assert($('stepper').hidden,'settings hide workflow steps');
    window.ContractoUI.mostrarTela('inicio');assert(!$('stepper').hidden,'workflow restores steps');
    input('campo-0-nome_completo','PESSOA QA UM');input('campo-0-cpf','52998224725');input('campo-0-endereco','RUA QA');
    checkboxes()[1].click();await wait(()=>!$('btn-adicionar').disabled,'compose two profiles');
    assert($('campo-0-nome_completo').value==='PESSOA QA UM','draft preserved after composition');
    $('modo-simples').click();$('modo-avancado').click();
    assert($('campo-0-nome_completo').value==='PESSOA QA UM','draft preserved after mode change');
    checkboxes()[1].click();await wait(()=>!$('btn-adicionar').disabled,'compose single profile');
    input('campo-global-regime','B');
    assert(!$('campo-0-detalhe').parentElement.hidden,'conditional field visible');
    input('campo-global-regime','A');
    assert($('campo-0-detalhe').parentElement.hidden,'conditional field hidden');
    $('btn-adicionar').click();
    input('campo-1-nome_completo','PESSOA QA DOIS');input('campo-1-cpf','11144477735');input('campo-1-endereco','RUA QA');
    input('data-assinatura','14/09/2026');input('local-assinatura','CIDADE QA');
    $('btn-pasta').click();await wait(()=>!$('btn-gerar').disabled,'generation enabled');
    assert($('campo-0-dobro').value==='20,00','backend calculated preview displayed');
    const request=window.ContractoAPI.request;
    let responseLost=false;
    window.ContractoAPI.request=async(method,path,payload)=>{
      const result=await request(method,path,payload);
      if(path==='/api/v1/jobs/generate' && result.status===202 && !responseLost){responseLost=true;return {status:503,data:{code:'simulated_response_loss'}};}
      return result;
    };
    $('btn-gerar').click();$('btn-gerar').click();
    await wait(()=>!$('btn-retomar').hidden && !$('btn-retomar').disabled,'ambiguous send recoverable');
    assert(window.ContractoEtapa2.ocupado(),'ambiguous send blocks duplicates');
    $('btn-retomar').click();
    await wait(()=>$('lista-resultados').children.length===2 && !window.ContractoEtapa2.ocupado(),'generation terminal');
    assert($('manifesto-resumo').textContent.includes('2 gerado'),'generated manifest');
    $('btn-anexo').click();await wait(()=>$('lista-anexos').textContent.includes('anexo-qa.pdf'),'attachment appears');
    assert($('manifesto-resumo').textContent.includes('1 anexo'),'attachment retained with generated');
    $('btn-finalizar').click();$('btn-finalizar').click();
    await wait(()=>$('lista-resultados').children.length===3 && !window.ContractoEtapa2.ocupado(),'processing terminal');
    assert(!$('btn-abrir-pasta').hidden,'final folder available');
    assert($('btn-finalizar').disabled,'unchanged completed process cannot duplicate');
    $('lista-resultados').querySelector('button').click();
    await wait(()=>document.querySelector('.pdf-preview'),'viewer created');
    assert($('app').inert,'modal background inert');
    assert(document.querySelector('.pdf-preview').src.startsWith('blob:'),'viewer uses local blob');
    window.ContractoUI.fecharModal();assert(!$('app').inert,'modal releases background');
    if(window.__qaKeepResult){window.__qaResult={ok:true,checks};return;}
    window.ContractoUI.mostrarTela('inicio');
    assert(document.querySelector('[data-etapa="1"]').getAttribute('aria-current')==='step','navigation synchronized');
    input('campo-0-nome_completo','PESSOA QA EDITADA');
    assert($('btn-finalizar').disabled && !$('lista-resultados').children.length,'old result invalidated on edit');
    window.__qaResult={ok:true,checks};
  } catch(error) {window.__qaResult={ok:false,error:String(error),checks};}
})();
