$(document).ready(function () {
    let arquivosGerados = [];
    console.log('Processar botão clicado'); 
    function updateFileMessage(fileName) {
        $('.file-message').text(fileName ? `Arquivo selecionado: ${fileName}` : 'Arraste um arquivo ou clique para selecionar');
    }


    // Processar
    $('#btnProcessar').on('click', function (e) {
        e.preventDefault();

        const fileInput = $('.file-input')[0];
        if (!fileInput?.files?.length) return alert('Por favor, selecione um arquivo PDF primeiro.');

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
                $('#resultadoRecorrente').text(response.recorrente || '');
                $('#resultadoTipoRecurso').text(response.tipo_recurso || '');
                $('#resultadoResumo').text(response.resumo || '');
                $('#resumoPeticao').val(response.resumo || '');

                const argumentosList = $('#resultadoArgumentos');
                argumentosList.empty();
                (response.argumentos || []).forEach(arg => {
                    if (arg) argumentosList.append(`<li>${arg}</li>`);
                });

                arquivosGerados = response.arquivos || [];
                $('#btnDownloadDocx, #btnDownloadOdt').removeClass('disabled').attr('aria-disabled', 'false');
                $('#resultadosModal').modal('show');
            },
            error: function (xhr) {
                $('#loadingModal').modal('hide');
                const erro = xhr?.responseJSON?.erro || 'Erro ao processar o arquivo.';
                $('#mensagemErroAjax').text(erro);
                $('#alertaErro').fadeIn().addClass('show');
                setTimeout(() => $('#alertaErro').fadeOut().removeClass('show'), 5000);
            }
        });
    });

    // Visualizar .docx
    $('#btnVisualizarDocx').on('click', function () {
        if (!arquivosGerados.includes('docx')) {
            return alert('O arquivo .docx ainda não foi gerado. Processe uma petição primeiro.');
        }

        fetch('/download/docx')
            .then(res => res.blob())
            .then(blob => {
                const reader = new FileReader();
                reader.onload = function (e) {
                    mammoth.convertToHtml({ arrayBuffer: e.target.result })
                        .then(result => {
                            $('#previewDocx').html(result.value);
                        })
                        .catch(err => {
                            console.error(err);
                            alert('Erro ao exibir .docx');
                        });
                };
                reader.readAsArrayBuffer(blob);
            });
    });

    $('#btnUsarResumo').on('click', function () {
        const resumo = $('#resumoPeticao').val();
        $('#preVisualizacaoMinuta').val(resumo || '');
    });

    $('#btnAplicarResultados').on('click', function () {
        const resumo = $('#resultadoResumo').text();
        $('#resumoPeticao').val(resumo);
        $('#preVisualizacaoMinuta').val(resumo);
        $('#resultadosModal').modal('hide');
    });

    $('#btnSalvarRascunho').on('click', function () {
        const texto = $('#preVisualizacaoMinuta').val();
        alert(texto ? 'Rascunho salvo com sucesso!' : 'Não há conteúdo para salvar.');
    });

    $(document).on('click', '.tese-button', function () {
        const tese = $(this).data('tese');
        const textoAtual = $('#preVisualizacaoMinuta').val() || '';
        $.post('/aplicar_tese', JSON.stringify({ tese, texto_atual: textoAtual }), function (resp) {
            if (resp?.texto) $('#preVisualizacaoMinuta').val(resp.texto);
        }, 'json').fail(() => alert('Erro ao aplicar tese.'));
    });
});
