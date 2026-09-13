"""Integração opcional real: HTTP -> Word/GS -> saída publicada. Windows/Word/GS."""
from test_local_api import TestLocalAPI


def main():
    test = TestLocalAPI()
    test.setUp()
    try:
        status, caps = test.http("/api/v1/capabilities")
        assert status == 200 and caps["word"] and caps["ghostscript"], caps
        file = test.root / "contract.rtf"
        file.write_text(r"{\rtf1\ansi Contracto HTTP integration}", encoding="ascii")
        file_id = test.server.jobs.selections.register(file, "file")
        original = file.read_bytes()
        status, job = test.http("/api/v1/jobs/process", {
            "participants": [test.participant], "output_id": test.output_id,
            "attachments": [{"file_id": file_id, "document_type": "CONTRATO"}],
            "format": "PDF/A-2b"})
        assert status == 202, job
        # Word pode demorar no primeiro lançamento.
        import time
        for _ in range(500):
            _, result = test.http(f"/api/v1/jobs/{job['job_id']}")
            if result["status"] in {"completed", "failed", "cancelled"}:
                break
            time.sleep(0.1)
        assert result["status"] == "completed", result
        pdf = test.server.jobs.selections.resolve(result["file_ids"][0], "file")
        from services.pdfa_converter import validar_pdfa
        from pypdf import PdfReader
        assert validar_pdfa(pdf)
        with pdf.open("rb") as stream:
            assert "Contracto HTTP integration" in PdfReader(stream).pages[0].extract_text()
        assert file.read_bytes() == original
        assert not list(test.output.glob(".contracto-*"))
        print("SMOKE API ENGINES: OK — HTTP, Word, Ghostscript, conteúdo e preservação do RTF.")
    finally:
        test.cleanup()


if __name__ == "__main__":
    main()
