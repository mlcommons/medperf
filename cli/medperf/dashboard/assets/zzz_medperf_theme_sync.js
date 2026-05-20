/**
 * Keeps Dash dashboard theme in sync with MedPerf WebUI:
 * - Same localStorage key and prefers-color-scheme fallback as base.html
 * - postMessage from parent (dashboard_wrapper) when user toggles theme
 * - Plotly relayout after theme change (graphs render async)
 * Palette aligned with web_ui/static/css/brand-tokens.css
 */
(function () {
    var FONT = "Instrument Sans, ui-sans-serif, system-ui, sans-serif";
    var INK = "#11141f";
    var SURFACE = "#f7f8fa";
    var MINT = "#ccebd4";
    var CARD_DARK = "#1f2433";
    var INK_DARK_PAGE = "#11141f";

    function medperfDashIsDark() {
        try {
            var v = localStorage.getItem("medperf-dark");
            return (
                v === "1" ||
                (v === null &&
                    window.matchMedia &&
                    window.matchMedia("(prefers-color-scheme: dark)").matches)
            );
        } catch (e) {
            return false;
        }
    }

    function medperfPlotlyRelayout() {
        if (typeof window.Plotly === "undefined") return;
        var dark = document.documentElement.classList.contains("dark");
        var plots = document.querySelectorAll(".js-plotly-plot");
        var i;
        var gd;
        var layout;
        if (dark) {
            layout = {
                paper_bgcolor: "rgba(0,0,0,0)",
                plot_bgcolor: CARD_DARK,
                font: { color: "#e5e7eb", family: FONT },
                title: { font: { color: "#ffffff", family: FONT } },
                legend: {
                    bgcolor: "rgba(24,28,40,0.95)",
                    bordercolor: "#3d455a",
                    font: { color: "#e5e7eb", family: FONT },
                },
                "xaxis.gridcolor": "#3d455a",
                "xaxis.linecolor": "#6b7280",
                "xaxis.zerolinecolor": "#4b5563",
                "xaxis.tickfont.color": "#c5c8d0",
                "yaxis.gridcolor": "#3d455a",
                "yaxis.linecolor": "#6b7280",
                "yaxis.zerolinecolor": "#4b5563",
                "yaxis.tickfont.color": "#c5c8d0",
            };
        } else {
            layout = {
                paper_bgcolor: "rgba(0,0,0,0)",
                plot_bgcolor: SURFACE,
                font: { color: INK, family: FONT },
                title: { font: { color: INK, family: FONT } },
                legend: {
                    bgcolor: "rgba(247,248,250,0.95)",
                    bordercolor: "#ebeef4",
                    font: { color: INK, family: FONT },
                },
                "xaxis.gridcolor": "#d8dce6",
                "xaxis.linecolor": "#9b9fad",
                "xaxis.zerolinecolor": "#d8dce6",
                "xaxis.tickfont.color": INK,
                "yaxis.gridcolor": "#d8dce6",
                "yaxis.linecolor": "#9b9fad",
                "yaxis.zerolinecolor": "#d8dce6",
                "yaxis.tickfont.color": INK,
            };
        }
        for (i = 0; i < plots.length; i++) {
            gd = plots[i];
            try {
                window.Plotly.relayout(gd, layout);
            } catch (e) {
                /* ignore per-figure errors */
            }
        }
    }

    function medperfDashApplyTheme(dark) {
        document.documentElement.classList.toggle("dark", !!dark);
        medperfPlotlyRelayout();
        setTimeout(medperfPlotlyRelayout, 200);
        setTimeout(medperfPlotlyRelayout, 800);
        setTimeout(medperfPlotlyRelayout, 2000);
    }

    window.addEventListener("message", function (ev) {
        if (!ev.data || ev.data.type !== "medperf-theme") return;
        medperfDashApplyTheme(!!ev.data.dark);
    });

    window.addEventListener("storage", function (ev) {
        if (ev.key !== "medperf-dark") return;
        medperfDashApplyTheme(ev.newValue === "1");
    });

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () {
            medperfDashApplyTheme(medperfDashIsDark());
        });
    } else {
        medperfDashApplyTheme(medperfDashIsDark());
    }
})();
