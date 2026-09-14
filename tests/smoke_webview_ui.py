"""Real frontend -> bridge -> HTTP -> PDF. Synthetic dialog adapter; no personal data.

The JS drives DOM events in the actual WebView2 engine. Native file-picker clicks
are covered separately by manual QA. Run --visible to keep the final window open.
"""
import json
import os
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))


def main():
    import webview
    from reportlab.pdfgen import canvas
    from pypdf import PdfReader
    from server import LocalServer
    from webview_shell import ShellBridge
    from utils.profile_manager import CampoEntrada, FormularioModelo, Perfil

    errors = []
    with tempfile.TemporaryDirectory(prefix="contracto-ui-flow-") as temp:
        os.environ["APPDATA"] = os.environ["LOCALAPPDATA"] = temp
        folder = Path(temp)
        template = folder / "modelo.pdf"
        doc = canvas.Canvas(str(template))
        for i, name in enumerate(("NOME", "CPF", "ENDERECO")):
            doc.acroForm.textfield(name=name, x=40, y=700-i*40, width=450, height=25)
        doc.showPage(); doc.save()
        attachment = folder / "anexo-qa.pdf"
        doc = canvas.Canvas(str(attachment)); doc.drawString(40,700,"ANEXO QA ORIGINAL"); doc.showPage(); doc.save()
        original = attachment.read_bytes()
        output = folder / "saida"; output.mkdir()
        fields = [CampoEntrada(id="valor", rotulo="Valor", tipo="MOEDA", valor_padrao="10,00"),
                  CampoEntrada(id="dobro", rotulo="Total calculado", tipo="MOEDA", calculo="valor + valor"),
                  CampoEntrada(id="endereco", rotulo="Endereço", obrigatorio=True),
                  CampoEntrada(id="regime", rotulo="Regime", tipo="SELECAO", opcoes=["A", "B"], valor_padrao="A", escopo="global"),
                  CampoEntrada(id="detalhe", rotulo="Detalhe B", obrigatorio=True, visivel_quando=[{"regime":["B"]}])]
        profiles = [Perfil(nome="QA "+name, modo_fluxo="formulario_simples", max_participantes=2, formato_saida="PDF",
                           campos_entrada=fields,
                           formularios=[FormularioModelo("DOC"+name,str(template),mapeamento={"NOME":"participante.nome", "CPF":"participante.cpf", "ENDERECO":"participante.endereco"})])
                    for name in ("A", "B")]
        with LocalServer(profiles=profiles) as server:
            url=(ROOT / "frontend/index.html").as_uri()
            bridge=ShellBridge(server, frontend_url=url)
            window=webview.create_window("Contracto — QA sintético",url=url,js_api=bridge,width=1200,height=850,hidden="--visible" not in sys.argv)
            bridge._attach(window)
            class Dialogs:
                def selecionar_pasta(self): return output
                def selecionar_arquivo(self): return attachment
            bridge._dialogs=Dialogs()

            def probe():
                try:
                    assert window.events.loaded.wait(20), "WebView did not load"
                    if "--visual-start" in sys.argv:
                        assert "--visible" in sys.argv, "--visual-start requires --visible"
                        print("VISUAL FIXTURE: ready, synthetic profiles; no flow executed", flush=True)
                        return
                    if "--visible" in sys.argv:
                        window.evaluate_js("window.__qaKeepResult = true")
                    window.evaluate_js((ROOT / "tests/webview_flow.js").read_text(encoding="utf-8"))
                    deadline=time.monotonic()+90
                    result=None
                    while time.monotonic()<deadline:
                        result=window.evaluate_js("window.__qaResult || null")
                        if result: break
                        time.sleep(.1)
                    assert result and result.get("ok"), result
                    if "--layout" in sys.argv:
                        for width, height in ((1024,768),(1280,720),(1920,1080),(680,768)):
                            window.resize(width,height)
                            time.sleep(.3)
                            for theme in ("light", "dark"):
                                window.evaluate_js("ContractoUI.aplicarTema("+json.dumps(theme)+")")
                                for page in ("inicio","etapa2","perfis","config"):
                                    window.evaluate_js("ContractoUI.mostrarTela("+json.dumps(page)+")")
                                    layout=window.evaluate_js("""(() => {
                                      const controls=[...document.querySelectorAll('input,select,button')].filter(e=>e.getClientRects().length && !e.closest('[hidden]'));
                                      const clipped=controls.filter(e=>{const r=e.getBoundingClientRect();return r.left < -1 || r.right > innerWidth+1;}).map(e=>e.id||e.textContent);
                                      return {ok:document.documentElement.scrollWidth<=innerWidth+1 && !clipped.length,clipped,width:innerWidth,height:innerHeight};
                                    })()""")
                                    assert layout["ok"], (width,height,theme,page,layout)
                            print("LAYOUT OK",width,height,flush=True)
                    completed=[s for s in server.jobs._states.values() if s.status == "completed"]
                    assert len(completed)==2, [(s.status,s.error) for s in server.jobs._states.values()]
                    generated=completed[0]
                    assert len(generated.file_ids)==2
                    for key in generated.file_ids:
                        pdf=PdfReader(server.jobs.selections.resolve(key,"file"))
                        form=pdf.get_fields()
                        assert form["NOME"]["/V"].startswith("PESSOA QA"), form
                        assert form["ENDERECO"]["/V"] == "RUA QA", form
                    assert len(completed[1].file_ids)==3
                    texts=[PdfReader(server.jobs.selections.resolve(key,"file")).pages[0].extract_text() for key in completed[1].file_ids]
                    assert any("ANEXO QA ORIGINAL" in text for text in texts), texts
                    assert attachment.read_bytes()==original
                    print("WEBVIEW UI FLOW OK: " + json.dumps(result,ensure_ascii=False))
                except Exception as exc:
                    errors.append(str(exc))
                    print("WEBVIEW UI FLOW FAILED:",str(exc))
                finally:
                    if "--visible" not in sys.argv: window.destroy()
            webview.start(probe,gui="edgechromium",debug=False)
        assert not errors, errors


if __name__ == "__main__":
    main()
