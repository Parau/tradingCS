document.addEventListener('DOMContentLoaded', () => {
    const chartContainer = document.getElementById('chart-container');
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    const timeframeSelect = document.getElementById('timeframe');
    const updateButton = document.getElementById('update-chart');
    const wsStatus = document.querySelector('#ws-status span');

    const SYMBOL = 'WDOV25';
    const API_BASE_URL = 'http://127.0.0.1:8000';
    const WS_BASE_URL = 'ws://127.0.0.1:8000';

    let websocket;
    let candlestickSeries;
    let activeMarkers = []; // Array para rastrear os retângulos no gráfico

    // --- Chart Initialization ---
    const chart = LightweightCharts.createChart(chartContainer, {
        layout: {
            background: { type: 'solid', color: '#000000' },
            textColor: 'rgba(255, 255, 255, 0.9)',
        },
        localization: {
            locale: 'pt-BR',
        },
        grid: {
            vertLines: { color: 'rgba(197, 203, 206, 0.5)' },
            horzLines: { color: 'rgba(197, 203, 206, 0.5)' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
        },
        rightPriceScale: {
            borderColor: 'rgba(197, 203, 206, 0.8)',
        },
        timeScale: {
            borderColor: 'rgba(197, 203, 206, 0.8)',
            timeVisible: true,
            secondsVisible: false,
            tickMarkFormatter: time => {
                const date = new Date(time * 1000);
                return date.toLocaleTimeString('pt-BR', {
                    timeZone: 'UTC',
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: false,
                });
            },
        },
        
    });

    candlestickSeries = chart.addSeries(LightweightCharts.CandlestickSeries, {
        upColor: '#ffffffff', 
        downColor: '#000000ff', // red-500
        borderDownColor: '#a9a8a8ff',
        borderUpColor: '#ffffffff',
        wickDownColor: '#a9a8a8ff',
        wickUpColor: '#ffffffff',
    });

    // --- Plugin Initialization ---
    // A inicialização agora é feita dinamicamente quando os dados chegam.

    // --- Date Initialization ---
    function setDefaultDates() {
        const now = new Date();
        // Formatar manualmente para horário local (America/Sao_Paulo), assumindo 09:00 e 18:00 locais
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const startString = `${year}-${month}-${day}T09:00`;
        const endString = `${year}-${month}-${day}T18:30`;

        startDateInput.value = startString;
        endDateInput.value = endString;

            console.log('setDefaultDates -> startDateInput.value:', startDateInput.value, 'endDateInput.value:', endDateInput.value);
    console.log('navigator.language:', navigator.language);
    }

    // --- Data Fetching and WebSocket ---
    async function loadChartData() {
        const timeframe = timeframeSelect.value;
        const start = startDateInput.value;
        const end = endDateInput.value;

        if (!start || !end) {
            alert('Por favor, selecione data de início e fim.');
            return;
        }

        // Envia a string "ingênua", o backend vai interpretar como America/Sao_Paulo
        const url = `${API_BASE_URL}/api/history/${SYMBOL}?timeframe=${timeframe}&start=${start}:00Z&end=${end}:00Z`;

        try {
            console.log(`Fetching: ${url}`);
            const response = await fetch(url);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`Erro ao buscar dados: ${errorData.detail || response.statusText}`);
            }
            const data = await response.json();
            console.log(`Received ${data.length} data points.`);

            //Manter este código comentado porque é usado para debugar os dados recebidos do servidor
            /*data.forEach((point, index) => {
                const date = new Date(point.time * 1000);
                const formattedTime = date.toLocaleString('pt-BR', {
                    timeZone: 'UTC',
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: false,
                });
                console.log(`Point ${index}: time=${formattedTime}, open=${point.open}, high=${point.high}, low=${point.low}, close=${point.close}`);
            });*/


            candlestickSeries.setData(data);
            chart.timeScale().fitContent();
        } catch (error) {
            console.error(error);
            alert(error.message);
        }
    }

    function setupWebSocket() {
        // Fecha conexão antiga se existir
        if (websocket) {
            websocket.close();
        }

        const timeframe = timeframeSelect.value;
        const wsUrl = `${WS_BASE_URL}/ws/candles?symbol=${SYMBOL}&timeframe=${timeframe}`;
        console.log(`Connecting to WebSocket: ${wsUrl}`);

        websocket = new WebSocket(wsUrl);

        websocket.onopen = () => {
            console.log('WebSocket connected.');
            wsStatus.textContent = 'Conectado';
            wsStatus.className = 'text-green-500';
        };

        websocket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.type === 'candle') {
                candlestickSeries.update(message.data);
            } else if (message.type === 'markers') {
                console.log('Marker data received:', message.data.length, 'markers');

                // 1. Remove os marcadores antigos
                console.log('Removing', activeMarkers.length, 'existing markers');
                activeMarkers.forEach((marker, index) => {
                    try {
                        candlestickSeries.detachPrimitive(marker);
                        console.log(`Marker ${index} removed successfully`);
                    } catch (error) {
                        console.error(`Error removing marker ${index}:`, error);
                    }
                });
                activeMarkers.length = 0;

                // 2. Ordena os marcadores por data e hora
                const sortedMarkers = [...message.data].sort((a, b) => {
                    const dateTimeA = new Date(`${a.Data}T${a.Hora}:00`);
                    const dateTimeB = new Date(`${b.Data}T${b.Hora}:00`);
                    return dateTimeA - dateTimeB;
                });
                console.log('Sorted markers:', sortedMarkers.map(m => `${m.Tipo} ${m.Data} ${m.Hora} ${m.Preco}`));

                // 3. Agrupa por data para garantir que POCs só são válidos no mesmo dia
                const markersByDate = {};
                sortedMarkers.forEach(marker => {
                    if (!markersByDate[marker.Data]) {
                        markersByDate[marker.Data] = [];
                    }
                    markersByDate[marker.Data].push(marker);
                });
                console.log('Markers grouped by date:', Object.keys(markersByDate), 'days');

                // 4. Processa cada grupo de data
                Object.keys(markersByDate).forEach(date => {
                    const dayMarkers = markersByDate[date];
                    console.log(`Processing ${dayMarkers.length} markers for date ${date}`);
                    
                    dayMarkers.forEach((markerData, index) => {
                        const startTime = new Date(`${markerData.Data}T${markerData.Hora}:00Z`).getTime() / 1000;
                        let endTime;

                        // Encontra o próximo marcador do mesmo tipo no mesmo dia
                        const nextMarkerIndex = dayMarkers.findIndex((m, i) => 
                            i > index && m.Tipo === markerData.Tipo
                        );
                        console.log(`Marker ${index} (${markerData.Tipo}): looking for next marker of same type, found at index:`, nextMarkerIndex);

                        if (nextMarkerIndex !== -1) {
                            // Usa o horário do próximo marcador do mesmo tipo
                            const nextMarker = dayMarkers[nextMarkerIndex];
                            endTime = new Date(`${nextMarker.Data}T${nextMarker.Hora}:00Z`).getTime() / 1000;
                            console.log(`Using next marker time: ${nextMarker.Hora}`);
                        } else {
                            // Não há próximo marcador do mesmo tipo?
                            // Usa o final do range se ele estiver no mesmo dia ou 18:00 se o final do range for de outra data.
                            const timeScale = chart.timeScale();
                            const visibleRange = timeScale.getVisibleRange();
                            
                        if (visibleRange) {
                            // Verifica se o final do visibleRange está no mesmo dia que markerData.Data
                            const endDate = new Date(visibleRange.to * 1000);
                            const endDateString = endDate.toISOString().slice(0, 10); // Formato YYYY-MM-DD
                            
                            if (endDateString === markerData.Data) {
                                endTime = visibleRange.to;
                                console.log(`Using visible range end (same day):`, new Date(endTime * 1000));
                            } else {
                                // Fallback para 18:00 do mesmo dia (eu tenho um problema na renderização de que o horário do último candle muda dependendo do tempo do gráfio. como ainda não busquei solução para isso eu estou deixando até as 18:00 que atende a maioria dos timeframes selecionado)
                                endTime = new Date(`${markerData.Data}T18:00:00Z`).getTime() / 1000;
                                console.log(`Using 18:00 fallback (different day)`);
                            }
                        } else {
                            // Fallback para 18:00 do mesmo dia (eu tenho um problema na renderização de que o horário do último candle muda dependendo do tempo do gráfio. como ainda não busquei solução para isso eu estou deixando até as 18:00 que atende a maioria dos timeframes selecionado)
                            endTime = new Date(`${markerData.Data}T18:00:00Z`).getTime() / 1000;
                            console.log(`Using 18:00 fallback (no visible range)`);
                        }
                        }

                        // Garantir que endTime seja sempre maior que startTime
                        if (endTime <= startTime) {
                            endTime = startTime + 3600; // Adiciona 1 hora como mínimo
                            console.log(`Adjusted endTime to avoid invalid range`);
                        }

                        const p1 = {
                            time: startTime,
                            price: markerData.Preco + 0.5
                        };
                        const p2 = {
                            time: endTime,
                            price: markerData.Preco - 0.5
                        };
                        const color = markerData.Tipo === 'POC_VENDA' ? 'rgba(255, 0, 0, 1)' : 'rgba(16, 253, 8, 1)';

                        console.log(`Creating rectangle ${index}:`, {
                            type: markerData.Tipo,
                            p1: {...p1, time: new Date(p1.time * 1000).toISOString()},
                            p2: {...p2, time: new Date(p2.time * 1000).toISOString()},
                            color
                        });

                        try {
                            const newRectangle = new RectanglePrimitive(chart, candlestickSeries, p1, p2, color);
                            candlestickSeries.attachPrimitive(newRectangle);
                            newRectangle.updateAllViews();
                            activeMarkers.push(newRectangle);
                            console.log(`Rectangle ${index} created and attached successfully. Total active markers: ${activeMarkers.length}`);
                        } catch (error) {
                            console.error(`Error creating rectangle ${index}:`, error, {
                                startTime: new Date(startTime * 1000),
                                endTime: new Date(endTime * 1000),
                                p1, p2
                            });
                        }
                    });
                });
                
                console.log(`Final count - Total active markers: ${activeMarkers.length}`);
            }
        };

        websocket.onclose = () => {
            console.log('WebSocket disconnected.');
            wsStatus.textContent = 'Desconectado';
            wsStatus.className = 'text-gray-500';
        };

        websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            wsStatus.textContent = 'Erro';
            wsStatus.className = 'text-red-500';
        };
    }

    // --- Event Listeners ---
    updateButton.addEventListener('click', () => {
        loadChartData();
        setupWebSocket();
    });

    window.addEventListener('resize', () => {
        chart.resize(chartContainer.clientWidth, chartContainer.clientHeight);
    });

    // --- Initial Load ---
    setDefaultDates();
    loadChartData();
    setupWebSocket();
});

