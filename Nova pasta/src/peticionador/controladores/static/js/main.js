// src/peticionador/controladores/static/js/main.js
$(document).ready(function () {
    let ultimoResultadoProcessado = null;
    let arquivosGerados = [];

    console.log('JavaScript (main.js) carregado e pronto.');

    function updateFileMessage(fileName) {
        $('.file-message').text(fileName ? `Arquivo selecionado: ${fileName}` : 'Arraste um arquivo ou clique para selecionar');
    }

    // --- Handlers de Upload ---
    $('.file-drop-area').on('dragover', function(e) {
        e.preventDefault();
        $(this).addClass('is-active');
    });
    $('.file-drop-area').on('dragleave', function(e) {
        e.preventDefault();
        $(this).removeClass('is-active');
    });
    $('.file-drop-area').on('drop', function(e) {
        e.preventDefault();
        $(this).removeClass('is-active');
        const files = e.originalEvent.dataTransfer.files;
        if (files && files.length > 0) {
            $('.file-input').prop('files', files);
            updateFileMessage(files[0].name);
        }
    });
    $('.file-input').on('change', function() {
        const fileInput = $(this)[0];
        if (fileInput && fileInput.files && fileInput.files.length > 0) {
            updateFileMessage(fileInput.files[0].name);
        } else {
            updateFileMessage(null);
        }
    });
    updateFileMessage(null); // Inicializa

    // --- Handler para o Botão "Processar Petição" (#btnProcessar) ---
    $('#btnProcessar').on('click', function (e) {
        e.preventDefault();
        const fileInput = $('.file-input')[0];
        if (!fileInput?.files?.length) {
            alert('Por favor, selecione um arquivo PDF para processar.');
            return;
        }
        ultimoResultadoProcessado = null; // Limpa cache anterior
        $('#btnReabrirAnalise').hide();     // Esconde botão de reabrir

        const formData = new FormData();
        formData.append('arquivo', fileInput.files[0]);
        $('#loadingModal').modal('show');

        $.ajax({
            url: '/processar',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function (response) {
                $('#loadingModal').modal('hide');
                console.log("Sucesso AJAX /processar:", response);
                ultimoResultadoProcessado = response;

                $('#resultadoRecorrente').text(response.recorrente || 'N/A');
                $('#resultadoTipoRecurso').text(response.tipo_recurso || 'N/A');
                $('#resultadoResumo').html(response.resumo ? response.resumo.replace(/\n/g, '<br>') : 'Nenhum resumo gerado.');
                
                const argumentosList = $('#resultadoArgumentos');
                argumentosList.empty();
                if (response.argumentos && response.argumentos.length > 0) {
                    response.argumentos.forEach(arg => {
                        if (arg) argumentosList.append($('<li>').addClass('list-group-item').text(arg));
                    });
                } else {
                    argumentosList.append($('<li>').addClass('list-group-item').text('Nenhuma tese/argumento aplicável identificado.'));
                }
                
                $('#resumoPeticao').val(response.resumo || '');

                arquivosGerados = response.arquivos || [];
                if (arquivosGerados.length > 0) {
                    $('#btnDownloadDocx, #btnDownloadOdt').removeClass('disabled').attr('aria-disabled', 'false')
                        .attr('href', '/download/docx'); // Define href dinamicamente se necessário ou mantenha estático
                    $('#btnDownloadOdt').attr('href', '/download/odt');
                } else {
                    $('#btnDownloadDocx, #btnDownloadOdt').addClass('disabled').attr('aria-disabled', 'true')
                        .attr('href', '#');
                }
                
                $('#resultadosModal').modal('show');
                if (ultimoResultadoProcessado) {
                    $('#btnReabrirAnalise').show();
                }
            },
            error: function (xhr) {
                $('#loadingModal').modal('hide');
                console.error("Erro AJAX /processar:", xhr);
                const erroMsg = xhr?.responseJSON?.erro || 'Erro desconhecido ao processar o arquivo. Verifique os logs do servidor.';
                alert(`Erro no processamento: ${erroMsg}`);
            }
        });
    });

    // --- Handler para o Botão "Reabrir Última Análise" (#btnReabrirAnalise) ---
    $('#btnReabrirAnalise').on('click', function() {
        if (ultimoResultadoProcessado) {
            $('#resultadoRecorrente').text(ultimoResultadoProcessado.recorrente || 'N/A');
            $('#resultadoTipoRecurso').text(ultimoResultadoProcessado.tipo_recurso || 'N/A');
            $('#resultadoResumo').html(ultimoResultadoProcessado.resumo ? ultimoResultadoProcessado.resumo.replace(/\n/g, '<br>') : 'Nenhum resumo gerado.');
            const argumentosList = $('#resultadoArgumentos');
            argumentosList.empty();
            if (ultimoResultadoProcessado.argumentos && ultimoResultadoProcessado.argumentos.length > 0) {
                ultimoResultadoProcessado.argumentos.forEach(arg => {
                    if (arg) argumentosList.append($('<li>').addClass('list-group-item').text(arg));
                });
            } else {
                argumentosList.append($('<li>').addClass('list-group-item').text('Nenhuma tese/argumento aplicável identificado.'));
            }
            $('#resultadosModal').modal('show');
        } else {
            alert("Nenhuma análise anterior para reabrir. Processe um arquivo.");
        }
    });

    // --- Handler para o Botão "Aplicar à Minuta" (#btnAplicarResultados) ---
    $('#btnAplicarResultados').on('click', function () {
        let resumoParaAplicar = "";
        let argsParaAplicar = [];
        if (ultimoResultadoProcessado) {
            resumoParaAplicar = ultimoResultadoProcessado.resumo || "";
            argsParaAplicar = ultimoResultadoProcessado.argumentos || [];
        } else {
            resumoParaAplicar = $('#resultadoResumo').text(); // Fallback
        }
        $('#resumoPeticao').val(resumoParaAplicar);
        let textoMinuta = `RESUMO TÉCNICO DA PETIÇÃO DO RECORRENTE:\n${resumoParaAplicar}\n\n--- TESES E ARGUMENTOS PARA CONTRARRAZÕES ---\n`;
        if (argsParaAplicar.length > 0) {
            argsParaAplicar.forEach(arg => {
                textoMinuta += `- ${arg}\n`;
            });
        } else {
            textoMinuta += "Nenhuma tese específica sugerida pela IA para este caso.\n";
        }
        $('#preVisualizacaoMinuta').val(textoMinuta.trim());
        $('#resultadosModal').modal('hide');
    });

    // --- Handler para o Botão "Visualizar .docx" (#btnVisualizarDocx) ---
    $('#btnVisualizarDocx').on('click', function () {
        if (!arquivosGerados || !arquivosGerados.includes('docx')) {
            alert('O arquivo .docx ainda não foi gerado. Processe uma petição primeiro.');
            return;
        }
        fetch('/download/docx')
            .then(res => {
                if (!res.ok) throw new Error(`Erro HTTP ao buscar DOCX: ${res.status}`);
                return res.blob();
            })
            .then(blob => {
                if (blob.size === 0) throw new Error("Arquivo DOCX recebido está vazio.");
                const reader = new FileReader();
                reader.onload = function (e) {
                    mammoth.convertToHtml({ arrayBuffer: e.target.result })
                        .then(result => { $('#previewDocx').html(result.value); })
                        .catch(err => {
                            console.error("Erro Mammoth.js:", err);
                            alert('Erro ao converter .docx para visualização.');
                        });
                };
                reader.onerror = () => alert('Erro ao ler o arquivo .docx.');
                reader.readAsArrayBuffer(blob);
            })
            .catch(err => {
                console.error("Erro Visualizar DOCX:", err);
                alert(`Erro ao visualizar o .docx: ${err.message}. Verifique logs do servidor e console.`);
            });
    });

    // --- Handler para o Botão "Salvar Rascunho" (#btnSalvarRascunho) ---
    $('#btnSalvarRascunho').on('click', function () {
        const texto = $('#preVisualizacaoMinuta').val();
        alert(texto ? 'Rascunho salvo com sucesso! (Simulado)' : 'Não há conteúdo para salvar.');
    });

    // Em main.js, dentro de $(document).ready()
// Substitua o handler .tese-button anterior por este:

// Guarda o estado dos botões (texto e se está aplicado)
let estadoModelosTeses = {}; // Ex: { "Contestação": {texto: "...", aplicado: false}, "Súmula 7": {texto: "...", aplicado: false} }

// Função para renderizar os botões nas duas listas
function renderizarBotoesModelosTeses() {
    const containerProntas = $('#botoesModelosTesesContainer'); // Onde os botões de seleção ficam
    const containerAplicadas = $('#modelosTesesAplicadasContainer');
    const placeholderAplicadas = $('#placeholderTesesAplicadas');
    
    containerProntas.find('.tese-button-dinamico').remove(); // Remove botões dinâmicos antigos para não duplicar
    containerAplicadas.find('.tese-button-dinamico').remove();
    
    let algumaAplicada = false;

    // Popula estadoModelosTeses a partir dos botões HTML existentes na primeira vez
    if (Object.keys(estadoModelosTeses).length === 0) {
        $('#botoesModelosTesesContainer .tese-button').each(function() {
            const nomeBotao = $(this).text().trim();
            const textoConteudo = $(this).data('texto') || nomeBotao;
            if (!estadoModelosTeses[nomeBotao]) { // Evita sobrescrever se já processado
                 estadoModelosTeses[nomeBotao] = { nome: nomeBotao, texto: textoConteudo, aplicado: false, originalContainer: 'prontas' };
            }
            $(this).addClass('tese-button-dinamico'); // Adiciona classe para gerenciamento
        });
    }
    
    // Percorre o estado para criar/mover os botões
    for (const nomeBotao in estadoModelosTeses) {
        const item = estadoModelosTeses[nomeBotao];
        const $button = $('<button></button>')
            .addClass('btn btn-block mb-2 tese-button tese-button-dinamico')
            .attr('data-texto', item.texto)
            .text(item.nome);

        if (item.aplicado) {
            $button.addClass('active btn-danger').removeClass('btn-outline-secondary'); // Estilo para aplicado (com opção de remover)
            $button.append(' <i class="fas fa-times-circle ml-2"></i>'); // Ícone de remover
            containerAplicadas.append($button);
            algumaAplicada = true;
        } else {
            // Determina a cor original base (poderia ser mais sofisticado)
            if (item.originalContainer === 'prontas' || $(`#botoesModelosTesesContainer button[data-texto="${item.texto}"]`).length > 0){
                 $button.addClass('btn-outline-primary'); // Ou btn-outline-info dependendo da origem
            } else {
                 $button.addClass('btn-outline-info'); 
            }
            containerProntas.append($button);
        }
    }

    if (algumaAplicada) {
        placeholderAplicadas.hide();
    } else {
        placeholderAplicadas.show();
    }
}

// Evento de clique unificado para os botões de tese/modelo
$(document).on('click', '.tese-button-dinamico', function () {
    const $button = $(this);
    const nomeBotao = $button.text().trim().replace(/ <i class="fas fa-times-circle ml-2"><\/i>$/, '').trim(); // Remove ícone se houver
    
    if (!estadoModelosTeses[nomeBotao]) {
        console.error("Estado não encontrado para o botão:", nomeBotao);
        return;
    }

    const item = estadoModelosTeses[nomeBotao];
    const textoParaAplicar = item.texto;
    const blocoId = gerarIdParaBloco(textoParaAplicar); // Reutiliza sua função gerarIdParaBloco

    const inicioDelimitador = `\n\n\n`;
    const fimDelimitador = `\n\n\n`;
    const textoComDelimitadores = `${inicioDelimitador}- ${textoParaAplicar}\n${fimDelimitador}`;

    let minutaAtual = $('#preVisualizacaoMinuta').val() || '';

    if (item.aplicado) { // Se já está aplicado, queremos remover
        const regexEscapedInicio = inicioDelimitador.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regexEscapedFim = fimDelimitador.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regexParaRemover = new RegExp(regexEscapedInicio + "[\\s\\S]*?" + regexEscapedFim, 'g');
        
        minutaAtual = minutaAtual.replace(regexParaRemover, '');
        item.aplicado = false;
        console.log(`Bloco "${nomeBotao}" REMOVIDO da minuta.`);
    } else { // Se não está aplicado, queremos adicionar
        // Verifica se já não existe para evitar duplicidade (embora o estado deva controlar)
        if (minutaAtual.indexOf(inicioDelimitador) === -1) {
            minutaAtual += textoComDelimitadores;
        }
        item.aplicado = true;
        console.log(`Bloco "${nomeBotao}" ADICIONADO à minuta.`);
    }

    $('#preVisualizacaoMinuta').val(minutaAtual.replace(/\n{3,}/g, '\n\n').trim());
    renderizarBotoesModelosTeses(); // Re-renderiza os botões nas listas corretas
});

// Chamar na carga inicial para popular estadoModelosTeses a partir do HTML
// e renderizar os botões dinamicamente pela primeira vez.
renderizarBotoesModelosTeses();

    $(document).on('click', '.tese-button', function () {
        const $button = $(this);
        const textoDoBotao = $button.text().trim();
        const textoParaAplicar = $button.data('texto') || textoDoBotao;
        const blocoId = gerarIdParaBloco(textoParaAplicar); // Usa textoParaAplicar para ID mais estável

        const inicioDelimitador = ``;
        const fimDelimitador = ``;
        const textoFormatadoParaInserir = `- ${textoParaAplicar}\n`;
        const textoComDelimitadores = `\n\n${inicioDelimitador}\n${textoFormatadoParaInserir}${fimDelimitador}\n\n`;

        let minutaAtual = $('#preVisualizacaoMinuta').val() || '';

        const regexEscapedInicio = inicioDelimitador.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regexEscapedFim = fimDelimitador.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regexParaRemover = new RegExp(`\\s*${regexEscapedInicio}[\\s\\S]*?${regexEscapedFim}\\s*`, 'g');

        if ($button.hasClass('active')) {
            minutaAtual = minutaAtual.replace(regexParaRemover, '');
            $button.removeClass('active');
            if ($button.closest('.card-body').find('h5').text().includes("Modelos")) { // Ajuste para o seletor do card
                $button.removeClass('btn-primary').addClass('btn-outline-primary');
            } else {
                $button.removeClass('btn-info').addClass('btn-outline-info');
            }
        } else {
            if (minutaAtual.indexOf(inicioDelimitador) === -1) { // Evita duplicar o mesmo bloco delimitado
                minutaAtual += textoComDelimitadores;
            }
            $button.addClass('active');
            if ($button.closest('.card-body').find('h5').text().includes("Modelos")) {
                $button.removeClass('btn-outline-primary').addClass('btn-primary');
            } else {
                $button.removeClass('btn-outline-info').addClass('btn-info');
            }
        }
        $('#preVisualizacaoMinuta').val(minutaAtual.replace(/\n{3,}/g, '\n\n').trim()); // Limpa múltiplas quebras de linha
    });

    // --- Funcionalidade do Menu Hambúrguer e Sidebar ---
    const sidebar = $('#sidebarMenu');
    const mainContentArea = $('.main-content-area'); // Usa a classe que definimos no layout

    $('#btnMenu').on('click', function() {
        const sidebarWidth = sidebar.width();
        if (sidebarWidth === 0 || sidebar.css('width') === '0px') {
            sidebar.css('width', '280px'); // Abre o sidebar
            if (mainContentArea.length) { // Se usar a funcionalidade de empurrar
                 mainContentArea.css('margin-left', '280px');
            }
        } else {
            sidebar.css('width', '0'); // Fecha o sidebar
            if (mainContentArea.length) {
                mainContentArea.css('margin-left', '0');
            }
        }
    });

    $('#btnCloseSidebar').on('click', function() {
        sidebar.css('width', '0');
        if (mainContentArea.length) {
            mainContentArea.css('margin-left', '0');
        }
    });

    $('#linkGerenciarModelos').on('click', function(e) {
        e.preventDefault();
        window.location.href = "/gerenciar_modelos";
    });

    $('#linkRecarregarTrabalhos').on('click', function(e) {
        e.preventDefault();
        alert('Funcionalidade "Recarregar Trabalhos" a ser implementada!');
        sidebar.css('width', '0');
        if (mainContentArea.length) { mainContentArea.css('margin-left', '0');}
    });

}); 