## Contracto v5.5.1

Acertos no modelo **MO 29300 (DAMP)** e no texto dos campos.

### Corrigido
- **Acentos e hífen errados no visualizador** (ex.: "COMUNH˜O", "CAMOCIM›CE"): o valor dos campos passa a ser gravado de forma que os visualizadores leem certo. A impressão já saía correta.
- **Data do casamento** não cobre mais a vírgula e o ponto final.
- **"Possuo imóvel em"**: campo maior e ponto final acompanhando.
- **Endereço do imóvel**: campo bem mais largo, a letra encolhe menos.

### Importante
- Esta é a primeira versão que dá para instalar **pelo próprio aplicativo** (Configurações → Atualização), a partir da 5.5.0.

### Validação
- Testes unitários: OK. Renderização do modelo conferida em PDFium.
- **Não verificado:** o visualizador exato em que o erro de acento apareceu (a causa foi identificada no arquivo, não reproduzida lá); caminho de atualização pelo app.

### Artefatos
- `Contracto_Setup_v5.5.1.exe` (51.3 MiB), instalador. SHA-256: `3D92ED1E638A7501A07A34A444FFE6E1741EE26B71E85A050377880ED845EC67`
- `Contracto_v5.5.1.zip` (66.6 MiB), portátil. SHA-256: `607DBB89241A742D55A734DC3C56DCFBB8CC6705D065733F2D292F6F095F2DEE`
- `latest.json`, lido pelo atualizador do aplicativo.
