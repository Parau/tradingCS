class RectanglePrimitive {
    constructor(time1, price1, time2, price2, color) {
        this._time1 = time1;
        this._price1 = price1;
        this._time2 = time2;
        this._price2 = price2;
        this._color = color;

        // As coordenadas em pixels serão calculadas no `update`
        this._x1 = 0;
        this._y1 = 0;
        this._x2 = 0;
        this._y2 = 0;
    }

    update(data) {
        const { chart, series } = data;

        // Converte as coordenadas de tempo/preço para coordenadas de pixel
        const timeScale = chart.timeScale();
        const priceScale = series.priceScale();

        this._x1 = timeScale.timeToCoordinate(this._time1);
        this._y1 = priceScale.priceToCoordinate(this._price1);
        this._x2 = timeScale.timeToCoordinate(this._time2);
        this._y2 = priceScale.priceToCoordinate(this._price2);
    }

    draw(ctx) {
        // Desenha o retângulo no canvas
        ctx.save();

        const x = Math.min(this._x1, this._x2);
        const y = Math.min(this._y1, this._y2);
        const width = Math.abs(this._x2 - this._x1);
        const height = Math.abs(this._y2 - this._y1);

        if (x === null || y === null || width <= 0 || height <= 0) {
            ctx.restore();
            return;
        }

        ctx.strokeStyle = this._color;
        ctx.lineWidth = 1;
        ctx.setLineDash([2, 3]); // Define a linha como pontilhada

        ctx.beginPath();
        ctx.rect(x, y, width, height);
        ctx.stroke();

        ctx.restore();
    }

    // Define que o desenho deve ficar por cima das velas
    zOrder() {
        return 'top';
    }
}

class RectanglePlugin {
    constructor() {
        this._primitives = [];
    }

    // Método chamado pelo gráfico para obter os primitivos a serem desenhados
    updateAllViews() {
        return this._primitives;
    }

    // Método para definir os dados das marcações
    setData(markers) {
        this._primitives = markers.map(marker => this._createPrimitiveFromMarker(marker));
    }

    _createPrimitiveFromMarker(marker) {
        // Converte a data e hora em um timestamp Unix (em segundos)
        // Ex: "2025-09-20" e "10:00" -> timestamp
        const startTimeStr = `${marker.Data}T${marker.Hora}:00`;
        const time1 = new Date(startTimeStr).getTime() / 1000;

        // O fim é às 18h do mesmo dia
        const endTimeStr = `${marker.Data}T18:00:00`;
        const time2 = new Date(endTimeStr).getTime() / 1000;

        const price1 = marker.Preco + 1.0;
        const price2 = marker.Preco - 1.0;

        const color = marker.Tipo === 'POC_VENDA' ? 'rgba(239, 68, 68, 0.7)' : 'rgba(16, 185, 129, 0.7)'; // red-500, green-500

        return new RectanglePrimitive(time1, price1, time2, price2, color);
    }
}
