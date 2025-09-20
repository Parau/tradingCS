// #region Pane Renderer
class RectanglePaneRenderer {
    constructor(p1, p2, fillColor) {
        this._p1 = p1;
        this._p2 = p2;
        this._fillColor = fillColor;
    }

    draw(target) {
        target.useBitmapCoordinateSpace(scope => {
            if (
                this._p1.x === null ||
                this._p1.y === null ||
                this._p2.x === null ||
                this._p2.y === null
            ) return;

            const ctx = scope.context;
            
            // Calcular posições do retângulo
            const x1 = Math.round(this._p1.x * scope.horizontalPixelRatio);
            const y1 = Math.round(this._p1.y * scope.verticalPixelRatio);
            const x2 = Math.round(this._p2.x * scope.horizontalPixelRatio);
            const y2 = Math.round(this._p2.y * scope.verticalPixelRatio);
            
            const x = Math.min(x1, x2);
            const y = Math.min(y1, y2);
            const width = Math.abs(x2 - x1);
            const height = Math.abs(y2 - y1);

            if (width <= 0 || height <= 0) return;

            // Desenhar retângulo pontilhado
            ctx.strokeStyle = this._fillColor;
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
            ctx.beginPath();
            ctx.rect(x, y, width, height);
            ctx.stroke();
            ctx.setLineDash([]); // Reset line dash
        });
    }
}
// #endregion

// #region Pane View
class RectanglePaneView {
    constructor(source) {
        this._source = source;
        this._p1 = { x: null, y: null };
        this._p2 = { x: null, y: null };
    }

    update() {
        const series = this._source.series();
        const timeScale = this._source.chart().timeScale();
        const p1 = this._source.points().p1;
        const p2 = this._source.points().p2;

        this._p1.x = timeScale.timeToCoordinate(p1.time);
        this._p1.y = series.priceToCoordinate(p1.price);
        this._p2.x = timeScale.timeToCoordinate(p2.time);
        this._p2.y = series.priceToCoordinate(p2.price);
    }

    renderer() {
        return new RectanglePaneRenderer(this._p1, this._p2, this._source.color());
    }

    zOrder() {
        return 'top';
    }
}
// #endregion

// #region Primitive
class RectanglePrimitive {
    constructor(chart, series, p1, p2, color, visible = true) {
        this._chart = chart;
        this._series = series;
        this._paneViews = [new RectanglePaneView(this)];
        this._points = { p1, p2 };
        this._color = color;
        this._visible = visible;
    }

    updateAllViews() {
        this._paneViews.forEach(view => view.update());
    }

    // Métodos obrigatórios da interface ISeriesPrimitive
    paneViews() { 
        return this._paneViews; 
    }
    
    timeAxisViews() { 
        return []; 
    }
    
    priceAxisViews() { 
        return []; 
    }
    
    priceAxisPaneViews() { 
        return []; 
    }
    
    timeAxisPaneViews() { 
        return []; 
    }

    // Métodos de acesso para as Views
    chart() { 
        return this._chart; 
    }
    
    series() { 
        return this._series; 
    }
    
    points() { 
        return this._points; 
    }
    
    color() { 
        return this._color; 
    }
    
    visible() { 
        return this._visible; 
    }

    setVisible(visible) {
        this._visible = visible;
        this.updateAllViews();
    }
}
