// #region Pane Renderer
class RectanglePaneRenderer {
	constructor(view) {
		this._view = view;
	}

	draw(target) {
		target.useBitmapCoordinateSpace(scope => {
			if (!this._view.visible()) return;
			const points = this._view.points();
			if (points.p1.x === null || points.p1.y === null || points.p2.x === null || points.p2.y === null) {
                return;
            }
			const ctx = scope.context;
			const x = Math.min(points.p1.x, points.p2.x);
            const y = Math.min(points.p1.y, points.p2.y);
            const width = Math.abs(points.p2.x - points.p1.x);
            const height = Math.abs(points.p2.y - points.p1.y);

            if (width <= 0 || height <= 0) {
                return;
            }
			ctx.strokeStyle = this._view.color();
            ctx.lineWidth = 1;
            ctx.setLineDash([2, 3]);
            ctx.beginPath();
            ctx.rect(x, y, width, height);
            ctx.stroke();
		});
	}
}
// #endregion

// #region Pane View
class RectanglePaneView {
	constructor(source) {
		this._source = source;
		this._renderer = new RectanglePaneRenderer(this);
        this._points = {
            p1: { x: null, y: null },
            p2: { x: null, y: null },
        };
	}

	update() {
		const series = this._source.series();
		const timeScale = this._source.chart().timeScale();
		const p1 = this._source.points().p1;
		const p2 = this._source.points().p2;

		this._points.p1.x = timeScale.timeToCoordinate(p1.time);
		this._points.p1.y = series.priceToCoordinate(p1.price);
		this._points.p2.x = timeScale.timeToCoordinate(p2.time);
		this._points.p2.y = series.priceToCoordinate(p2.price);
	}

	renderer() {
		return this._renderer;
	}

    visible() { return this._source.visible(); }
    points() { return this._points; }
    color() { return this._source.color(); }
    zOrder() { return 'top'; }
}
// #endregion

// #region Primitive
// Esta é a implementação final e correta, que segue a interface ISeriesPrimitive.
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
	paneViews() { return this._paneViews; }
	timeAxisViews() { return []; } // Não desenhamos nada no eixo do tempo
	priceAxisViews() { return []; } // Não desenhamos nada no eixo de preço
    priceAxisPaneViews() { return []; }
    timeAxisPaneViews() { return []; }

    // Métodos de acesso para as Views
    chart() { return this._chart; }
    series() { return this._series; }
    points() { return this._points; }
    color() { return this._color; }
    visible() { return this._visible; }

    setVisible(visible) {
        this._visible = visible;
        this.updateAllViews();
    }
}
// #endregion
