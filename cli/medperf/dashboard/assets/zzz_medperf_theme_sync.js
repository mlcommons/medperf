/**
 * Keeps Dash dashboard theme in sync with MedPerf WebUI:
 * - Same localStorage key and prefers-color-scheme fallback as base.html
 * - postMessage from parent (dashboard_wrapper) when user toggles theme
 * - Plotly relayout after theme change (graphs render async)
 */
(function () {
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
        for (i = 0; i < plots.length; i++) {
            gd = plots[i];
            try {
                if (dark) {
                    window.Plotly.relayout(gd, {
                        paper_bgcolor: "rgba(0,0,0,0)",
                        plot_bgcolor: "#111827",
                        font: {
                            color: "#e5e7eb",
                            family: "Inter, ui-sans-serif, system-ui, sans-serif",
                        },
                        title: { font: { color: "#f9fafb" } },
                        legend: {
                            bgcolor: "rgba(31,41,55,0.95)",
                            bordercolor: "#374151",
                            font: { color: "#e5e7eb" },
                        },
                        "xaxis.gridcolor": "#374151",
                        "xaxis.linecolor": "#6b7280",
                        "xaxis.zerolinecolor": "#4b5563",
                        "xaxis.tickfont.color": "#d1d5db",
                        "yaxis.gridcolor": "#374151",
                        "yaxis.linecolor": "#6b7280",
                        "yaxis.zerolinecolor": "#4b5563",
                        "yaxis.tickfont.color": "#d1d5db",
                    });
                } else {
                    window.Plotly.relayout(gd, {
                        paper_bgcolor: "rgba(0,0,0,0)",
                        plot_bgcolor: "#f9fafb",
                        font: {
                            color: "#374151",
                            family: "Inter, ui-sans-serif, system-ui, sans-serif",
                        },
                        title: { font: { color: "#1f2937" } },
                        legend: {
                            bgcolor: "rgba(249,250,251,0.95)",
                            bordercolor: "#e5e7eb",
                            font: { color: "#374151" },
                        },
                        "xaxis.gridcolor": "#e5e7eb",
                        "xaxis.linecolor": "#9ca3af",
                        "xaxis.zerolinecolor": "#d1d5db",
                        "xaxis.tickfont.color": "#4b5563",
                        "yaxis.gridcolor": "#e5e7eb",
                        "yaxis.linecolor": "#9ca3af",
                        "yaxis.zerolinecolor": "#d1d5db",
                        "yaxis.tickfont.color": "#4b5563",
                    });
                }
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
