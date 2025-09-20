// #region Pane Renderer
// Este objeto é responsável apenas por desenhar na tela.
class RectanglePaneRenderer {
	constructor(view) {
		this._view = view;
	}

	draw(target) {
		target.useBitmapCoordinateSpace(scope => {
			const view = this._view;
			if (!view.visible() || view.points().p1.x === null || view.points().p1.y === null || view.points().p2.x === null || view.points().p2.y === null) {
                return;
            }
			const ctx = scope.context;
			const x = Math.min(view.points().p1.x, view.points().p2.x);
            const y = Math.min(view.points().p1.y, view.points().p2.y);
            const width = Math.abs(view.points().p2.x - view.points().p1.x);
            const height = Math.abs(view.points().p2.y - view.points().p1.y);

            if (width <= 0 || height <= 0) {
                return;
            }
			ctx.strokeStyle = view.color();
            ctx.lineWidth = 1;
            ctx.setLineDash([2, 3]); // Linha pontilhada
            ctx.beginPath();
            ctx.rect(x, y, width, height);
            ctx.stroke();
		});
	}
}
// #endregion

// #region Pane View
// Este objeto representa a visão do primitivo no painel principal do gráfico.
// Ele calcula as coordenadas e retorna o objeto Renderer.
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

    visible() {
        return this._source.visible();
    }

    points() {
        return this._points;
    }

    color() {
        return this._source.color();
    }

    zOrder() {
        return 'top';
    }
}
// #endregion

// #region Primitive
// Este é o objeto principal, a "fonte" de dados para o nosso primitivo.
// Ele é o que é anexado à série do gráfico.
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

	paneViews() {
		return this._paneViews;
	}

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
// #endregion
