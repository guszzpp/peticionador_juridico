$(document).ready(function() {
    // Variáveis globais
    let arquivosGerados = [];
    
    // Área de drag and drop para upload
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
        $('.file-input').prop('files', files);
        if (files && files.length > 0) {
            updateFileMessage(files[0].name);
        }
    });
    
    $('.file-input').on('change', function() {
        const fileInput = $(this)[0];
        if (fileInput && fileInput.files && fileInput.files.length > 0) {
            const fileName = fileInput.files[0].name;
            updateFileMessage(fileName);
        }
    });
    
    function updateFileMessage(fileName) {
        if (fileName) {
            $('.file-message').text(`Arquivo selecionado: ${fileName}`);
        } else {
            $('.file-message').text('Arraste um arquivo ou clique para selecionar');
        }
    }
    
    // Processar petição
    $('#btnProcessar').on('click', function() {
        const fileInput = $('.file-input')[0];
        if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
            alert('Por favor, selecione um arquivo PDF primeiro.');
            return;
        }
        
        const formData = new FormData();
        formData.append('arquivo', fileInput.files[0]);
        
        // Mostrar modal de carregamento
        $('#loadingModal').modal('show');
        
        $.ajax({
            url: '/processar',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                // Esconder modal de carregamento
                $('#loadingModal').modal('hide');
                
                // Preencher o modal de resultados
                $('#resultadoRecorrente').text(response.recorrente || '');
                $('#resultadoTipoRecurso').text(response.tipo_recurso || '');
                $('#resultadoResumo').text(response.resumo || '');
                
                // Limpar e preencher a lista de argumentos
                const argumentosList = $('#resultadoArgumentos');
                argumentosList.empty();
                
                if (response.argumentos && Array.isArray(response.argumentos)) {
                    response.argumentos.forEach(function(argumento) {
                        if (argumento) {
                            argumentosList.append(`<li>${argumento}</li>`);
                        }
                    });
                }
                
                // Armazenar informações sobre arquivos gerados
                if (response.arquivos && Array.isArray(response.arquivos)) {
                    arquivosGerados = response.arquivos;
                }
                
                // Exibir o modal de resultados
                $('#resultadosModal').modal('show');
                
                // Preencher o campo de resumo
                $('#resumoPeticao').val(response.resumo || '');
            },
            error: function(xhr, status, error) {
                $('#loadingModal').modal('hide');
                let mensagemErro = 'Erro ao processar arquivo';
                
                if (xhr && xhr.responseJSON && xhr.responseJSON.erro) {
                    mensagemErro += ': ' + xhr.responseJSON.erro;
                }
                
                alert(mensagemErro);
            }
        });
    });
    
    // Usar resumo na peça
    $('#btnUsarResumo').on('click', function() {
        const resumo = $('#resumoPeticao').val();
        if (resumo) {
            $('#preVisualizacaoMinuta').val(resumo);
        } else {
            alert('O resumo da petição está vazio.');
        }
    });
    
    // Aplicar resultados da análise
    $('#btnAplicarResultados').on('click', function() {
        const resumo = $('#resultadoResumo').text();
        if (resumo) {
            $('#resumoPeticao').val(resumo);
            $('#preVisualizacaoMinuta').val(resumo);
        }
        $('#resultadosModal').modal('hide');
    });
    
    // Aplicar tese selecionada
    $(document).on('click', '.tese-button', function() {
        const tese = $(this).data('tese');
        const textoAtual = $('#preVisualizacaoMinuta').val() || '';
        
        $.ajax({
            url: '/aplicar_tese',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                tese: tese,
                texto_atual: textoAtual
            }),
            success: function(response) {
                if (response && response.texto) {
                    $('#preVisualizacaoMinuta').val(response.texto);
                }
            },
            error: function() {
                alert('Erro ao aplicar tese.');
            }
        });
    });
    
    // Download da minuta
    $(document).on('click', '.dropdown-item[data-format]', function(e) {
        e.preventDefault();
        const formato = $(this).data('format');
        
        if (arquivosGerados && arquivosGerados.includes(formato)) {
            window.location.href = `/download/${formato}`;
        } else {
            alert(`Arquivo no formato ${formato} não está disponível. Processe uma petição primeiro.`);
        }
    });
    
    // Salvar rascunho (simulação)
    $('#btnSalvarRascunho').on('click', function() {
        const textoMinuta = $('#preVisualizacaoMinuta').val();
        if (textoMinuta) {
            // Aqui seria implementada a funcionalidade de salvar no servidor
            // Como é uma simulação, apenas mostraremos um alerta
            alert('Rascunho salvo com sucesso!');
        } else {
            alert('Não há conteúdo para salvar.');
        }
    });
    
    // Filtro de busca para teses
    $(document).on('keyup', '.search-box input', function() {
        const valor = $(this).val().toLowerCase();
        const container = $(this).closest('.card-body').find('.teses-container, .modelo-buttons');
        
        if (container.length > 0) {
            container.find('button').each(function() {
                const texto = $(this).text().toLowerCase();
                $(this).toggle(texto.indexOf(valor) > -1);
            });
        }
    });
    
    // Toggle da sidebar em dispositivos móveis
    $('#btnToggleSidebar').on('click', function() {
        $('.sidebar').toggleClass('active');
    });
    
    // Fechar sidebar ao clicar fora em dispositivos móveis
    $(document).on('click', function(e) {
        if ($('.sidebar').hasClass('active') && 
            !$(e.target).closest('.sidebar').length && 
            !$(e.target).closest('#btnToggleSidebar').length) {
            $('.sidebar').removeClass('active');
        }
    });
});