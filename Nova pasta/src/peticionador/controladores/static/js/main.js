// src/peticionador/controladores/static/js/main.js
$(document).ready(function () {
    let ultimoResultadoProcessado = null;
    let arquivosGerados = [];

    console.log('JavaScript (main.js) carregado e pronto.');

    // Referências a elementos jQuery usados frequentemente
    const minutaTextArea = $('#preVisualizacaoMinuta');
    const resumoPeticaoTextArea = $('#resumoPeticao'); 
    const containerTesesProntas = $('#botoesModelosTesesContainer');
    const containerTesesAplicadas = $('#modelosTesesAplicadasContainer');
    const placeholderTesesAplicadas = $('#placeholderTesesAplicadas');

    // Função para atualizar a mensagem do arquivo selecionado
    function updateFileMessage(fileName) {
        $('.file-message').text(fileName ? `Arquivo selecionado: ${fileName}` : 'Arraste um arquivo PDF ou clique para selecionar');
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
            $('.file-input').prop('files', files); // Associa o arquivo ao input file escondido
            updateFileMessage(files[0].name);    // Atualiza a mensagem na interface
        }
    });
    $('.file-input').on('change', function() { // Quando um arquivo é selecionado pelo clique
        const fileInput = $(this)[0];
        if (fileInput && fileInput.files && fileInput.files.length > 0) {
            updateFileMessage(fileInput.files[0].name);
        } else {
            updateFileMessage(null);
        }
    });
    updateFileMessage(null); // Chama na inicialização para setar a mensagem padrão

    // --- Handler para o Botão "Processar Petição" (#btnProcessar) ---
    $('#btnProcessar').on('click', function (e) {
        e.preventDefault(); // Mantido
        const fileInput = $('.file-input')[0];
        if (!fileInput?.files?.length) {
            alert('Por favor, selecione um arquivo PDF para processar.');
            return;
        }
        ultimoResultadoProcessado = null; 
        $('#btnReabrirAnalise').hide();     

        const formData = new FormData(); // Mantido aqui
        formData.append('arquivo', fileInput.files[0]); // Mantido aqui

        $('#loadingModal').modal('show');
        $('#loadingModal .modal-body p').text('Analisando e processando a petição, por favor, aguarde...');

        const ajaxUrlProcessar = (typeof urlParaProcessar !== 'undefined') ? urlParaProcessar : '/processar';

        $.ajax({
            url: ajaxUrlProcessar, 
            type: 'POST',
            data: formData, // formData é definido acima
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
                    argumentosList.append($('<li>').addClass('list-group-item').text('Nenhuma tese/argumento aplicável identificado pela IA.'));
                }
                
                // ATUALIZA O TEXTAREA "resumoPeticao" com resumo E teses da IA
                let textoCombinadoParaResumoArea = "";                
                if (response.resumo) { 
                    textoCombinadoParaResumoArea += `RESUMO TÉCNICO DO RECURSO (GERADO PELA IA):\n${response.resumo}\n\n`;
                } else {
                    textoCombinadoParaResumoArea += `RESUMO TÉCNICO DO RECURSO (GERADO PELA IA):\n[Nenhum resumo gerado.]\n\n`;
                }

                if (response.argumentos && response.argumentos.length > 0) {
                    textoCombinadoParaResumoArea += "TESES E ARGUMENTOS APLICÁVEIS (SUGESTÕES DA IA):\n";
                    response.argumentos.forEach(arg => {
                        if (arg) textoCombinadoParaResumoArea += `- ${arg}\n`;
                    });
                } else {
                    textoCombinadoParaResumoArea += "TESES E ARGUMENTOS APLICÁVEIS (SUGESTÕES DA IA):\n[Nenhuma tese/argumento aplicável identificado pela IA.]\n";
                }
                resumoPeticaoTextArea.val(textoCombinadoParaResumoArea.trim());


                // Limpa a minuta principal e as teses aplicadas na interface
                if (minutaTextArea.hasClass('note-editor')) {
                    minutaTextArea.summernote('code', '');
                } else {
                    minutaTextArea.val('');
                }
                
                containerTesesAplicadas.find('.tese-button').each(function() {
                    $(this).removeClass('btn-success active').addClass('btn-outline-info');
                    $(this).find('i.fas.fa-check-circle').remove(); // Remove ícone de check
                    // Adicione aqui qualquer outro ícone que o botão "pronto" deveria ter, se houver
                    // Ex: $(this).prepend('<i class="fas fa-plus-circle mr-2"></i> ');
                    containerTesesProntas.append($(this)); // Move de volta para o container de teses prontas
                });

                // Opcional: Reordenar os botões na lista de "Teses Prontas" alfabeticamente
                const buttonsInProntas = containerTesesProntas.find('.tese-button').get();
                buttonsInProntas.sort(function(a, b) {
                    return $(a).text().trim().localeCompare($(b).text().trim());
                });
                $.each(buttonsInProntas, function(idx, itm) { containerTesesProntas.append(itm); });
                
                atualizarPlaceholderTesesAplicadas(); // Atualiza o placeholder se a lista de aplicadas estiver vazia
                $('#buscarModelosTeses').trigger('keyup'); // Atualiza a visibilidade da busca nas teses prontas
                
                atualizarPlaceholderTesesAplicadas();


                arquivosGerados = response.arquivos || [];
                const downloadUrlDocx = (typeof urlParaDownloadDocx !== 'undefined') ? urlParaDownloadDocx : '#';
                const downloadUrlOdt = (typeof urlParaDownloadOdt !== 'undefined') ? urlParaDownloadOdt : '#';

                if (arquivosGerados.includes('docx')) {
                    $('#btnDownloadDocx').removeClass('disabled').attr('aria-disabled', 'false').attr('href', downloadUrlDocx);
                } else {
                     $('#btnDownloadDocx').addClass('disabled').attr('aria-disabled', 'true').attr('href', '#');
                }
                if (arquivosGerados.includes('odt')) {
                    $('#btnDownloadOdt').removeClass('disabled').attr('aria-disabled', 'false').attr('href', downloadUrlOdt);
                } else {
                    $('#btnDownloadOdt').addClass('disabled').attr('aria-disabled', 'true').attr('href', '#');
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
                argumentosList.append($('<li>').addClass('list-group-item').text('Nenhuma tese/argumento aplicável identificado pela IA.'));
            }

            let textoCombinadoParaResumoArea = "";
            if (ultimoResultadoProcessado.resumo) {
                textoCombinadoParaResumoArea += `RESUMO TÉCNICO DO RECURSO (GERADO PELA IA):\n${ultimoResultadoProcessado.resumo}\n\n`;
            } else {
                textoCombinadoParaResumoArea += `RESUMO TÉCNICO DO RECURSO (GERADO PELA IA):\n[Nenhum resumo gerado.]\n\n`;
            }
            if (ultimoResultadoProcessado.argumentos && ultimoResultadoProcessado.argumentos.length > 0) {
                textoCombinadoParaResumoArea += "TESES E ARGUMENTOS APLICÁVEIS (SUGESTÕES DA IA):\n";
                ultimoResultadoProcessado.argumentos.forEach(arg => {
                    if (arg) textoCombinadoParaResumoArea += `- ${arg}\n`;
                });
            } else {
                textoCombinadoParaResumoArea += "TESES E ARGUMENTOS APLICÁVEIS (SUGESTÕES DA IA):\n[Nenhuma tese/argumento aplicável identificado pela IA.]\n";
            }
            resumoPeticaoTextArea.val(textoCombinadoParaResumoArea.trim());

            $('#resultadosModal').modal('show');
        } else {
            alert("Nenhuma análise anterior para reabrir. Processe um arquivo.");
        }
    });

    // --- Handler para o Botão "Aplicar à Minuta" (#btnAplicarResultados) do MODAL DE RESULTADOS ---
    $('#btnAplicarResultados').on('click', function () {
        let resumoTexto = "";
        let argumentosTexto = ""; 
        let textoCombinado = "";

        if (ultimoResultadoProcessado) {
            resumoTexto = ultimoResultadoProcessado.resumo || "[Nenhum resumo gerado.]";
            textoCombinado += `RESUMO TÉCNICO DO RECURSO (GERADO PELA IA):\n${resumoTexto}\n\n`;

            if (ultimoResultadoProcessado.argumentos && ultimoResultadoProcessado.argumentos.length > 0) {
                argumentosTexto = "TESES E ARGUMENTOS APLICÁVEIS (SUGESTÕES DA IA):\n";
                ultimoResultadoProcessado.argumentos.forEach(arg => {
                    if (arg) argumentosTexto += `- ${arg}\n`;
                });
            } else {
                argumentosTexto = "TESES E ARGUMENTOS APLICÁVEIS (SUGESTÕES DA IA):\n[Nenhuma tese/argumento aplicável identificado pela IA.]\n";
            }
            textoCombinado += argumentosTexto;
        } else {
            resumoTexto = $('#resultadoResumo').text().replace(/<br\s*\/?>/gi, '\n');
            textoCombinado += `RESUMO TÉCNICO DO RECURSO (GERADO PELA IA):\n${resumoTexto}\n\n`;
            const argsDoModal = [];
            $('#resultadoArgumentos li').each(function() {
                argsDoModal.push($(this).text());
            });
            if (argsDoModal.length > 0 && argsDoModal[0] !== 'Nenhuma tese/argumento aplicável identificado pela IA.') {
                 textoCombinado += "TESES E ARGUMENTOS APLICÁVEIS (SUGESTÕES DA IA):\n";
                 argsDoModal.forEach(arg => textoCombinado += `- ${arg}\n`);
            } else {
                 textoCombinado += "TESES E ARGUMENTOS APLICÁVEIS (SUGESTÕES DA IA):\n[Nenhuma tese/argumento aplicável identificado pela IA.]\n";
            }
        }
        
        resumoPeticaoTextArea.val(textoCombinado.trim());
        
        const placeholderMinuta = "A minuta das contrarrazões será gerada aqui pela IA após você selecionar as teses e clicar em 'Gerar peça (com IA)'.";
        if (minutaTextArea.hasClass('note-editor')) { 
            minutaTextArea.summernote('code', `<p><i>${placeholderMinuta}</i></p>`); // Para Summernote, use HTML
        } else {
            minutaTextArea.val(placeholderMinuta); // Para textarea normal
        }

        $('#resultadosModal').modal('hide');
        alert("Informações da IA aplicadas. Selecione as teses desejadas e clique em 'Gerar peça (com IA)'.");
    });
    
    // --- LÓGICA PARA BOTÕES DE TESE NA PÁGINA INICIAL (index.html) ---
    function atualizarPlaceholderTesesAplicadas() {
        if (containerTesesAplicadas.find('.tese-button').length === 0) {
            placeholderTesesAplicadas.show();
        } else {
            placeholderTesesAplicadas.hide();
        }
    }
    
    $(document).on('click', '#botoesModelosTesesContainer .tese-button, #modelosTesesAplicadasContainer .tese-button', function(event) {
        const $button = $(this);
        
        // Não precisamos mais de teseId ou textoCompleto aqui para modificar a minuta diretamente,
        // pois a minuta só será construída pelo botão "Gerar peça (com IA)".
        // Apenas movemos o botão e alteramos sua aparência.

        if ($button.parent().attr('id') === 'botoesModelosTesesContainer') {
            // Mover de "Prontas" para "Aplicadas"
            $button.removeClass('btn-outline-info').addClass('btn-success active'); 
            $button.find('i.fas.fa-plus-circle').remove(); // Remove ícone de "adicionar" se houver
            $button.prepend('<i class="fas fa-check-circle mr-2"></i> '); 
            containerTesesAplicadas.append($button); 
        } 
        else if ($button.parent().attr('id') === 'modelosTesesAplicadasContainer') {
            // Mover de "Aplicadas" para "Prontas"
            $button.removeClass('btn-success active').addClass('btn-outline-info'); 
            $button.find('i.fas.fa-check-circle').remove(); // Remove ícone de "check"
            // Opcional: Adicionar ícone de "plus" ao voltar para prontas
            // $button.prepend('<i class="fas fa-plus-circle mr-2"></i> '); 
            containerTesesProntas.append($button); 

            // Reordenar na lista de prontas
            const buttonsInProntas = containerTesesProntas.find('.tese-button').get();
            buttonsInProntas.sort(function(a, b) {
                return $(a).text().trim().localeCompare($(b).text().trim());
            });
            $.each(buttonsInProntas, function(idx, itm) { containerTesesProntas.append(itm); });
        }

        atualizarPlaceholderTesesAplicadas();
        $('#buscarModelosTeses').trigger('keyup'); 
    });

    $('#buscarModelosTeses').on('keyup', function() {
        const valorBusca = $(this).val().toLowerCase();
        containerTesesProntas.find('.tese-button').each(function() { 
            const textoBotao = $(this).text().toLowerCase();
            $(this).toggle(textoBotao.includes(valorBusca));
        });
    });

    atualizarPlaceholderTesesAplicadas(); 

    // --- NOVO Handler para o Botão "Gerar peça (com IA)" ---
    $(document).on('click', '#btnGerarPecaIA', function () { 
        // const resumoTecnico = resumoPeticaoTextArea.val(); // NÃO FAÇA ISSO, pois pode ter as sugestões de teses da IA misturadas.

        // FAÇA ISSO: Pegue o resumo técnico original da IA armazenado em ultimoResultadoProcessado
        let resumoTecnicoOriginalParaIA = "";
        if (ultimoResultadoProcessado && ultimoResultadoProcessado.resumo) {
            resumoTecnicoOriginalParaIA = ultimoResultadoProcessado.resumo;
        } else {
            // Se por algum motivo 'ultimoResultadoProcessado.resumo' não estiver disponível,
            // podemos tentar pegar do campo #resumoPeticao, mas com cuidado para extrair só a parte do resumo.
            // Esta é uma lógica de fallback mais complexa e pode não ser 100% precisa.
            const textoCompletoCampo2 = resumoPeticaoTextArea.val();
            const match = textoCompletoCampo2.match(/RESUMO TÉCNICO DO RECURSO \(GERADO PELA IA\):\n([\s\S]*?)\n\n(TESES E ARGUMENTOS APLICÁVEIS|----)/); // Tenta capturar até as teses ou a linha de separação
            if (match && match[1]) {
                resumoTecnicoOriginalParaIA = match[1].trim();
                console.warn("Usando resumo extraído do textarea, pois ultimoResultadoProcessado.resumo não estava disponível.");
            } else {
                 // Se nem isso funcionar, pegue o conteúdo completo do textarea, alertando o usuário.
                resumoTecnicoOriginalParaIA = textoCompletoCampo2.trim();
                if (!resumoTecnicoOriginalParaIA) {
                    alert("O resumo técnico (campo 2) está vazio e não foi possível obter a análise original da IA. Processe o PDF novamente ou preencha o resumo.");
                    return;
                }
                console.warn("Usando conteúdo completo do campo 2 como resumo, pois o resumo original da IA não foi encontrado claramente.");
            }
        }

        if (!resumoTecnicoOriginalParaIA.trim()) { // Verifica se o resumo que será enviado não está vazio
            alert("O resumo técnico original da IA não pôde ser determinado. Por favor, processe o PDF ou verifique o conteúdo do campo 2.");
            return;
        }
        
        let tesesAplicadasTextos = [];
        $('#modelosTesesAplicadasContainer .tese-button').each(function() {
            tesesAplicadasTextos.push($(this).data('texto')); 
        });

        if (tesesAplicadasTextos.length === 0) {
            alert("Selecione ao menos uma tese (movendo-a para 'Teses aplicadas na minuta') para gerar a peça.");
            return;
        }

        let tipoRecursoDetectado = "REsp"; 
        let dadosProcesso = {
            recorrente: "Recorrente não identificado",
            numero_processo: "Número não identificado"
            // Adicione outros defaults se o seu modelo .odt os espera e eles podem não vir do ultimoResultadoProcessado
        };

        if (ultimoResultadoProcessado) {
            if (ultimoResultadoProcessado.tipo_recurso && ultimoResultadoProcessado.tipo_recurso !== "Indeterminado") {
                tipoRecursoDetectado = ultimoResultadoProcessado.tipo_recurso;
            }
            dadosProcesso.recorrente = ultimoResultadoProcessado.recorrente || dadosProcesso.recorrente;
            // Tenta pegar o numero_processo de ultimoResultadoProcessado.estrutura_base se existir
            if (ultimoResultadoProcessado.estrutura_base && ultimoResultadoProcessado.estrutura_base.numero_processo) {
                 dadosProcesso.numero_processo = ultimoResultadoProcessado.estrutura_base.numero_processo;
            } else {
                 dadosProcesso.numero_processo = ultimoResultadoProcessado.numero_processo || dadosProcesso.numero_processo; // Fallback para o campo que existia
            }            
        }
        
        $('#loadingModal').modal('show');
        $('#loadingModal .modal-body p').text('Gerando peça com IA, por favor, aguarde...');

        const ajaxUrlGerarPeca = (typeof urlParaGerarPecaIA !== 'undefined') ? urlParaGerarPecaIA : '/gerar_peca_com_ia';

        $.ajax({
            url: ajaxUrlGerarPeca, 
            type: 'POST',
            contentType: 'application/json', 
            data: JSON.stringify({
                resumo_tecnico: resumoTecnicoOriginalParaIA, // ENVIA O RESUMO TÉCNICO PURO DA IA
                teses_selecionadas: tesesAplicadasTextos,
                tipo_recurso: tipoRecursoDetectado,
                dados_processo: dadosProcesso
            }),
            success: function(response) {
                $('#loadingModal').modal('hide');
            
                if (response.minuta_gerada) {
                    if (minutaTextArea.hasClass('note-editor')) {
                        minutaTextArea.summernote('code', response.minuta_gerada.replace(/\n/g, '<br>'));
                    } else {
                        minutaTextArea.val(response.minuta_gerada);
                    }
            
                    alert("Peça gerada com IA e atualizada na minuta!");
            
                    // ✅ Ativa os botões de download Word/LibreOffice
                    $('#btnDownloadDocx').removeClass('disabled')
                        .attr('aria-disabled', 'false')
                        .attr('href', '/download/minuta_gerada_docx');
            
                    $('#btnDownloadOdt').removeClass('disabled')
                        .attr('aria-disabled', 'false')
                        .attr('href', '/download/minuta_gerada_odt');
            
                } else if (response.erro) {
                    alert("Erro ao gerar peça com IA: " + response.erro);
                }
            },
            
        });
    });
    

    // --- Funcionalidade do Menu Hambúrguer e Sidebar ---
    const sidebar = $('#sidebarMenu');
    const mainContentArea = $('.main-content-area'); 

    $('#btnMenu').on('click', function() {
        const sidebarWidth = sidebar.width();
        if (sidebarWidth === 0 || sidebar.css('width') === '0px') {
            sidebar.css('width', '280px'); 
            if (mainContentArea.length) { 
                 mainContentArea.css('margin-left', '280px');
            }
        } else {
            sidebar.css('width', '0'); 
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

    $('#linkPaginaInicial').on('click', function(e) { 
        e.preventDefault();
        if (typeof urlParaIndex !== 'undefined') {
            window.location.href = urlParaIndex;
        } else {
            console.error("Erro: urlParaIndex não está definida. Verifique layout.html.");
        }
    });

    $('#linkGerenciarModelos').on('click', function(e) {
        e.preventDefault();
        if (typeof urlParaGerenciarModelos !== 'undefined') {
            window.location.href = urlParaGerenciarModelos;
        } else {
            console.error("Erro: urlParaGerenciarModelos não está definida. Verifique layout.html.");
        }
    });

    $('#linkRecarregarTrabalhos').on('click', function(e) {
        e.preventDefault();
        alert('Funcionalidade "Recarregar trabalhos" a ser implementada!');
        sidebar.css('width', '0');
        if (mainContentArea.length) { mainContentArea.css('margin-left', '0');}
    });

}); // Fim do $(document).ready