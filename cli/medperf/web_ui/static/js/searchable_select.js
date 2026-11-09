/*
 * Searchable entity pickers (see partials/searchable_select.html).
 *
 * The user types in a search box; matching entities are fetched from
 * /api/entity_search and the chosen entity ID is stored in a hidden input,
 * which is the value submitted with the form.
 */

(function () {
    var MIN_SEARCH_LENGTH = 2;
    var DEBOUNCE_MS = 300;

    /** Make a `.searchable-select` element (root) interactive. */
    function initSearchableSelect(root) {
        if (root.dataset.initialized === "true") return;
        root.dataset.initialized = "true";

        var hiddenInput = root.querySelector('input[type="hidden"]');
        var queryInput = root.querySelector(".searchable-select-query");
        var resultsList = root.querySelector(".searchable-select-results");
        var clearBtn = root.querySelector(".searchable-select-clear");
        var hintEl = root.querySelector(".searchable-select-hint");
        var debounceTimer = null;
        var activeIndex = -1;

        var entityType = root.dataset.entityType;
        var mineOnly = root.dataset.mineOnly === "true";
        var containerType = root.dataset.containerType || "";
        var allowedIds = root.dataset.allowedIds || "";
        var disabled = root.dataset.disabled === "true";

        /** Notify the form that the selected value changed. */
        function dispatchChange() {
            hiddenInput.dispatchEvent(new Event("change", { bubbles: true }));
            hiddenInput.dispatchEvent(new Event("input", { bubbles: true }));
        }

        /** Show or hide the hint below the search box. */
        function setHint(message, visible) {
            if (!hintEl) return;
            hintEl.textContent = message || "";
            hintEl.classList.toggle("hidden", !visible);
        }

        /** Show the clear button only when something is selected. */
        function updateClearButton() {
            if (!clearBtn) return;
            clearBtn.classList.toggle("hidden", !hiddenInput.value);
        }

        /** Hide the results list. */
        function closeResults() {
            resultsList.classList.add("hidden");
            queryInput.setAttribute("aria-expanded", "false");
            activeIndex = -1;
        }

        /** Show the results list. */
        function openResults() {
            resultsList.classList.remove("hidden");
            queryInput.setAttribute("aria-expanded", "true");
        }

        /** Text shown for an entity in the results: "ID - name". */
        function entityLabel(item) {
            if (item.label) return item.label;
            if (item.id != null && item.name) return item.name + " (ID: " + item.id + ")";
            return item.name || String(item.id || "");
        }

        /** Fill the results list with the found entities. */
        function renderResults(items) {
            resultsList.innerHTML = "";
            activeIndex = -1;
            if (!items.length) {
                var empty = document.createElement("li");
                empty.className = "px-4 py-2.5 text-sm text-muted-fg";
                empty.textContent = "No results found";
                empty.setAttribute("role", "option");
                resultsList.appendChild(empty);
                openResults();
                return;
            }

            items.forEach(function (item) {
                var label = entityLabel(item);
                var li = document.createElement("li");
                li.className = "searchable-select-option px-4 py-2.5 text-sm text-ink cursor-pointer hover:bg-brand-subtle";
                li.textContent = label;
                li.dataset.value = String(item.id);
                li.dataset.label = label;
                li.setAttribute("role", "option");
                li.addEventListener("mousedown", function (e) {
                    e.preventDefault();
                    selectOption(item.id, label);
                });
                resultsList.appendChild(li);
            });
            openResults();
        }

        /** Select an entity: store its ID and show its label in the search box. */
        function selectOption(value, label) {
            hiddenInput.value = value;
            queryInput.value = label;
            updateClearButton();
            closeResults();
            setHint("", false);
            dispatchChange();
        }

        /** Unselect the current entity. */
        function clearSelection() {
            hiddenInput.value = "";
            queryInput.value = "";
            updateClearButton();
            closeResults();
            setHint("", false);
            dispatchChange();
        }

        /** Build the /api/entity_search URL for the given query parameters. */
        function buildSearchUrl(params) {
            return "/api/entity_search?" + params.toString();
        }

        /**
         * Fetch the entities matching the given options (restricted by the picker's
         * entity type, container type, allowed IDs and "mine only" settings).
         */
        function fetchResults(options) {
            var params = new URLSearchParams({
                entity_type: entityType,
                mine_only: mineOnly ? "true" : "false",
                limit: "20",
            });
            if (containerType) params.append("container_type", containerType);
            if (allowedIds) params.append("ids", allowedIds);
            if (options.selectedId) {
                params.append("selected_id", String(options.selectedId));
            } else if (options.query) {
                params.append("q", options.query);
            }

            return fetch(buildSearchUrl(params), { credentials: "same-origin" })
                .then(function (res) {
                    if (!res.ok) throw new Error("Search failed");
                    return res.json();
                });
        }

        /** Search the entities matching the text typed in the search box. */
        function runSearch() {
            var query = queryInput.value.trim();
            if (query.length < MIN_SEARCH_LENGTH) {
                setHint("Type at least " + MIN_SEARCH_LENGTH + " characters to search", true);
                closeResults();
                return;
            }
            setHint("Searching…", true);
            fetchResults({ query: query })
                .then(function (data) {
                    setHint("", false);
                    renderResults(data.results || []);
                })
                .catch(function () {
                    setHint("Search failed. Try again.", true);
                    closeResults();
                });
        }

        if (root.dataset.selectedValue && !root.dataset.selectedLabel) {
            fetchResults({ selectedId: root.dataset.selectedValue })
                .then(function (data) {
                    var results = data.results || [];
                    if (results.length) {
                        selectOption(results[0].id, entityLabel(results[0]));
                    }
                })
                .catch(function () {});
        }

        queryInput.addEventListener("input", function () {
            if (hiddenInput.value && queryInput.value !== root.dataset.selectedLabel) {
                hiddenInput.value = "";
                updateClearButton();
                dispatchChange();
            }
            if (debounceTimer) clearTimeout(debounceTimer);
            debounceTimer = setTimeout(runSearch, DEBOUNCE_MS);
        });

        queryInput.addEventListener("focus", function () {
            if (queryInput.value.trim().length >= MIN_SEARCH_LENGTH) {
                runSearch();
            }
        });

        queryInput.addEventListener("keydown", function (e) {
            var options = resultsList.querySelectorAll(".searchable-select-option");
            if (e.key === "ArrowDown") {
                e.preventDefault();
                activeIndex = Math.min(activeIndex + 1, options.length - 1);
            } else if (e.key === "ArrowUp") {
                e.preventDefault();
                activeIndex = Math.max(activeIndex - 1, 0);
            } else if (e.key === "Enter" && activeIndex >= 0 && options[activeIndex]) {
                e.preventDefault();
                var opt = options[activeIndex];
                selectOption(opt.dataset.value, opt.dataset.label);
                return;
            } else if (e.key === "Escape") {
                closeResults();
                return;
            } else {
                return;
            }

            options.forEach(function (opt, idx) {
                opt.classList.toggle("bg-brand-subtle", idx === activeIndex);
            });
        });

        document.addEventListener("click", function (e) {
            if (!root.contains(e.target)) closeResults();
        });

        if (clearBtn) {
            clearBtn.addEventListener("click", function () {
                if (disabled) return;
                clearSelection();
                queryInput.focus();
            });
        }

        updateClearButton();
    }

    /** Initialize all the searchable selects of the page. */
    function initAll() {
        document.querySelectorAll(".searchable-select").forEach(initSearchableSelect);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initAll);
    } else {
        initAll();
    }

    window.initSearchableSelects = initAll;
})();
