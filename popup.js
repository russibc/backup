document.getElementById('xmlInput').addEventListener('change', (e) => {
    const file = e.target.files[0];
    const statusEl = document.getElementById('status');
    statusEl.className = 'alert alert-info';

    if (!file) {
        statusEl.textContent = "Nenhum arquivo selecionado.";
        return;
    }

    const reader = new FileReader();

    reader.onload = function(e) {
        try {
            const parser = new DOMParser();
            const xml = parser.parseFromString(e.target.result, "text/xml");

            // Processar cabeçalho profissional
            const medicoNome = xml.querySelector("Cabecalho > Medico > Nome")?.textContent || "MÉDICO";
            const medicoTitulo = xml.querySelector("Cabecalho > Medico > Titulo")?.textContent || "";
            const medicoCRM = xml.querySelector("Cabecalho > Medico > CRM")?.textContent || "";

            // Processar rodapé profissional
            const email = xml.querySelector("Rodape > Contatos > Email")?.textContent || "";
            const telefone = xml.querySelector("Rodape > Contatos > Telefone")?.textContent || "";
            const instagram = xml.querySelector("Rodape > Contatos > Instagram")?.textContent || "";

            // Construir HTML com estilo profissional
            let html = `
            <div style="font-family: 'Montserrat', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; position: relative; min-height: 100vh;">
                <!-- Cabeçalho -->
                <div style="text-align: center; margin-bottom: 40px;">
                    <h1 style="font-size: 28pt; font-weight: 700; color: #0056a3; margin: 0; text-transform: uppercase;">${medicoNome}</h1>
                    <p style="font-size: 14pt; font-weight: 600; margin: 5px 0;">${medicoTitulo}</p>
                    <p style="font-size: 14pt; margin: 5px 0 20px 0;">${medicoCRM}</p>
                    <div style="border-bottom: 2px solid #0056a3; width: 80%; margin: 0 auto;"></div>
                    <h2 style="color: #0056a3; font-size: 20pt; margin-top: 20px;">ORIENTAÇÕES MÉDICAS</h2>
                </div>

                <!-- Paciente -->
                <div style="margin-bottom: 30px;">
                    <p style="font-size: 12pt;"><strong>Paciente:</strong> ${xml.querySelector("Paciente > Nome")?.textContent || "Não informado"}</p>
                    <p style="font-size: 12pt;"><strong>Data:</strong> ${xml.querySelector("Paciente > Data")?.textContent || ""}</p>
                </div>

                <!-- Conteúdo -->
                <div style="margin-bottom: 60px;">
            `;

            // Processar seções
            xml.querySelectorAll("Secao").forEach(secao => {
                const titulo = secao.getAttribute("nome") || "Seção";
                html += `
                    <div style="margin-bottom: 25px;">
                        <h3 style="color: #0056a3; font-size: 16pt; border-bottom: 1px solid #eee; padding-bottom: 5px;">
                            ${titulo}
                        </h3>
                `;

                secao.querySelectorAll("Item").forEach(item => {
                    html += `
                        <p style="font-size: 12pt; margin: 8px 0 8px 15px; position: relative;">
                            <span style="position: absolute; left: 0; color: #0056a3;">•</span>
                            ${item.textContent}
                        </p>
                    `;
                });

                secao.querySelectorAll("Importante").forEach(imp => {
                    html += `
                        <div style="background-color: #fff8e1; border-left: 4px solid #ffc107; 
                                padding: 10px; margin: 15px 0 15px 15px; font-size: 12pt;">
                            <strong>⚠️ IMPORTANTE:</strong> ${imp.textContent}
                        </div>
                    `;
                });

                html += `</div>`;
            });

            html += `</div>`; // Fecha div de conteúdo

            // Rodapé profissional (posicionado no final da página)
            html += `
                <div style="position: absolute; bottom: 20px; left: 0; right: 0; text-align: center; 
                        font-size: 10pt; color: #0056a3; border-top: 1px solid #ddd; padding-top: 15px;">
                    <div>
                        ${email} <span style="margin: 0 10px;">|</span> 
                        ${telefone} <span style="margin: 0 10px;">|</span> 
                        ${instagram}
                    </div>
                </div>
            </div>
            `;

            // Gerar PDF
            const container = document.createElement("div");
            container.innerHTML = html;
            document.body.appendChild(container);

            statusEl.textContent = "Gerando PDF...";
            statusEl.className = 'alert alert-warning';

            // Configurações avançadas para PDF profissional
            const options = {
                filename: 'orientacoes_medicas_dr_bernardino.pdf',
                html2canvas: { 
                    scale: 2,
                    letterRendering: true,
                    useCORS: true
                },
                jsPDF: {
                    unit: 'mm',
                    format: 'a4',
                    orientation: 'portrait'
                },
                pagebreak: { mode: ['avoid-all', 'css', 'legacy'] },
                margin: [15, 15, 15, 15]
            };

            html2pdf().set(options).from(container).save().then(() => {
                container.remove();
                statusEl.textContent = "PDF gerado com sucesso!";
                statusEl.className = 'alert alert-success';
            });

        } catch (err) {
            console.error("[ERRO]", err);
            statusEl.textContent = "Erro: " + err.message;
            statusEl.className = 'alert alert-danger';
        }
    };

    reader.onerror = () => {
        statusEl.textContent = "Erro ao ler o arquivo XML.";
        statusEl.className = 'alert alert-danger';
    };

    reader.readAsText(file);
    statusEl.textContent = "Processando XML...";
});