class METARMapAirportCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._built = false;
  }

  setConfig(config) {
    this._config = { ...config };
    this._updateValues();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._built) {
      this._buildDOM();
      this._built = true;
    }
    this._updateOptions();
    this._updateValues();
  }

  _buildDOM() {
    this.shadowRoot.innerHTML = `
      <style>
        .row { padding: 8px 0; }
        label { display: block; font-size: 0.85em; color: var(--secondary-text-color); margin-bottom: 4px; }
        select, input {
          width: 100%; padding: 8px; border-radius: 4px;
          border: 1px solid var(--divider-color);
          background: var(--card-background-color);
          color: var(--primary-text-color);
          font-size: 1em; box-sizing: border-box;
        }
      </style>
      <div class="row">
        <label>Airport Sensor</label>
        <select id="entity"></select>
      </div>
      <div class="row">
        <label>Label (optional — defaults to ICAO from sensor name)</label>
        <input id="label" type="text" placeholder="e.g. KDEN">
      </div>
    `;

    this.shadowRoot.querySelector("#entity").addEventListener("change", e => {
      this._config = { ...this._config, entity: e.target.value };
      this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config } }));
    });

    this.shadowRoot.querySelector("#label").addEventListener("input", e => {
      this._config = { ...this._config, label: e.target.value };
      this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config } }));
    });
  }

  _updateOptions() {
    const select = this.shadowRoot.querySelector("#entity");
    if (!select || !this._hass) return;
    const current = this._config?.entity || "";
    const airports = Object.keys(this._hass.states)
      .filter(eid => this._hass.states[eid].attributes.raw_metar !== undefined)
      .sort();
    select.innerHTML = airports
      .map(e => `<option value="${e}" ${e === current ? "selected" : ""}>${e}</option>`)
      .join("");
    // Auto-select first option when no entity is configured yet
    if (!current && airports.length > 0) {
      this._config = { ...this._config, entity: airports[0] };
      this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config } }));
    }
  }

  _updateValues() {
    const select = this.shadowRoot.querySelector("#entity");
    const input = this.shadowRoot.querySelector("#label");
    if (select && this._config?.entity) select.value = this._config.entity;
    if (input && this._config?.label !== undefined) input.value = this._config.label || "";
  }
}

class METARMapAirportCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  static getConfigElement() {
    return document.createElement("metarmap25-airport-card-editor");
  }

  static getStubConfig() {
    return { entity: "" };
  }

  setConfig(config) {
    this._config = config;
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _entityBase() {
    return this._config.entity.replace(/^sensor\./, "");
  }

  _icaoLabel(stateObj) {
    if (this._config.label) return this._config.label;
    const name = stateObj.attributes.friendly_name || "";
    return name.split(" ").pop().toUpperCase();
  }

  _render() {
    const hass = this._hass;
    const stateObj = hass.states[this._config.entity];

    if (!stateObj) {
      this.shadowRoot.innerHTML = `<ha-card><div style="padding:16px;color:var(--error-color)">Unknown entity: ${this._config.entity}</div></ha-card>`;
      return;
    }

    const base = this._entityBase();
    const category = stateObj.state;
    const attrs = stateObj.attributes;
    const color = attrs.color || "#888888";
    const rawMetar = attrs.raw_metar || "No METAR data";
    const icao = this._icaoLabel(stateObj);

    const windyObj = hass.states[`binary_sensor.${base}_windy`];
    const snowObj  = hass.states[`binary_sensor.${base}_snow`];
    const thunderObj = hass.states[`binary_sensor.${base}_thunder`];

    const isWindy   = windyObj?.state === "on";
    const hasSnow   = snowObj?.state === "on";
    const hasThunder = thunderObj?.state === "on";

    const windSpeed = attrs.wind_speed_kt || 0;
    const windGust  = attrs.wind_gust_kt  || 0;
    const windLabel = windGust > 0 ? `${windSpeed}kt G${windGust}kt` : `${windSpeed}kt`;

    const chips = [
      `<span class="chip cat" style="color:${color};border-color:${color}">${category}</span>`,
      isWindy    ? `<span class="chip"><span class="icon">💨</span>${windLabel}</span>` : "",
      hasSnow    ? `<span class="chip"><span class="icon">❄️</span>Snow</span>` : "",
      hasThunder ? `<span class="chip"><span class="icon">⚡</span>Thunder</span>` : "",
    ].join("");

    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }
        ha-card { padding: 14px 16px 12px; }
        .icao {
          font-size: 1.15em;
          font-weight: 700;
          color: ${color};
          letter-spacing: 0.05em;
          margin-bottom: 6px;
          display: inline-block;
          background: rgba(0, 0, 0, 0.4);
          padding: 2px 10px;
          border-radius: 6px;
        }
        .metar {
          font-size: 0.82em;
          color: var(--primary-text-color);
          opacity: 0.85;
          line-height: 1.5;
          margin-bottom: 10px;
          word-break: break-word;
        }
        .chips {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
        }
        .chip {
          display: inline-flex;
          align-items: center;
          gap: 3px;
          font-size: 0.78em;
          padding: 3px 10px;
          border-radius: 12px;
          border: 1px solid var(--divider-color);
          background: var(--secondary-background-color);
          color: var(--primary-text-color);
        }
        .chip.cat {
          font-weight: 700;
          background: transparent;
        }
        .icon { font-size: 1em; }
      </style>
      <ha-card>
        <div class="icao">${icao}</div>
        <div class="metar">${rawMetar}</div>
        <div class="chips">${chips}</div>
      </ha-card>
    `;
  }

  getCardSize() { return 2; }
}

customElements.define("metarmap25-airport-card-editor", METARMapAirportCardEditor);
customElements.define("metarmap25-airport-card", METARMapAirportCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "metarmap25-airport-card",
  name: "METARMap Airport Card",
  description: "Displays flight category, METAR, and weather conditions for a METARMap airport.",
  preview: false,
});
