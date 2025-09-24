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
                    timeZone: 'America/Sao_Paulo',
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: false,
                });
            },
        },
    });

    candlestickSeries = chart.addSeries(LightweightCharts.CandlestickSeries, {
        upColor: '#10B981', // green-500
        downColor: '#EF4444', // red-500
        borderDownColor: '#EF4444',
        borderUpColor: '#10B981',
        wickDownColor: '#EF4444',
        wickUpColor: '#10B981',
    });

    // --- Plugin Initialization ---
    // A inicialização agora é feita dinamicamente quando os dados chegam.

    // --- Date Initialization ---
    function setDefaultDates() {
        const now = new Date();
        const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 9, 0, 0); // 09:00
        const endOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 18, 0, 0); // 18:00

        // Formato para input datetime-local: YYYY-MM-DDTHH:MM
        startDateInput.value = startOfDay.toISOString().slice(0, 16);
        endDateInput.value = endOfDay.toISOString().slice(0, 16);
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
        const url = `${API_BASE_URL}/api/history/${SYMBOL}?timeframe=${timeframe}&start=${start}:00&end=${end}:00`;

        try {
            console.log(`Fetching: ${url}`);
            const response = await fetch(url);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`Erro ao buscar dados: ${errorData.detail || response.statusText}`);
            }
            const data = await response.json();
            console.log(`Received ${data.length} data points.`);
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
                activeMarkers.forEach(marker => candlestickSeries.detachPrimitive(marker));
                activeMarkers = [];

                // 2. Cria e anexa os novos marcadores
                message.data.forEach(markerData => {
                    const startTime = new Date(`${markerData.Data}T${markerData.Hora}:00`).getTime() / 1000;
                    let endTime = new Date(`${markerData.Data}T18:00:00`).getTime() / 1000;
                    
                    // Verificar se o endTime está dentro do range visível
                    const timeScale = chart.timeScale();
                    const visibleRange = timeScale.getVisibleRange();
                    
                    if (visibleRange && endTime > visibleRange.to) {
                        // Se 18:00 está fora do range, usar o final do range visível
                        endTime = visibleRange.to;
                    }
                    
                    const p1 = {
                        time: startTime,
                        price: markerData.Preco + 1.0
                    };
                    const p2 = {
                        time: endTime,
                        price: markerData.Preco - 1.0
                    };
                    const color = markerData.Tipo === 'POC_VENDA' ? 'rgba(239, 68, 68, 0.7)' : 'rgba(16, 185, 129, 0.7)';

                    try {
                        const newRectangle = new RectanglePrimitive(chart, candlestickSeries, p1, p2, color);
                        candlestickSeries.attachPrimitive(newRectangle);
                        newRectangle.updateAllViews();
                        activeMarkers.push(newRectangle);
                    } catch (error) {
                        console.error('Error creating rectangle:', error);
                    }
                });
                
                // Forçar redesenho do gráfico
                chart.timeScale().fitContent();
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

