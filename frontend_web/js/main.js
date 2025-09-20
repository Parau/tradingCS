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
    let rectanglePlugin;

    // --- Chart Initialization ---
    const chart = LightweightCharts.createChart(chartContainer, {
        layout: {
            background: { type: 'solid', color: '#000000' },
            textColor: 'rgba(255, 255, 255, 0.9)',
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
            // Formata o tempo para o fuso horário de São Paulo (UTC-3)
            tickMarkFormatter: (time, tickMarkType, locale) => {
                const date = new Date(time * 1000);
                // Usamos toLocaleString para obter a data e hora formatada corretamente
                // para o Brasil, no fuso horário de São Paulo.
                // Isso garante que 12:00 UTC seja exibido como 09:00.
                const options = {
                    year: '2-digit',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    timeZone: 'America/Sao_Paulo',
                };
                // O tickMarkFormatter pode ser chamado para diferentes níveis de zoom.
                // Podemos querer mostrar apenas a hora, ou data + hora.
                // Por simplicidade, vamos mostrar a hora para os ticks mais comuns.
                // LightweightCharts.TickMarkType.Year = 0;
                // LightweightCharts.TickMarkType.Month = 1;
                // LightweightCharts.TickMarkType.DayOfMonth = 2;
                // LightweightCharts.TickMarkType.Time = 3;
                // LightweightCharts.TickMarkType.TimeWithSeconds = 4;
                if (tickMarkType === 3 || tickMarkType === 4) {
                     return date.toLocaleTimeString('pt-BR', { timeZone: 'America/Sao_Paulo', hour: '2-digit', minute: '2-digit' });
                }
                // Para outros tipos de marcação (dia, mês, ano), podemos usar um formato diferente.
                return date.toLocaleDateString('pt-BR', { timeZone: 'America/Sao_Paulo' });
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
    rectanglePlugin = new RectanglePlugin();
    candlestickSeries.attachPrimitive(rectanglePlugin);

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

        // Pega os valores dos inputs (ex: "2025-09-19T09:00")
        const startLocalValue = startDateInput.value;
        const endLocalValue = endDateInput.value;

        if (!startLocalValue || !endLocalValue) {
            alert('Por favor, selecione data de início e fim.');
            return;
        }

        // Converte o horário local do input para um objeto Date do JS,
        // e então para uma string ISO 8601 em UTC.
        // O navegador lida com a conversão do fuso horário local para UTC.
        const startUTC = new Date(startLocalValue).toISOString();
        const endUTC = new Date(endLocalValue).toISOString();

        const url = `${API_BASE_URL}/api/history/${SYMBOL}?timeframe=${timeframe}&start=${startUTC}&end=${endUTC}`;

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
                // console.log('Candle update received:', message.data);
                candlestickSeries.update(message.data);
            } else if (message.type === 'markers') {
                console.log('Marker data received:', message.data);
                rectanglePlugin.setData(message.data);
                // O gráfico precisa ser "notificado" para redesenhar os primitivos.
                // Forçar um pequeno ajuste no timescale faz isso.
                chart.timeScale().scrollToPosition(chart.timeScale().scrollPosition());
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
